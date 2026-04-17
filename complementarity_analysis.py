"""
complementarity_analysis.py
---------------------------
Module owner: Chisom
Objective 4 (part 1): Identify complementary peer pairs among JSS3 students.

Complementarity = negative correlation between score vectors.
Two students are "complementary" when one is strong where the other is weak.
These pairs are ideal for peer learning because each can teach the other.

This module:
  1. Reads all student score vectors from Neo4j
  2. Computes the 50x50 Pearson correlation matrix
  3. Ranks all 1225 unique pairs from most complementary to least
  4. Writes the top 20 pairs back to Neo4j as :COMPLEMENTS edges
  5. Saves a JSON report and a heatmap visualisation

Run from the bece-sln folder:
    python complementarity_analysis.py
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
TOP_N_PAIRS = 20              # how many best pairs to write back to Neo4j
MATRIX_OUTPUT = "complementarity_matrix.json"
PAIRS_OUTPUT = "complementary_pairs.json"

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
    Build a (50, 80) matrix where row i is student i's scores across all topics.
    Also return the student IDs in the same order as the rows.
    """
    with driver.session() as session:
        students = [r["id"] for r in session.run(
            "MATCH (s:Student) RETURN s.id AS id ORDER BY s.id"
        )]
        topics = [r["id"] for r in session.run(
            "MATCH (t:Topic) RETURN t.id AS id ORDER BY t.id"
        )]

        student_index = {sid: i for i, sid in enumerate(students)}
        topic_index = {tid: j for j, tid in enumerate(topics)}

        matrix = np.zeros((len(students), len(topics)))
        for record in session.run("""
            MATCH (s:Student)-[r:SCORED]->(t:Topic)
            RETURN s.id AS sid, t.id AS tid, r.score AS score
        """):
            matrix[student_index[record["sid"]]][topic_index[record["tid"]]] = record["score"]

    return students, matrix


# ===================================================================
# SECTION 2 — COMPUTE COMPLEMENTARITY
# ===================================================================

def compute_correlation_matrix(score_matrix):
    """
    Compute the Pearson correlation between every pair of students.
    Returns a (50, 50) matrix where entry [i][j] is the correlation
    between student i's scores and student j's scores.

    np.corrcoef does this in one line — it's a standard statistics function.
    We pass score_matrix directly because np.corrcoef treats rows as the
    variables to correlate.
    """
    return np.corrcoef(score_matrix)


def rank_pairs(correlation_matrix, student_ids):
    """
    Take the correlation matrix and produce a ranked list of all unique
    student pairs, sorted from most negative (most complementary) to most
    positive (least complementary).

    We skip the diagonal (a student compared to themselves = 1.0 always)
    and skip duplicates (pair A-B is the same as pair B-A).
    """
    n = len(student_ids)
    pairs = []
    for i in range(n):
        for j in range(i + 1, n):   # j starts at i+1 so we skip self and duplicates
            correlation = correlation_matrix[i][j]
            # complementarity_score: convert correlation to a positive "goodness" metric
            # correlation of -1 = perfect complement = score of 1.0
            # correlation of +1 = identical = score of 0.0
            complementarity = (1.0 - correlation) / 2.0
            pairs.append({
                "student_a": student_ids[i],
                "student_b": student_ids[j],
                "correlation": round(float(correlation), 4),
                "complementarity_score": round(float(complementarity), 4),
            })

    # Sort so most complementary pairs come first
    pairs.sort(key=lambda p: p["complementarity_score"], reverse=True)
    return pairs


# ===================================================================
# SECTION 3 — WRITE RESULTS BACK TO NEO4J
# ===================================================================

def write_complements_to_neo4j(top_pairs):
    """
    Write the top N pairs back into Neo4j as :COMPLEMENTS relationships.
    Before writing, we clear any existing :COMPLEMENTS edges so the graph
    reflects the latest analysis.
    """
    with driver.session() as session:
        # Clear old complementarity edges
        session.run("MATCH ()-[r:COMPLEMENTS]-() DELETE r")

        # Write new ones
        session.run("""
            UNWIND $pairs AS pair
            MATCH (a:Student {id: pair.student_a})
            MATCH (b:Student {id: pair.student_b})
            MERGE (a)-[r:COMPLEMENTS]->(b)
            SET r.score = pair.complementarity_score,
                r.correlation = pair.correlation
        """, pairs=top_pairs)

    print(f"  Wrote {len(top_pairs)} :COMPLEMENTS edges to Neo4j")


# ===================================================================
# SECTION 4 — VISUALISATION
# ===================================================================

def chart_heatmap(correlation_matrix, student_ids):
    """
    Heatmap of the full 50x50 correlation matrix.
    Blue = negative correlation (complementary, good)
    Red  = positive correlation (similar, not useful for peer learning)
    """
    fig, ax = plt.subplots(figsize=(12, 10))
    im = ax.imshow(correlation_matrix, cmap="RdBu_r", vmin=-1, vmax=1, aspect="auto")

    # Show a subset of student IDs on the axes to avoid clutter
    step = 5
    ticks = range(0, len(student_ids), step)
    labels = [student_ids[i] for i in ticks]
    ax.set_xticks(ticks); ax.set_xticklabels(labels, rotation=45, ha="right", fontsize=8)
    ax.set_yticks(ticks); ax.set_yticklabels(labels, fontsize=8)

    ax.set_title("Student-Student Correlation Heatmap\n"
                 "(Blue = complementary pair, Red = similar)")
    fig.colorbar(im, ax=ax, label="Pearson correlation")
    plt.tight_layout()
    plt.savefig("chart_complementarity_heatmap.png", dpi=150)
    plt.close()
    print("  Saved chart_complementarity_heatmap.png")


# ===================================================================
# SECTION 5 — SUMMARY PRINT
# ===================================================================

def print_summary(all_pairs, top_pairs):
    print("\n" + "=" * 60)
    print("COMPLEMENTARITY ANALYSIS SUMMARY")
    print("=" * 60)
    print(f"Total unique pairs analysed: {len(all_pairs)}")

    correlations = [p["correlation"] for p in all_pairs]
    print(f"\nCorrelation statistics:")
    print(f"  Mean:   {np.mean(correlations):+.4f}")
    print(f"  Min:    {min(correlations):+.4f}  (most complementary)")
    print(f"  Max:    {max(correlations):+.4f}  (most similar)")
    print(f"  Median: {np.median(correlations):+.4f}")

    print(f"\nTop 10 most complementary pairs:")
    print(f"  {'Rank':<5} {'Student A':<10} {'Student B':<10} {'Correlation':<12} {'Score'}")
    for i, p in enumerate(top_pairs[:10], 1):
        print(f"  {i:<5} {p['student_a']:<10} {p['student_b']:<10} "
              f"{p['correlation']:+.4f}      {p['complementarity_score']:.4f}")

    print("=" * 60 + "\n")


# ===================================================================
# MAIN
# ===================================================================

def main():
    print("Connecting to Neo4j ...")
    driver.verify_connectivity()
    print("  Connected.\n")

    print("Loading student score matrix ...")
    student_ids, score_matrix = load_score_matrix()
    print(f"  Loaded {len(student_ids)} students x {score_matrix.shape[1]} topics\n")

    print("Computing correlation matrix ...")
    correlation_matrix = compute_correlation_matrix(score_matrix)
    print(f"  Shape: {correlation_matrix.shape}\n")

    print("Ranking complementary pairs ...")
    all_pairs = rank_pairs(correlation_matrix, student_ids)
    top_pairs = all_pairs[:TOP_N_PAIRS]
    print(f"  Ranked {len(all_pairs)} pairs, keeping top {TOP_N_PAIRS}\n")

    print("Writing :COMPLEMENTS edges to Neo4j ...")
    write_complements_to_neo4j(top_pairs)

    print("\nSaving JSON reports ...")
    with open(MATRIX_OUTPUT, "w", encoding="utf-8") as f:
        json.dump({
            "student_ids": student_ids,
            "matrix": correlation_matrix.round(4).tolist(),
        }, f, indent=2)
    print(f"  Saved {MATRIX_OUTPUT}")

    with open(PAIRS_OUTPUT, "w", encoding="utf-8") as f:
        json.dump({
            "total_pairs_analysed": len(all_pairs),
            "top_pairs": top_pairs,
            "all_pairs": all_pairs,
        }, f, indent=2)
    print(f"  Saved {PAIRS_OUTPUT}")

    print("\nBuilding heatmap ...")
    chart_heatmap(correlation_matrix, student_ids)

    print_summary(all_pairs, top_pairs)

    driver.close()
    print("All done. Verify in Neo4j with this query:")
    print("  MATCH (a:Student)-[r:COMPLEMENTS]-(b:Student) RETURN a, r, b\n")


if __name__ == "__main__":
    main()
