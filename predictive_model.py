"""
predictive_model.py
-------------------
Module owner: Chisom
Objective 3: Develop a predictive model that can identify possible learning
             dependencies between topics (e.g., if a student struggles in
             Topic A, they are likely to struggle in Topic B).

This module:
  1. Computes topic-topic correlation from student performance data
  2. Identifies strongly correlated topic pairs (dependencies)
  3. Builds a "if you fail X, you'll likely fail Y" prediction system
  4. Tests predictions against actual student data
  5. Writes dependency edges back to Neo4j
  6. Saves a chart and JSON report

Run from the bece-sln folder:
    python predictive_model.py
"""

import json
import os
import numpy as np
from neo4j import GraphDatabase
from dotenv import load_dotenv
import matplotlib.pyplot as plt

# -------------------------------------------------------------------
# CONFIGURATION
# -------------------------------------------------------------------
DEPENDENCY_THRESHOLD = 0.5   # correlation above this = topics are dependent
FAILURE_THRESHOLD = 0.4      # score below this = student "failed" the topic
TOP_N_DEPENDENCIES = 30      # how many strongest dependencies to write to Neo4j
OUTPUT_FILE = "predictive_model_report.json"

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

def load_score_matrix():
    """
    Build a (50, 80) matrix where row i = student i, column j = topic j.
    Also return topic metadata for labeling.
    """
    with driver.session() as session:
        students = [r["id"] for r in session.run(
            "MATCH (s:Student) RETURN s.id AS id ORDER BY s.id"
        )]
        topics_raw = list(session.run(
            "MATCH (t:Topic) RETURN t.id AS id, t.name AS name, "
            "t.subject AS subject, t.difficulty AS difficulty ORDER BY t.id"
        ))
        topic_ids = [r["id"] for r in topics_raw]
        topic_meta = {r["id"]: {
            "name": r["name"],
            "subject": r["subject"],
            "difficulty": r["difficulty"]
        } for r in topics_raw}

        student_index = {sid: i for i, sid in enumerate(students)}
        topic_index = {tid: j for j, tid in enumerate(topic_ids)}

        matrix = np.zeros((len(students), len(topic_ids)))
        for record in session.run("""
            MATCH (s:Student)-[r:SCORED]->(t:Topic)
            RETURN s.id AS sid, t.id AS tid, r.score AS score
        """):
            matrix[student_index[record["sid"]]][topic_index[record["tid"]]] = record["score"]

    return students, topic_ids, topic_meta, matrix


# ===================================================================
# SECTION 2 — FIND TOPIC DEPENDENCIES
# ===================================================================

def compute_topic_correlations(score_matrix):
    """
    Compute correlation between TOPICS (columns), not students (rows).

    In complementarity analysis, we correlated rows (students).
    Here we correlate columns (topics).

    If students who fail Topic A also fail Topic B, those columns will
    have high positive correlation = dependency.

    np.corrcoef with rowvar=False treats columns as variables.
    Returns an (80, 80) correlation matrix.
    """
    return np.corrcoef(score_matrix, rowvar=False)


def find_dependencies(correlation_matrix, topic_ids, topic_meta):
    """
    Extract all topic pairs with correlation above DEPENDENCY_THRESHOLD.
    These are the "if you fail A, you'll likely fail B" pairs.
    """
    n = len(topic_ids)
    dependencies = []

    for i in range(n):
        for j in range(i + 1, n):
            corr = correlation_matrix[i][j]
            if corr >= DEPENDENCY_THRESHOLD:
                topic_a = topic_ids[i]
                topic_b = topic_ids[j]
                meta_a = topic_meta[topic_a]
                meta_b = topic_meta[topic_b]

                dependencies.append({
                    "topic_a_id": topic_a,
                    "topic_a_name": meta_a["name"],
                    "topic_a_subject": meta_a["subject"],
                    "topic_b_id": topic_b,
                    "topic_b_name": meta_b["name"],
                    "topic_b_subject": meta_b["subject"],
                    "correlation": round(float(corr), 4),
                    "same_subject": meta_a["subject"] == meta_b["subject"],
                })

    # Sort strongest dependencies first
    dependencies.sort(key=lambda d: d["correlation"], reverse=True)
    return dependencies


# ===================================================================
# SECTION 3 — TEST PREDICTIONS
# ===================================================================

def test_predictions(dependencies, score_matrix, topic_ids):
    """
    For each dependency pair, test: when a student fails Topic A,
    how often do they also fail Topic B?

    This gives us a "prediction accuracy" for each dependency.
    If accuracy is high (e.g. 85%), the dependency is reliable.
    """
    topic_index = {tid: j for j, tid in enumerate(topic_ids)}

    for dep in dependencies:
        col_a = topic_index[dep["topic_a_id"]]
        col_b = topic_index[dep["topic_b_id"]]

        # Find students who failed Topic A
        failed_a = score_matrix[:, col_a] < FAILURE_THRESHOLD
        num_failed_a = int(np.sum(failed_a))

        if num_failed_a == 0:
            dep["prediction_accuracy"] = "N/A (no students failed Topic A)"
            dep["students_failed_a"] = 0
            dep["also_failed_b"] = 0
            continue

        # Of those, how many also failed Topic B?
        also_failed_b = int(np.sum(
            (score_matrix[:, col_a] < FAILURE_THRESHOLD) &
            (score_matrix[:, col_b] < FAILURE_THRESHOLD)
        ))

        accuracy = also_failed_b / num_failed_a
        dep["students_failed_a"] = num_failed_a
        dep["also_failed_b"] = also_failed_b
        dep["prediction_accuracy"] = round(float(accuracy), 3)

    return dependencies


# ===================================================================
# SECTION 4 — WRITE TO NEO4J
# ===================================================================

def write_dependencies_to_neo4j(dependencies):
    """
    Write the top N topic dependencies back to Neo4j as :DEPENDS_ON edges.
    This lets the dashboard show which topics are linked.
    """
    top = dependencies[:TOP_N_DEPENDENCIES]

    with driver.session() as session:
        # Clear old dependency edges
        session.run("MATCH ()-[r:DEPENDS_ON]-() DELETE r")

        # Write new ones
        session.run("""
            UNWIND $deps AS dep
            MATCH (a:Topic {id: dep.topic_a_id})
            MATCH (b:Topic {id: dep.topic_b_id})
            MERGE (a)-[r:DEPENDS_ON]->(b)
            SET r.correlation = dep.correlation,
                r.prediction_accuracy = dep.prediction_accuracy
        """, deps=[d for d in top if isinstance(d.get("prediction_accuracy"), float)])

    print(f"  Wrote {len(top)} :DEPENDS_ON edges to Neo4j")


# ===================================================================
# SECTION 5 — CHARTS
# ===================================================================

def chart_top_dependencies(dependencies, filename):
    """
    Horizontal bar chart of the top 15 topic dependencies.
    """
    top = dependencies[:15]
    labels = [f"{d['topic_a_name'][:20]} ↔ {d['topic_b_name'][:20]}" for d in top]
    correlations = [d["correlation"] for d in top]

    # Color by same_subject (orange = same subject, blue = cross-subject)
    colors = ["#e67e22" if d["same_subject"] else "#3498db" for d in top]

    fig, ax = plt.subplots(figsize=(12, 8))
    bars = ax.barh(labels, correlations, color=colors)
    ax.set_xlabel("Correlation Strength")
    ax.set_title("Top 15 Topic Dependencies\n"
                 "(Orange = same subject, Blue = cross-subject)")
    ax.invert_yaxis()
    ax.set_xlim(0, 1)
    plt.tight_layout()
    plt.savefig(filename, dpi=150)
    plt.close()


def chart_prediction_accuracy(dependencies, filename):
    """
    Bar chart showing prediction accuracy for top dependencies.
    "If student fails Topic A, X% chance they also fail Topic B"
    """
    # Filter to only dependencies with numeric accuracy
    with_accuracy = [d for d in dependencies
                     if isinstance(d.get("prediction_accuracy"), float)][:15]

    if not with_accuracy:
        print("  Skipping prediction accuracy chart (no valid predictions)")
        return

    labels = [f"{d['topic_a_name'][:18]} → {d['topic_b_name'][:18]}" for d in with_accuracy]
    accuracies = [d["prediction_accuracy"] * 100 for d in with_accuracy]

    fig, ax = plt.subplots(figsize=(12, 8))
    ax.barh(labels, accuracies, color="#2ecc71")
    ax.set_xlabel("Prediction Accuracy (%)")
    ax.set_title("Topic Dependency Prediction Accuracy\n"
                 "'If student fails Topic A, how likely do they also fail Topic B?'")
    ax.invert_yaxis()
    ax.set_xlim(0, 100)
    plt.tight_layout()
    plt.savefig(filename, dpi=150)
    plt.close()


# ===================================================================
# SECTION 6 — SUMMARY
# ===================================================================

def print_summary(dependencies, all_topic_pairs):
    print("\n" + "=" * 70)
    print("PREDICTIVE MODEL — TOPIC DEPENDENCY REPORT")
    print("=" * 70)
    print(f"Total topic pairs analysed: {all_topic_pairs}")
    print(f"Dependencies found (correlation >= {DEPENDENCY_THRESHOLD}): {len(dependencies)}")

    same_subject = sum(1 for d in dependencies if d["same_subject"])
    cross_subject = len(dependencies) - same_subject
    print(f"  Same-subject dependencies: {same_subject}")
    print(f"  Cross-subject dependencies: {cross_subject}")

    print(f"\nTop 10 strongest dependencies:")
    print(f"  {'Topic A':<25} {'Topic B':<25} {'Corr':<8} {'Accuracy'}")
    for d in dependencies[:10]:
        acc = d.get("prediction_accuracy", "N/A")
        acc_str = f"{acc:.0%}" if isinstance(acc, float) else acc
        print(f"  {d['topic_a_name'][:23]:<25} {d['topic_b_name'][:23]:<25} "
              f"{d['correlation']:<8} {acc_str}")

    # Overall prediction performance
    valid = [d for d in dependencies if isinstance(d.get("prediction_accuracy"), float)]
    if valid:
        avg_accuracy = np.mean([d["prediction_accuracy"] for d in valid])
        print(f"\nOverall average prediction accuracy: {avg_accuracy:.1%}")
        print(f"(across {len(valid)} testable dependencies)")

    print("=" * 70 + "\n")


# ===================================================================
# MAIN
# ===================================================================

def main():
    print("Connecting to Neo4j ...")
    driver.verify_connectivity()
    print("  Connected.\n")

    print("Loading score matrix ...")
    students, topic_ids, topic_meta, score_matrix = load_score_matrix()
    print(f"  Loaded {len(students)} students x {len(topic_ids)} topics\n")

    print("Computing topic-topic correlations ...")
    correlation_matrix = compute_topic_correlations(score_matrix)
    total_pairs = len(topic_ids) * (len(topic_ids) - 1) // 2
    print(f"  Analysed {total_pairs} topic pairs\n")

    print("Finding dependencies ...")
    dependencies = find_dependencies(correlation_matrix, topic_ids, topic_meta)
    print(f"  Found {len(dependencies)} dependencies above threshold {DEPENDENCY_THRESHOLD}\n")

    print("Testing prediction accuracy ...")
    dependencies = test_predictions(dependencies, score_matrix, topic_ids)
    print("  Done.\n")

    print("Writing :DEPENDS_ON edges to Neo4j ...")
    write_dependencies_to_neo4j(dependencies)

    print("\nBuilding charts ...")
    chart_top_dependencies(dependencies, "chart_topic_dependencies.png")
    print("  Saved chart_topic_dependencies.png")

    chart_prediction_accuracy(dependencies, "chart_prediction_accuracy.png")
    print("  Saved chart_prediction_accuracy.png")

    # Save report
    report = {
        "threshold": DEPENDENCY_THRESHOLD,
        "failure_threshold": FAILURE_THRESHOLD,
        "total_topic_pairs": total_pairs,
        "dependencies_found": len(dependencies),
        "dependencies": dependencies,
    }
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
    print(f"  Saved {OUTPUT_FILE}")

    print_summary(dependencies, total_pairs)

    driver.close()
    print("All done. Verify in Neo4j with this query:")
    print("  MATCH (a:Topic)-[r:DEPENDS_ON]->(b:Topic) RETURN a, r, b\n")


if __name__ == "__main__":
    main()
