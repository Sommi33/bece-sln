"""
topic_failure_analysis.py
-------------------------
Module owner: Adebayo
Objective 2: Analyze students' performance to determine the topics
             in which students fail most frequently.

This module reads the knowledge graph from Neo4j and produces:
  1. topic_failure_report.json   -- structured data for other modules
  2. chart_weakest_topics.png    -- bar chart of 10 weakest topics
  3. chart_subjects_avg.png      -- bar chart of average score per subject
  4. chart_difficulty_avg.png    -- bar chart of Easy/Medium/Hard averages

Run from the bece-sln folder:
    python topic_failure_analysis.py
"""

import json
import os
from neo4j import GraphDatabase
from dotenv import load_dotenv
import matplotlib.pyplot as plt

# -------------------------------------------------------------------
# CONFIGURATION — you can tune these
# -------------------------------------------------------------------
FAILURE_THRESHOLD = 0.40   # scores below this count as "failing" a topic
TOP_N_WEAKEST = 10         # how many weakest topics to show in the chart
OUTPUT_REPORT = "topic_failure_report.json"

# -------------------------------------------------------------------
# CONNECT TO NEO4J
# -------------------------------------------------------------------
load_dotenv()
URI = os.getenv("NEO4J_URI")
USER = os.getenv("NEO4J_USERNAME")
PASSWORD = os.getenv("NEO4J_PASSWORD")

driver = GraphDatabase.driver(URI, auth=(USER, PASSWORD))


# ===================================================================
# SECTION 1 — QUERY FUNCTIONS (mostly done for you)
# ===================================================================

def get_class_average():
    """Return the overall average score across all students and all topics."""
    with driver.session() as session:
        result = session.run("""
            MATCH (s:Student)-[r:SCORED]->(t:Topic)
            RETURN avg(r.score) AS class_avg
        """).single()
        return round(result["class_avg"], 3)


def get_topic_statistics():
    """
    Return per-topic statistics:
      - topic_id, topic_name, subject, difficulty
      - class_average for that topic
      - number of students below FAILURE_THRESHOLD on that topic

    Returns a list of dicts, one per topic.
    """
    with driver.session() as session:
        result = session.run("""
            MATCH (s:Student)-[r:SCORED]->(t:Topic)
            WITH t, avg(r.score) AS class_avg,
                 sum(CASE WHEN r.score < $threshold THEN 1 ELSE 0 END) AS failing_count
            RETURN t.id AS topic_id,
                   t.name AS topic_name,
                   t.subject AS subject,
                   t.difficulty AS difficulty,
                   round(class_avg, 3) AS class_average,
                   failing_count
            ORDER BY class_avg ASC
        """, threshold=FAILURE_THRESHOLD)
        return [dict(record) for record in result]


def get_subject_statistics():
    """
    Return per-subject statistics:
      - subject name
      - average score across all its topics and students
      - the single hardest topic in that subject

    Returns a list of dicts, one per subject, sorted by average ascending.
    """
    with driver.session() as session:
        result = session.run("""
            MATCH (s:Student)-[r:SCORED]->(t:Topic)
            WITH t.subject AS subject, avg(r.score) AS subject_avg
            ORDER BY subject_avg ASC
            RETURN subject, round(subject_avg, 3) AS average
        """)
        subjects = [dict(record) for record in result]

    # For each subject, find its weakest topic
    for subj in subjects:
        with driver.session() as session:
            weakest = session.run("""
                MATCH (s:Student)-[r:SCORED]->(t:Topic {subject: $subject})
                WITH t, avg(r.score) AS topic_avg
                ORDER BY topic_avg ASC LIMIT 1
                RETURN t.name AS hardest_topic
            """, subject=subj["subject"]).single()
            subj["hardest_topic"] = weakest["hardest_topic"]

    return subjects


def get_difficulty_breakdown():
    """
    Return average score for Easy, Medium, and Hard topics separately.
    Returns a dict like: {"Easy": 0.62, "Medium": 0.53, "Hard": 0.41}
    """
    with driver.session() as session:
        result = session.run("""
            MATCH (s:Student)-[r:SCORED]->(t:Topic)
            RETURN t.difficulty AS difficulty,
                   round(avg(r.score), 3) AS avg_score
            ORDER BY avg_score DESC
        """)
        return {record["difficulty"]: record["avg_score"] for record in result}


def get_struggling_students(limit=10):
    """
    Return the students with the lowest overall averages.
    Returns a list of dicts with student_id, average, and profile_type.
    """
    with driver.session() as session:
        result = session.run("""
            MATCH (s:Student)-[r:SCORED]->(t:Topic)
            WITH s, avg(r.score) AS student_avg
            ORDER BY student_avg ASC
            LIMIT $limit
            RETURN s.id AS student_id,
                   round(student_avg, 3) AS average,
                   s.profile_type AS profile
        """, limit=limit)
        return [dict(record) for record in result]


# ===================================================================
# SECTION 2 — BUILD THE REPORT (YOUR TURN)
# ===================================================================

def build_report():
    """
    Assemble all the analysis results into one big dictionary,
    which will be saved as topic_failure_report.json.

    TODO: fill in the missing values below by calling the query functions above.
    Everything you need is already defined — just call the right function.
    """

    class_average = get_class_average()

    # TODO 1: Get all topic statistics, then pick just the TOP_N_WEAKEST topics
    #         Hint: get_topic_statistics() already sorts topics weakest first.
    #               Use Python slicing: list[:TOP_N_WEAKEST]
    all_topic_stats = get_topic_statistics()      # <-- replace None with a function call
    weakest_topics = all_topic_stats[:TOP_N_WEAKEST]        # <-- take the first TOP_N_WEAKEST items from all_topic_stats

    # TODO 2: Get subject statistics (already sorted weakest first)
    weakest_subjects = get_subject_statistics()      # <-- replace None

    # TODO 3: Get the difficulty breakdown (Easy/Medium/Hard averages)
    difficulty_breakdown = get_difficulty_breakdown()  # <-- replace None

    # TODO 4: Get the top 10 struggling students
    struggling_students = get_struggling_students()   # <-- replace None

    report = {
        "class_average": class_average,
        "failure_threshold": FAILURE_THRESHOLD,
        "weakest_topics": weakest_topics,
        "weakest_subjects": weakest_subjects,
        "difficulty_breakdown": difficulty_breakdown,
        "struggling_students": struggling_students,
    }
    return report


# ===================================================================
# SECTION 3 — CHARTS (YOUR TURN)
# ===================================================================

def chart_weakest_topics(weakest_topics):
    """
    Bar chart of the weakest TOP_N_WEAKEST topics.
    x-axis: topic names (shortened if too long)
    y-axis: class average score
    """
    # TODO 5: Extract the lists for the chart.
    #
    # You need two lists of the same length:
    #   names[i]  = topic name for bar i
    #   scores[i] = class average for bar i
    #
    # weakest_topics is a list of dicts. Each dict looks like:
    #   {"topic_id": "MTH17", "topic_name": "Algebraic Expressions",
    #    "subject": "Mathematics", "difficulty": "Hard",
    #    "class_average": 0.312, "failing_count": 38}
    #
    # Hint: use a "list comprehension" — for example:
    #   names  = [t["topic_name"] for t in weakest_topics]
    #   scores = [t["class_average"] for t in weakest_topics]
    names = [t["topic_name"] for t in weakest_topics]
    scores = [t["class_average"] for t in weakest_topics]

    # Everything below is done for you — do not change unless you want to
    fig, ax = plt.subplots(figsize=(12, 6))
    ax.barh(names, scores, color="#d9534f")
    ax.set_xlabel("Class Average Score")
    ax.set_title(f"Top {TOP_N_WEAKEST} Weakest Topics (BECE Class Performance)")
    ax.invert_yaxis()   # weakest topic at the top
    plt.tight_layout()
    plt.savefig("chart_weakest_topics.png", dpi=150)
    plt.close()
    print("  Saved chart_weakest_topics.png")


def chart_subjects_avg(weakest_subjects):
    """
    Bar chart of average score per subject.
    """
    # TODO 6: Extract the lists (same pattern as above)
    # weakest_subjects items look like:
    #   {"subject": "Mathematics", "average": 0.48, "hardest_topic": "..."}
    names = [s["subject"] for s in weakest_subjects]
    averages = [s["average"] for s in weakest_subjects]

    fig, ax = plt.subplots(figsize=(12, 6))
    ax.bar(names, averages, color="#5bc0de")
    ax.set_ylabel("Average Score")
    ax.set_title("Average Score by Subject (BECE Class Performance)")
    ax.set_ylim(0, 1)
    plt.xticks(rotation=30, ha="right")
    plt.tight_layout()
    plt.savefig("chart_subjects_avg.png", dpi=150)
    plt.close()
    print("  Saved chart_subjects_avg.png")


def chart_difficulty_avg(difficulty_breakdown):
    """
    Bar chart of Easy / Medium / Hard averages.
    """
    # TODO 7: Extract the lists from the difficulty_breakdown dict.
    # difficulty_breakdown looks like: {"Easy": 0.62, "Medium": 0.53, "Hard": 0.41}
    #
    # Hint: we want a specific order (Easy, Medium, Hard), not whatever order
    # the dict happens to have. Use:
    #   labels = ["Easy", "Medium", "Hard"]
    #   values = [difficulty_breakdown[d] for d in labels]
    labels = ["Easy", "Medium", "Hard"]
    values = [difficulty_breakdown[d] for d in labels]

    colors = ["#5cb85c", "#f0ad4e", "#d9534f"]  # green, orange, red
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.bar(labels, values, color=colors)
    ax.set_ylabel("Average Score")
    ax.set_title("Average Score by Difficulty Level")
    ax.set_ylim(0, 1)
    plt.tight_layout()
    plt.savefig("chart_difficulty_avg.png", dpi=150)
    plt.close()
    print("  Saved chart_difficulty_avg.png")


# ===================================================================
# SECTION 4 — PRINT SUMMARY TO TERMINAL (DONE FOR YOU)
# ===================================================================

def print_summary(report):
    print("\n" + "=" * 60)
    print("TOPIC FAILURE ANALYSIS REPORT")
    print("=" * 60)
    print(f"Overall class average: {report['class_average']}")
    print(f"Failure threshold:     {report['failure_threshold']}")

    print("\nTop 10 Weakest Topics:")
    print(f"  {'ID':<8} {'Topic':<40} {'Subject':<25} {'Avg':<6} {'Failing'}")
    for t in report["weakest_topics"]:
        name = t["topic_name"][:38] + ".." if len(t["topic_name"]) > 40 else t["topic_name"]
        print(f"  {t['topic_id']:<8} {name:<40} {t['subject']:<25} "
              f"{t['class_average']:<6} {t['failing_count']}")

    print("\nWeakest Subjects:")
    for s in report["weakest_subjects"]:
        print(f"  {s['subject']:<30} avg {s['average']:<6} | hardest: {s['hardest_topic']}")

    print("\nDifficulty Breakdown:")
    for d, v in report["difficulty_breakdown"].items():
        print(f"  {d:<8} avg {v}")

    print("\nTop 10 Struggling Students:")
    for s in report["struggling_students"]:
        print(f"  {s['student_id']:<8} avg {s['average']:<6} profile: {s['profile']}")

    print("=" * 60 + "\n")


# ===================================================================
# MAIN
# ===================================================================

def main():
    print("Connecting to Neo4j ...")
    driver.verify_connectivity()
    print("  Connected.\n")

    print("Building report ...")
    report = build_report()

    # Validate — crash early with a clear message if any TODO wasn't filled in
    required_keys = ["weakest_topics", "weakest_subjects",
                     "difficulty_breakdown", "struggling_students"]
    for key in required_keys:
        if report[key] is None:
            print(f"\nERROR: report['{key}'] is None — you still have a TODO to finish.")
            print("Open topic_failure_analysis.py and look for '# TODO:' markers.\n")
            driver.close()
            return

    # Save JSON report
    with open(OUTPUT_REPORT, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
    print(f"  Saved {OUTPUT_REPORT}\n")

    # Build charts
    print("Building charts ...")
    try:
        chart_weakest_topics(report["weakest_topics"])
        chart_subjects_avg(report["weakest_subjects"])
        chart_difficulty_avg(report["difficulty_breakdown"])
    except Exception as e:
        print(f"\nERROR generating charts: {e}")
        print("Check the TODOs inside the chart_* functions.\n")
        driver.close()
        return

    # Print summary
    print_summary(report)

    driver.close()
    print("All done. Commit your work with:")
    print("  git add topic_failure_analysis.py topic_failure_report.json chart_*.png")
    print("  git commit -m 'Topic failure analysis complete'")
    print("  git push\n")


if __name__ == "__main__":
    main()
