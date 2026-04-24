"""
app.py
------
Flask REST API for the BECE Social Learning Network system.

This API serves data from Neo4j to the React dashboard.
Each endpoint returns JSON that the frontend can display.

Run from the bece-sln folder:
    python app.py

The API runs at http://localhost:5000
Test in your browser: http://localhost:5000/api/health
"""

import json
import os
from flask import Flask, jsonify
from flask_cors import CORS
from neo4j import GraphDatabase
from dotenv import load_dotenv

# -------------------------------------------------------------------
# SETUP
# -------------------------------------------------------------------
load_dotenv()
app = Flask(__name__)
CORS(app)  # allows React frontend to connect

driver = GraphDatabase.driver(
    os.getenv("NEO4J_URI"),
    auth=(os.getenv("NEO4J_USERNAME"), os.getenv("NEO4J_PASSWORD"))
)


# ===================================================================
# HEALTH CHECK — test if API and database are working
# ===================================================================

@app.route("/api/health", methods=["GET"])
def health_check():
    """Quick check that the API is running and Neo4j is reachable."""
    try:
        driver.verify_connectivity()
        return jsonify({
            "status": "healthy",
            "database": "connected",
            "message": "BECE SLN API is running"
        })
    except Exception as e:
        return jsonify({
            "status": "unhealthy",
            "database": "disconnected",
            "error": str(e)
        }), 500


# ===================================================================
# STUDENTS
# ===================================================================

@app.route("/api/students", methods=["GET"])
def get_students():
    """Return all 50 students with their average scores and profiles."""
    with driver.session() as session:
        result = session.run("""
            MATCH (s:Student)-[r:SCORED]->(t:Topic)
            WITH s, avg(r.score) AS avg_score, count(t) AS topic_count
            RETURN s.id AS id, s.profile_type AS profile,
                   round(avg_score, 3) AS average_score, topic_count
            ORDER BY s.id
        """)
        students = [dict(record) for record in result]
    return jsonify({"students": students, "count": len(students)})


@app.route("/api/students/<student_id>", methods=["GET"])
def get_student_detail(student_id):
    """Return a single student's scores across all topics, grouped by subject."""
    with driver.session() as session:
        # Get student info
        student = session.run("""
            MATCH (s:Student {id: $id})-[r:SCORED]->(t:Topic)
            WITH s, avg(r.score) AS avg_score
            RETURN s.id AS id, s.profile_type AS profile,
                   round(avg_score, 3) AS average_score
        """, id=student_id).single()

        if not student:
            return jsonify({"error": f"Student {student_id} not found"}), 404

        # Get all scores grouped by subject
        scores = session.run("""
            MATCH (s:Student {id: $id})-[r:SCORED]->(t:Topic)
            RETURN t.id AS topic_id, t.name AS topic_name,
                   t.subject AS subject, t.difficulty AS difficulty,
                   round(r.score, 3) AS score
            ORDER BY t.subject, t.id
        """, id=student_id)
        score_list = [dict(record) for record in scores]

        # Group by subject
        subjects = {}
        for s in score_list:
            subj = s["subject"]
            if subj not in subjects:
                subjects[subj] = []
            subjects[subj].append(s)

    return jsonify({
        "student": dict(student),
        "scores_by_subject": subjects,
        "total_topics": len(score_list)
    })


# ===================================================================
# TOPICS
# ===================================================================

@app.route("/api/topics", methods=["GET"])
def get_topics():
    """Return all 80 topics with their class averages and failure counts."""
    with driver.session() as session:
        result = session.run("""
            MATCH (s:Student)-[r:SCORED]->(t:Topic)
            WITH t, avg(r.score) AS class_avg,
                 sum(CASE WHEN r.score < 0.4 THEN 1 ELSE 0 END) AS failing_count
            RETURN t.id AS id, t.name AS name, t.subject AS subject,
                   t.difficulty AS difficulty,
                   round(class_avg, 3) AS class_average,
                   failing_count
            ORDER BY class_avg ASC
        """)
        topics = [dict(record) for record in result]
    return jsonify({"topics": topics, "count": len(topics)})


@app.route("/api/topics/weakest", methods=["GET"])
def get_weakest_topics():
    """Return the 10 topics with the lowest class averages."""
    with driver.session() as session:
        result = session.run("""
            MATCH (s:Student)-[r:SCORED]->(t:Topic)
            WITH t, avg(r.score) AS class_avg,
                 sum(CASE WHEN r.score < 0.4 THEN 1 ELSE 0 END) AS failing_count
            RETURN t.id AS id, t.name AS name, t.subject AS subject,
                   t.difficulty AS difficulty,
                   round(class_avg, 3) AS class_average,
                   failing_count
            ORDER BY class_avg ASC
            LIMIT 10
        """)
        topics = [dict(record) for record in result]
    return jsonify({"weakest_topics": topics})


# ===================================================================
# SUBJECTS
# ===================================================================

@app.route("/api/subjects", methods=["GET"])
def get_subjects():
    """Return average scores per subject."""
    with driver.session() as session:
        result = session.run("""
            MATCH (s:Student)-[r:SCORED]->(t:Topic)
            WITH t.subject AS subject, avg(r.score) AS subject_avg
            RETURN subject, round(subject_avg, 3) AS average
            ORDER BY subject_avg ASC
        """)
        subjects = [dict(record) for record in result]
    return jsonify({"subjects": subjects})


# ===================================================================
# COMPLEMENTARITY
# ===================================================================

@app.route("/api/complementary-pairs", methods=["GET"])
def get_complementary_pairs():
    """Return the top 20 complementary student pairs from the graph."""
    with driver.session() as session:
        result = session.run("""
            MATCH (a:Student)-[r:COMPLEMENTS]->(b:Student)
            RETURN a.id AS student_a, b.id AS student_b,
                   r.score AS complementarity_score,
                   r.correlation AS correlation
            ORDER BY r.score DESC
        """)
        pairs = [dict(record) for record in result]
    return jsonify({"pairs": pairs, "count": len(pairs)})


# ===================================================================
# TOPIC DEPENDENCIES (PREDICTIVE MODEL)
# ===================================================================

@app.route("/api/topic-dependencies", methods=["GET"])
def get_topic_dependencies():
    """Return topic-topic dependencies from the predictive model."""
    with driver.session() as session:
        result = session.run("""
            MATCH (a:Topic)-[r:DEPENDS_ON]->(b:Topic)
            RETURN a.id AS topic_a_id, a.name AS topic_a_name,
                   a.subject AS topic_a_subject,
                   b.id AS topic_b_id, b.name AS topic_b_name,
                   b.subject AS topic_b_subject,
                   r.correlation AS correlation,
                   r.prediction_accuracy AS prediction_accuracy
            ORDER BY r.correlation DESC
        """)
        dependencies = [dict(record) for record in result]
    return jsonify({"dependencies": dependencies, "count": len(dependencies)})


# ===================================================================
# PEER GROUPS (from Samuel's clustering — reads peer_groups.json)
# ===================================================================

@app.route("/api/peer-groups", methods=["GET"])
def get_peer_groups():
    """
    Return the recommended peer study groups.
    Reads from peer_groups.json (produced by Samuel's ai_clustering.py).
    If Samuel hasn't finished yet, returns a placeholder message.
    """
    try:
        with open("peer_groups.json", "r", encoding="utf-8") as f:
            data = json.load(f)
        return jsonify(data)
    except FileNotFoundError:
        return jsonify({
            "message": "Peer groups not yet generated. Run ai_clustering.py first.",
            "groups": []
        }), 404


# ===================================================================
# SIR SIMULATION RESULTS
# ===================================================================

@app.route("/api/sir-results", methods=["GET"])
def get_sir_results():
    """
    Return SIR simulation results.
    Reads from sir_simulation_report.json.
    """
    try:
        with open("sir_simulation_report.json", "r", encoding="utf-8") as f:
            data = json.load(f)
        return jsonify(data)
    except FileNotFoundError:
        return jsonify({
            "message": "SIR simulation not yet run. Run sir_simulation.py first.",
        }), 404


# ===================================================================
# DASHBOARD SUMMARY — one endpoint for the main dashboard view
# ===================================================================

@app.route("/api/dashboard", methods=["GET"])
def get_dashboard_summary():
    """
    Aggregate endpoint that returns everything the main dashboard needs
    in a single request. This avoids the frontend making 6 separate calls.
    """
    with driver.session() as session:
        # Overall class stats
        class_stats = session.run("""
            MATCH (s:Student)-[r:SCORED]->(t:Topic)
            RETURN round(avg(r.score), 3) AS class_average,
                   count(DISTINCT s) AS total_students,
                   count(DISTINCT t) AS total_topics
        """).single()

        # Top 5 weakest topics
        weakest = session.run("""
            MATCH (s:Student)-[r:SCORED]->(t:Topic)
            WITH t, avg(r.score) AS avg_score
            RETURN t.name AS name, t.subject AS subject,
                   round(avg_score, 3) AS average
            ORDER BY avg_score ASC LIMIT 5
        """)
        weakest_topics = [dict(r) for r in weakest]

        # Top 5 struggling students
        struggling = session.run("""
            MATCH (s:Student)-[r:SCORED]->(t:Topic)
            WITH s, avg(r.score) AS avg_score
            RETURN s.id AS id, s.profile_type AS profile,
                   round(avg_score, 3) AS average
            ORDER BY avg_score ASC LIMIT 5
        """)
        struggling_students = [dict(r) for r in struggling]

        # Subject averages
        subjects = session.run("""
            MATCH (s:Student)-[r:SCORED]->(t:Topic)
            WITH t.subject AS subject, avg(r.score) AS avg_score
            RETURN subject, round(avg_score, 3) AS average
            ORDER BY avg_score ASC
        """)
        subject_averages = [dict(r) for r in subjects]

        # Complementary pairs count
        comp_count = session.run("""
            MATCH ()-[r:COMPLEMENTS]->() RETURN count(r) AS count
        """).single()["count"]

        # Dependencies count
        dep_count = session.run("""
            MATCH ()-[r:DEPENDS_ON]->() RETURN count(r) AS count
        """).single()["count"]

    return jsonify({
        "class_average": class_stats["class_average"],
        "total_students": class_stats["total_students"],
        "total_topics": class_stats["total_topics"],
        "weakest_topics": weakest_topics,
        "struggling_students": struggling_students,
        "subject_averages": subject_averages,
        "complementary_pairs": comp_count,
        "topic_dependencies": dep_count,
    })


# ===================================================================
# RUN THE SERVER
# ===================================================================

if __name__ == "__main__":
    print("\n" + "=" * 50)
    print("BECE SLN — API SERVER")
    print("=" * 50)
    print("Starting Flask server ...")
    print("API running at: http://localhost:5000")
    print("Test it:         http://localhost:5000/api/health")
    print("Dashboard data:  http://localhost:5000/api/dashboard")
    print("\nPress Ctrl+C to stop the server.\n")
    app.run(debug=True, port=5000)
