"""
ai_clustering.py
----------------
Module owner: Samuel
Objective 4: Form efficient peer study groups using AI clustering
             to maximise knowledge sharing among JSS3 students.

This module reads the knowledge graph from Neo4j and produces:
  1. peer_groups.json              -- the 10 recommended study groups
  2. chart_group_composition.png   -- visualisation of group balance

STRATEGY:
  - Represent each student as an 80-dimensional vector of their topic scores
  - Use K-Means clustering with k=5 to find 5 student "archetypes"
  - Build 10 peer groups, each containing 1 student from each archetype
  - Result: every group has 5 students with complementary strengths

Run from the bece-sln folder:
    python ai_clustering.py
"""

import json
import os

import numpy as np
from neo4j import GraphDatabase
from dotenv import load_dotenv
from sklearn.cluster import KMeans
import matplotlib.pyplot as plt

# -------------------------------------------------------------------
# CONFIGURATION
# -------------------------------------------------------------------
NUM_ARCHETYPES = 5      # how many student types K-Means should find
NUM_GROUPS = 10         # total peer groups to form
GROUP_SIZE = 5          # students per group (one from each archetype)
RANDOM_SEED = 42        # keeps results reproducible
OUTPUT_FILE = "peer_groups.json"

# -------------------------------------------------------------------
# CONNECT TO NEO4J
# -------------------------------------------------------------------
load_dotenv()
driver = GraphDatabase.driver(
    os.getenv("NEO4J_URI"),
    auth=(os.getenv("NEO4J_USERNAME"), os.getenv("NEO4J_PASSWORD"))
)


# ===================================================================
# SECTION 1 — LOAD DATA FROM NEO4J (done for you)
# ===================================================================

def load_student_vectors():
    """
    Load every student's score on every topic from Neo4j.

    Returns three things:
      - student_ids: list of 50 strings, e.g. ["STU001", "STU002", ...]
      - topic_ids:   list of 80 strings, e.g. ["MTH01", "MTH02", ...]
      - score_matrix: NumPy array of shape (50, 80)
                      where score_matrix[i][j] is student i's score on topic j

    Why a matrix? Because scikit-learn's K-Means expects this exact shape:
    rows = things to cluster (students), columns = features (topics).
    """
    with driver.session() as session:
        # Get ordered student and topic lists
        students = [r["id"] for r in session.run(
            "MATCH (s:Student) RETURN s.id AS id ORDER BY s.id"
        )]
        topics = [r["id"] for r in session.run(
            "MATCH (t:Topic) RETURN t.id AS id ORDER BY t.id"
        )]

        # Build the score matrix
        matrix = np.zeros((len(students), len(topics)))
        student_index = {sid: i for i, sid in enumerate(students)}
        topic_index = {tid: j for j, tid in enumerate(topics)}

        results = session.run("""
            MATCH (s:Student)-[r:SCORED]->(t:Topic)
            RETURN s.id AS sid, t.id AS tid, r.score AS score
        """)
        for record in results:
            i = student_index[record["sid"]]
            j = topic_index[record["tid"]]
            matrix[i][j] = record["score"]

    return students, topics, matrix


def load_topic_metadata():
    """
    Return a dict mapping topic_id -> subject name.
    Used for identifying strong/weak subjects per group later.
    """
    with driver.session() as session:
        results = session.run("""
            MATCH (t:Topic) RETURN t.id AS id, t.subject AS subject
        """)
        return {r["id"]: r["subject"] for r in results}


# ===================================================================
# SECTION 2 — CLUSTERING (YOUR TURN)
# ===================================================================

def cluster_students(score_matrix):
    """
    Run K-Means clustering on the student score matrix to find NUM_ARCHETYPES
    student types.

    Returns a list of 50 integers (one per student), where each integer is the
    archetype label (0, 1, 2, 3, or 4) that student belongs to.

    TODO 1: Create a KMeans object from scikit-learn.
    Hint: the syntax is:
        model = KMeans(n_clusters=NUM_ARCHETYPES,
                       random_state=RANDOM_SEED,
                       n_init=10)

    TODO 2: Fit the model on score_matrix and get the labels.
    Hint: scikit-learn's pattern is:
        labels = model.fit_predict(score_matrix)
    """
    model = KMeans(n_clusters=NUM_ARCHETYPES,
               random_state=RANDOM_SEED,
               n_init=10)


    labels = model.fit_predict(score_matrix)

    return labels


# ===================================================================
# SECTION 3 — FORM PEER GROUPS (YOUR TURN — SMALL CHANGES ONLY)
# ===================================================================

def form_peer_groups(student_ids, cluster_labels):
    """
    Form NUM_GROUPS peer groups, each containing GROUP_SIZE students.
    Each group will have ONE student from each of the NUM_ARCHETYPES clusters,
    so every group has a balanced mix of learning profiles.

    Strategy: we bucket students by archetype, then pick one from each bucket
    for each group, in a round-robin fashion.
    """
    # Bucket students by their cluster label
    buckets = {i: [] for i in range(NUM_ARCHETYPES)}
    for student_id, label in zip(student_ids, cluster_labels):
        buckets[label].append(student_id)

    # TODO 3
    print("=== Archetype Bucket Distribution ===")
    for label, members in buckets.items():
        count = len(members)
        ideal = 10
        warning = ""
        if count == 0:
            warning = " ⚠️  WARNING: Empty bucket — K-Means failed to use this cluster!"
        elif count < ideal // 2 or count > ideal * 2:
            warning = f" ⚠️  WARNING: Expected ~{ideal}, got {count} — unbalanced clustering!"
        print(f"  Archetype {label}: {count} students{warning}")
    ...

    # Shuffle each bucket...
    rng = np.random.default_rng(RANDOM_SEED)
    for label in buckets:
        rng.shuffle(buckets[label])

    # Build the groups...
    groups = []
    for i in range(NUM_GROUPS):
        members = []
        for label in range(NUM_ARCHETYPES):
            if i < len(buckets[label]):
                members.append(buckets[label][i])
        groups.append(members)

    return groups


# ===================================================================
# SECTION 4 — ANALYSE EACH GROUP (YOUR TURN)
# ===================================================================

def analyse_group(members, student_ids, topic_ids, score_matrix, topic_subjects):
    """
    Compute descriptive statistics for a single group.

    Returns a dict:
      - average_score: mean score across all members and all topics
      - strongest_subjects: top 2 subjects where the group is strong
      - weakest_subjects: top 2 subjects where the group is weak
      - complementarity_score: a measure of how diverse the group is
                               (higher = more diverse = better peer learning)
    """
    # Find the row indices of these members in the score matrix
    member_indices = [student_ids.index(m) for m in members]
    group_scores = score_matrix[member_indices]   # shape: (GROUP_SIZE, 80)

    # TODO 4: Compute the average score across the whole group.
    # Hint: np.mean(group_scores) averages all values in the array.
    average_score = np.mean(group_scores)  # <-- replace with a numpy mean call

    # Find strongest and weakest subjects for this group
    subject_scores = {}
    for j, topic_id in enumerate(topic_ids):
        subject = topic_subjects.get(topic_id, "Unknown")
        subject_scores.setdefault(subject, []).append(
            np.mean(group_scores[:, j])   # average this topic across group members
        )
    subject_averages = {s: float(np.mean(vals)) for s, vals in subject_scores.items()}
    sorted_subjects = sorted(subject_averages.items(), key=lambda x: x[1], reverse=True)
    strongest_subjects = [s for s, _ in sorted_subjects[:2]]
    weakest_subjects = [s for s, _ in sorted_subjects[-2:]]

    # TODO 5: Compute the complementarity score for this group.
    # Complementarity = how diverse the group is = higher is better.
    # A simple measure: average standard deviation across topics.
    # If all members score the same on every topic, std = 0 (bad, no diversity).
    # If members score very differently, std is large (good, complementary).
    #
    # Hint:
    #   per_topic_std = np.std(group_scores, axis=0)   # std for each topic
    #   complementarity_score = np.mean(per_topic_std) # average across topics
    per_topic_std = np.std(group_scores, axis=0)
    complementarity_score = np.mean(per_topic_std)  # <-- replace

    return {
        "average_score": round(float(average_score), 3) if average_score is not None else None,
        "strongest_subjects": strongest_subjects,
        "weakest_subjects": weakest_subjects,
        "complementarity_score": round(float(complementarity_score), 3) if complementarity_score is not None else None,
    }


# ===================================================================
# SECTION 5 — COMPARE TO RANDOM BASELINE (done for you)
# ===================================================================

def compute_random_baseline(student_ids, topic_ids, score_matrix, topic_subjects):
    """
    To prove our clustering is better than random grouping, we form random
    groups and compute their average complementarity score for comparison.
    """
    rng = np.random.default_rng(RANDOM_SEED + 1)
    shuffled = list(student_ids)
    rng.shuffle(shuffled)

    random_groups = [shuffled[i*GROUP_SIZE:(i+1)*GROUP_SIZE] for i in range(NUM_GROUPS)]
    comps = []
    for members in random_groups:
        indices = [student_ids.index(m) for m in members]
        g_scores = score_matrix[indices]
        comps.append(np.mean(np.std(g_scores, axis=0)))
    return float(np.mean(comps))


# ===================================================================
# SECTION 6 — CHART (YOUR TURN — just 1 TODO)
# ===================================================================

def chart_group_composition(report):
    """
    Bar chart showing each group's average score.
    X-axis: group IDs (GRP01 - GRP10)
    Y-axis: average score for that group
    """
    # TODO 6: extract the lists for the chart
    # report["groups"] is a list of 10 dicts, each with keys:
    #   group_id, members, average_score, ...
    #
    # Hint:
    #   group_ids = [g["group_id"] for g in report["groups"]]
    #   averages  = [g["average_score"] for g in report["groups"]]
    group_ids = [g["group_id"] for g in report["groups"]]   
    averages  = [g["average_score"] for g in report["groups"]]

    fig, ax = plt.subplots(figsize=(10, 5))
    ax.bar(group_ids, averages, color="#428bca")
    ax.set_ylabel("Group Average Score")
    ax.set_title("Average Score per Peer Group (10 groups of 5 students)")
    ax.set_ylim(0, 1)
    plt.xticks(rotation=30)
    plt.tight_layout()
    plt.savefig("chart_group_composition.png", dpi=150)
    plt.close()
    print("  Saved chart_group_composition.png")


# ===================================================================
# SECTION 7 — PRINT SUMMARY (done for you)
# ===================================================================

def print_summary(report):
    print("\n" + "=" * 70)
    print("PEER GROUP RECOMMENDATIONS")
    print("=" * 70)
    for g in report["groups"]:
        print(f"\n{g['group_id']}   average {g['average_score']}   "
              f"complementarity {g['complementarity_score']}")
        print(f"  Members:   {', '.join(g['members'])}")
        print(f"  Strong in: {', '.join(g['strongest_subjects'])}")
        print(f"  Weak in:   {', '.join(g['weakest_subjects'])}")

    print("\n" + "-" * 70)
    print("QUALITY METRICS")
    m = report["quality_metrics"]
    print(f"  Average complementarity (our algorithm): {m['average_complementarity']}")
    print(f"  Average complementarity (random groups): {m['random_baseline']}")
    improvement = m['vs_random_baseline']
    print(f"  Improvement vs random:                   {improvement}")
    print("=" * 70 + "\n")

# ===================================================================
# MAIN
# ===================================================================

def main():
    print("Connecting to Neo4j ...")
    driver.verify_connectivity()
    print("  Connected.\n")

    print("Loading student vectors ...")
    student_ids, topic_ids, score_matrix = load_student_vectors()
    topic_subjects = load_topic_metadata()
    print(f"  Loaded {len(student_ids)} students x {len(topic_ids)} topics\n")

    print("Running K-Means clustering ...")
    cluster_labels = cluster_students(score_matrix)
    if cluster_labels is None:
        print("\nERROR: cluster_students returned None. Finish TODOs 1 and 2.\n")
        driver.close()
        return
    print(f"  {len(set(cluster_labels))} archetypes found\n")

    print("Forming peer groups ...")
    groups_raw = form_peer_groups(student_ids, cluster_labels)

    print("\nAnalysing each group ...")
    groups_analysed = []
    for i, members in enumerate(groups_raw):
        analysis = analyse_group(members, student_ids, topic_ids, score_matrix, topic_subjects)

        if analysis["average_score"] is None or analysis["complementarity_score"] is None:
            print("\nERROR: analyse_group returned None values. Finish TODOs 4 and 5.\n")
            driver.close()
            return

        groups_analysed.append({
            "group_id": f"GRP{(i+1):02d}",
            "members": members,
            **analysis
        })

    # Quality comparison
    our_complementarity = np.mean([g["complementarity_score"] for g in groups_analysed])
    random_complementarity = compute_random_baseline(student_ids, topic_ids, score_matrix, topic_subjects)
    improvement_pct = ((our_complementarity - random_complementarity) / random_complementarity) * 100

    report = {
        "algorithm": "KMeans with complementarity-balanced grouping",
        "num_groups": NUM_GROUPS,
        "group_size": GROUP_SIZE,
        "groups": groups_analysed,
        "quality_metrics": {
            "average_complementarity": round(float(our_complementarity), 3),
            "random_baseline": round(float(random_complementarity), 3),
            "vs_random_baseline": f"{improvement_pct:+.1f}%",
        }
    }

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
    print(f"  Saved {OUTPUT_FILE}\n")

    print("Building chart ...")
    try:
        chart_group_composition(report)
    except Exception as e:
        print(f"\nERROR generating chart: {e}\nFinish TODO 6.\n")
        driver.close()
        return

    print_summary(report)

    driver.close()
    print("All done. Commit your work with:")
    print("  git pull --rebase")
    print("  git add ai_clustering.py peer_groups.json chart_group_composition.png")
    print("  git commit -m 'AI clustering and peer group formation complete'")
    print("  git push\n")


if __name__ == "__main__":
    main()
