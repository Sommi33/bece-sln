"""
topic_peer_pairing.py
---------------------
Module: Topic-Specific Peer Pairing for Knowledge Diffusion
Objective: For each BECE topic, identify weak students (Susceptible)
           and strong students (Informed), then pair them for targeted
           peer learning to achieve knowledge diffusion.

This directly implements the SIR model's practical recommendation:
  - Susceptible students (score < 0.4) need to learn the topic
  - Informed students (score >= 0.7) can teach it
  - Pairs are formed to maximise knowledge transfer

Output:
  1. topic_peer_pairs.json    -- all pairings per topic
  2. chart_diffusion_pairs.png -- visualisation of weak/strong distribution
  3. Writes TEACHES relationships to Neo4j

Run from the bece-sln folder:
    python topic_peer_pairing.py
"""

import json
import os
import numpy as np
from neo4j import GraphDatabase
from dotenv import load_dotenv
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

# -------------------------------------------------------------------
# CONFIGURATION
# -------------------------------------------------------------------
INFORMED_THRESHOLD = 0.70    # score >= this → student is STRONG (Informed)
SUSCEPTIBLE_THRESHOLD = 0.40 # score < this  → student is WEAK (Susceptible)
OUTPUT_FILE = "topic_peer_pairs.json"
TOP_N_TOPICS = 10            # show pairings for the N most critical topics

# -------------------------------------------------------------------
# CONNECT TO NEO4J
# -------------------------------------------------------------------
load_dotenv()
driver = GraphDatabase.driver(
    os.getenv("NEO4J_URI"),
    auth=(os.getenv("NEO4J_USERNAME"), os.getenv("NEO4J_PASSWORD"))
)


# ===================================================================
# SECTION 1 — LOAD DATA
# ===================================================================

def load_all_scores():
    """
    Load every student's score on every topic.
    Returns:
      - student_ids: sorted list of 50 student IDs
      - topic_data: dict of topic_id -> {name, subject, difficulty, scores: {student_id: score}}
    """
    with driver.session() as session:
        # Get all student IDs
        student_ids = sorted([
            r["id"] for r in session.run(
                "MATCH (s:Student) RETURN s.id AS id ORDER BY s.id"
            )
        ])

        # Get all topics with metadata
        topics_raw = list(session.run("""
            MATCH (t:Topic)
            RETURN t.id AS id, t.name AS name,
                   t.subject AS subject, t.difficulty AS difficulty
            ORDER BY t.subject, t.id
        """))

        topic_data = {r["id"]: {
            "name": r["name"],
            "subject": r["subject"],
            "difficulty": r["difficulty"],
            "scores": {}
        } for r in topics_raw}

        # Get all scores
        scores = session.run("""
            MATCH (s:Student)-[r:SCORED]->(t:Topic)
            RETURN s.id AS sid, t.id AS tid, r.score AS score
        """)
        for record in scores:
            if record["tid"] in topic_data:
                topic_data[record["tid"]]["scores"][record["sid"]] = record["score"]

    return student_ids, topic_data


# ===================================================================
# SECTION 2 — CLASSIFY AND PAIR STUDENTS PER TOPIC
# ===================================================================

def classify_students_for_topic(topic_scores):
    """
    For one topic, classify each student as:
      - 'informed'     : score >= INFORMED_THRESHOLD (strong, can teach)
      - 'susceptible'  : score < SUSCEPTIBLE_THRESHOLD (weak, needs help)
      - 'intermediate' : between thresholds (partially understands)
    """
    informed = []
    susceptible = []
    intermediate = []

    for student_id, score in topic_scores.items():
        if score >= INFORMED_THRESHOLD:
            informed.append({"student_id": student_id, "score": round(score, 3)})
        elif score < SUSCEPTIBLE_THRESHOLD:
            susceptible.append({"student_id": student_id, "score": round(score, 3)})
        else:
            intermediate.append({"student_id": student_id, "score": round(score, 3)})

    # Sort: informed from highest score, susceptible from lowest score
    informed.sort(key=lambda x: x["score"], reverse=True)
    susceptible.sort(key=lambda x: x["score"])

    return informed, susceptible, intermediate


def form_teaching_pairs(informed, susceptible):
    """
    Pair each weak (susceptible) student with the best available
    strong (informed) student.

    Strategy: Round-robin assignment — distribute weak students
    across strong students evenly so no one strong student is
    overwhelmed. Each strong student is paired with at most 3
    weak students.
    """
    if not informed or not susceptible:
        return []

    pairs = []
    max_per_tutor = 3

    # Track how many weak students each informed student is already tutoring
    tutor_load = {s["student_id"]: 0 for s in informed}

    for weak in susceptible:
        # Find the informed student with the highest score who still has capacity
        best_tutor = None
        best_score = -1

        for tutor in informed:
            tid = tutor["student_id"]
            if tutor_load[tid] < max_per_tutor and tutor["score"] > best_score:
                best_tutor = tutor
                best_score = tutor["score"]

        if best_tutor:
            pairs.append({
                "weak_student": weak["student_id"],
                "weak_score": weak["score"],
                "strong_student": best_tutor["student_id"],
                "strong_score": best_tutor["score"],
                "score_gap": round(best_tutor["score"] - weak["score"], 3),
                "learning_potential": "High" if best_tutor["score"] - weak["score"] > 0.4 else "Moderate"
            })
            tutor_load[best_tutor["student_id"]] += 1

    return pairs


def analyse_all_topics(topic_data):
    """
    For every topic, classify students and form teaching pairs.
    Returns a list of topic analysis results, sorted by number of
    susceptible students (most critical topics first).
    """
    results = []

    for topic_id, data in topic_data.items():
        informed, susceptible, intermediate = classify_students_for_topic(data["scores"])
        pairs = form_teaching_pairs(informed, susceptible)

        # Class average for this topic
        scores = list(data["scores"].values())
        class_avg = round(float(np.mean(scores)), 3) if scores else 0

        results.append({
            "topic_id": topic_id,
            "topic_name": data["name"],
            "subject": data["subject"],
            "difficulty": data["difficulty"],
            "class_average": class_avg,
            "informed_count": len(informed),
            "susceptible_count": len(susceptible),
            "intermediate_count": len(intermediate),
            "informed_students": informed,
            "susceptible_students": susceptible,
            "teaching_pairs": pairs,
            "coverage": round(len(pairs) / len(susceptible), 3) if susceptible else 1.0,
            "diffusion_possible": len(informed) > 0,
        })

    # Sort by susceptible count descending (most critical topics first)
    results.sort(key=lambda x: x["susceptible_count"], reverse=True)
    return results


# ===================================================================
# SECTION 3 — WRITE BACK TO NEO4J
# ===================================================================

def write_teaches_to_neo4j(topic_results):
    """
    Write TEACHES relationships to Neo4j for all topic pairs.
    Each TEACHES edge connects a strong student to a weak student
    for a specific topic.
    """
    with driver.session() as session:
        # Clear old TEACHES edges
        session.run("MATCH ()-[r:TEACHES]-() DELETE r")

        total_edges = 0
        for topic in topic_results:
            for pair in topic["teaching_pairs"]:
                session.run("""
                    MATCH (strong:Student {id: $strong_id})
                    MATCH (weak:Student {id: $weak_id})
                    MATCH (t:Topic {id: $topic_id})
                    MERGE (strong)-[r:TEACHES]->(weak)
                    SET r.topic_id = $topic_id,
                        r.topic_name = $topic_name,
                        r.strong_score = $strong_score,
                        r.weak_score = $weak_score,
                        r.score_gap = $score_gap
                """,
                    strong_id=pair["strong_student"],
                    weak_id=pair["weak_student"],
                    topic_id=topic["topic_id"],
                    topic_name=topic["topic_name"],
                    strong_score=pair["strong_score"],
                    weak_score=pair["weak_score"],
                    score_gap=pair["score_gap"]
                )
                total_edges += 1

    print(f"  Wrote {total_edges} :TEACHES edges to Neo4j")
    return total_edges


# ===================================================================
# SECTION 4 — CHARTS
# ===================================================================

def chart_weak_strong_distribution(topic_results, filename):
    """
    Stacked bar chart showing the number of Informed, Intermediate,
    and Susceptible students for the TOP_N_TOPICS most critical topics.
    """
    top_topics = topic_results[:TOP_N_TOPICS]
    names = [f"{t['topic_name'][:20]}..." if len(t['topic_name']) > 20
             else t['topic_name'] for t in top_topics]
    informed = [t["informed_count"] for t in top_topics]
    intermediate = [t["intermediate_count"] for t in top_topics]
    susceptible = [t["susceptible_count"] for t in top_topics]

    x = range(len(names))
    fig, ax = plt.subplots(figsize=(14, 7))

    bars_s = ax.bar(x, susceptible, label="Susceptible (Weak)", color="#f87171")
    bars_m = ax.bar(x, intermediate, bottom=susceptible,
                    label="Intermediate", color="#fb923c")
    bars_i = ax.bar(x, informed,
                    bottom=[s + m for s, m in zip(susceptible, intermediate)],
                    label="Informed (Strong)", color="#34d399")

    ax.set_xticks(x)
    ax.set_xticklabels(names, rotation=35, ha="right", fontsize=9)
    ax.set_ylabel("Number of Students")
    ax.set_title(f"Top {TOP_N_TOPICS} Topics: Student Distribution by Knowledge State\n"
                 "(Green = can teach, Orange = partially knows, Red = needs help)")
    ax.legend(loc="upper right")
    ax.set_ylim(0, 55)
    plt.tight_layout()
    plt.savefig(filename, dpi=150)
    plt.close()
    print(f"  Saved {filename}")


def chart_topic_coverage(topic_results, filename):
    """
    Bar chart showing what percentage of weak students can be paired
    with a strong student for each of the top critical topics.
    """
    top = [t for t in topic_results[:TOP_N_TOPICS] if t["susceptible_count"] > 0]
    names = [f"{t['topic_name'][:20]}..." if len(t['topic_name']) > 20
             else t['topic_name'] for t in top]
    coverage = [t["coverage"] * 100 for t in top]
    colors = ["#34d399" if c >= 80 else "#fb923c" if c >= 50 else "#f87171"
              for c in coverage]

    fig, ax = plt.subplots(figsize=(12, 6))
    ax.barh(names, coverage, color=colors)
    ax.set_xlabel("% of Weak Students Paired with a Strong Tutor")
    ax.set_title("Peer Pairing Coverage for Most Critical Topics\n"
                 "(Green ≥ 80%, Orange ≥ 50%, Red < 50%)")
    ax.set_xlim(0, 110)
    ax.invert_yaxis()

    for i, v in enumerate(coverage):
        ax.text(v + 1, i, f"{v:.0f}%", va="center", fontsize=9)

    plt.tight_layout()
    plt.savefig(filename, dpi=150)
    plt.close()
    print(f"  Saved {filename}")


# ===================================================================
# SECTION 5 — PRINT SUMMARY
# ===================================================================

def print_summary(topic_results):
    print("\n" + "=" * 75)
    print("TOPIC-SPECIFIC PEER PAIRING SUMMARY")
    print("=" * 75)

    total_pairs = sum(len(t["teaching_pairs"]) for t in topic_results)
    no_diffusion = [t for t in topic_results if not t["diffusion_possible"]]
    full_coverage = [t for t in topic_results
                     if t["diffusion_possible"] and t["coverage"] >= 0.8]

    print(f"\nOverall statistics:")
    print(f"  Total topics analysed:            {len(topic_results)}")
    print(f"  Total teaching pairs formed:       {total_pairs}")
    print(f"  Topics with no informed students:  {len(no_diffusion)}")
    print(f"  Topics with ≥80% weak coverage:    {len(full_coverage)}")

    print(f"\nTop 10 most critical topics (most weak students):")
    print(f"  {'Topic':<30} {'Subj':<10} {'Diff':<8} {'Weak':<6} {'Strong':<8} {'Pairs':<6} {'Cover'}")
    for t in topic_results[:10]:
        subj_short = t["subject"].split()[0][:9]
        print(f"  {t['topic_name'][:28]:<30} {subj_short:<10} "
              f"{t['difficulty']:<8} {t['susceptible_count']:<6} "
              f"{t['informed_count']:<8} {len(t['teaching_pairs']):<6} "
              f"{t['coverage']*100:.0f}%")

    if no_diffusion:
        print(f"\nTopics where peer learning is impossible (no informed students):")
        for t in no_diffusion[:5]:
            print(f"  ⚠️  {t['topic_name']} ({t['subject']}) — "
                  f"all {t['susceptible_count']} students are weak")
        print("  → Teacher-led instruction required for these topics first.")

    print("=" * 75 + "\n")


# ===================================================================
# MAIN
# ===================================================================

def main():
    print("Connecting to Neo4j ...")
    driver.verify_connectivity()
    print("  Connected.\n")

    print("Loading student scores ...")
    student_ids, topic_data = load_all_scores()
    print(f"  Loaded {len(student_ids)} students across {len(topic_data)} topics\n")

    print("Classifying students and forming teaching pairs ...")
    topic_results = analyse_all_topics(topic_data)
    print(f"  Analysed {len(topic_results)} topics\n")

    print("Writing :TEACHES edges to Neo4j ...")
    total_edges = write_teaches_to_neo4j(topic_results)

    print("\nBuilding charts ...")
    chart_weak_strong_distribution(topic_results, "chart_peer_pairing_distribution.png")
    chart_topic_coverage(topic_results, "chart_peer_pairing_coverage.png")

    # Save report (top 20 topics with full details, rest summary only)
    report = {
        "thresholds": {
            "informed": INFORMED_THRESHOLD,
            "susceptible": SUSCEPTIBLE_THRESHOLD
        },
        "summary": {
            "total_topics": len(topic_results),
            "total_teaching_pairs": sum(len(t["teaching_pairs"]) for t in topic_results),
            "topics_with_no_informed": len([t for t in topic_results
                                            if not t["diffusion_possible"]]),
        },
        "critical_topics": topic_results[:20],    # top 20 with full pair details
        "all_topics_summary": [{
            "topic_id": t["topic_id"],
            "topic_name": t["topic_name"],
            "subject": t["subject"],
            "difficulty": t["difficulty"],
            "class_average": t["class_average"],
            "informed_count": t["informed_count"],
            "susceptible_count": t["susceptible_count"],
            "pairs_formed": len(t["teaching_pairs"]),
            "coverage": t["coverage"],
            "diffusion_possible": t["diffusion_possible"],
        } for t in topic_results]
    }

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
    print(f"\n  Saved {OUTPUT_FILE}")

    print_summary(topic_results)

    driver.close()
    print("Verify in Neo4j with:")
    print("  MATCH (a:Student)-[r:TEACHES]->(b:Student) RETURN a, r, b\n")


if __name__ == "__main__":
    main()