import json
import os
from flask import Flask, jsonify, send_file
from flask_cors import CORS
from neo4j import GraphDatabase
from dotenv import load_dotenv

load_dotenv()
app = Flask(__name__)
CORS(app) 

@app.route("/")
def serve_dashboard():
    return send_file("dashboard.html")

@app.route("/chart.min.js")
def serve_chartjs():
    return send_file("chart.min.js")

driver = GraphDatabase.driver(
    os.getenv("NEO4J_URI"),
    auth=(os.getenv("NEO4J_USERNAME"), os.getenv("NEO4J_PASSWORD"))
)



@app.route("/api/health", methods=["GET"])
def health_check():
    
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


@app.route("/api/students", methods=["GET"])
def get_students():
    
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
    
    with driver.session() as session:
        
        student = session.run("""
            MATCH (s:Student {id: $id})-[r:SCORED]->(t:Topic)
            WITH s, avg(r.score) AS avg_score
            RETURN s.id AS id, s.profile_type AS profile,
                   round(avg_score, 3) AS average_score
        """, id=student_id).single()

        if not student:
            return jsonify({"error": f"Student {student_id} not found"}), 404

        scores = session.run("""
            MATCH (s:Student {id: $id})-[r:SCORED]->(t:Topic)
            RETURN t.id AS topic_id, t.name AS topic_name,
                   t.subject AS subject, t.difficulty AS difficulty,
                   round(r.score, 3) AS score
            ORDER BY t.subject, t.id
        """, id=student_id)
        score_list = [dict(record) for record in scores]

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



@app.route("/api/topics", methods=["GET"])
def get_topics():
    
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



@app.route("/api/subjects", methods=["GET"])
def get_subjects():
    with driver.session() as session:
        result = session.run("""
            MATCH (s:Student)-[r:SCORED]->(t:Topic)
            WITH t.subject AS subject, avg(r.score) AS subject_avg
            RETURN subject, round(subject_avg, 3) AS average
            ORDER BY subject_avg ASC
        """)
        subjects = [dict(record) for record in result]
    return jsonify({"subjects": subjects})



@app.route("/api/complementary-pairs", methods=["GET"])
def get_complementary_pairs():
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



@app.route("/api/topic-dependencies", methods=["GET"])
def get_topic_dependencies():
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



@app.route("/api/peer-groups", methods=["GET"])
def get_peer_groups():
    try:
        with open("peer_groups.json", "r", encoding="utf-8") as f:
            data = json.load(f)
        return jsonify(data)
    except FileNotFoundError:
        return jsonify({
            "message": "Peer groups not yet generated. Run ai_clustering.py first.",
            "groups": []
        }), 404



@app.route("/api/sir-results", methods=["GET"])
def get_sir_results():
    try:
        with open("sir_simulation_report.json", "r", encoding="utf-8") as f:
            data = json.load(f)
        return jsonify(data)
    except FileNotFoundError:
        return jsonify({
            "message": "SIR simulation not yet run. Run sir_simulation.py first.",
        }), 404



@app.route("/api/dashboard", methods=["GET"])
def get_dashboard_summary():
    with driver.session() as session:
        class_stats = session.run("""
            MATCH (s:Student)-[r:SCORED]->(t:Topic)
            RETURN round(avg(r.score), 3) AS class_average,
                   count(DISTINCT s) AS total_students,
                   count(DISTINCT t) AS total_topics
        """).single()

        weakest = session.run("""
            MATCH (s:Student)-[r:SCORED]->(t:Topic)
            WITH t, avg(r.score) AS avg_score
            RETURN t.name AS name, t.subject AS subject,
                   round(avg_score, 3) AS average
            ORDER BY avg_score ASC LIMIT 5
        """)
        weakest_topics = [dict(r) for r in weakest]

        struggling = session.run("""
            MATCH (s:Student)-[r:SCORED]->(t:Topic)
            WITH s, avg(r.score) AS avg_score
            RETURN s.id AS id, s.profile_type AS profile,
                   round(avg_score, 3) AS average
            ORDER BY avg_score ASC LIMIT 5
        """)
        struggling_students = [dict(r) for r in struggling]

        subjects = session.run("""
            MATCH (s:Student)-[r:SCORED]->(t:Topic)
            WITH t.subject AS subject, avg(r.score) AS avg_score
            RETURN subject, round(avg_score, 3) AS average
            ORDER BY avg_score ASC
        """)
        subject_averages = [dict(r) for r in subjects]

        comp_count = session.run("""
            MATCH ()-[r:COMPLEMENTS]->() RETURN count(r) AS count
        """).single()["count"]

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

@app.route("/api/peer-pairing/<topic_id>", methods=["GET"])
def get_topic_pairs(topic_id):
    with driver.session() as session:
        strong = list(session.run("""
            MATCH (s:Student)-[r:SCORED]->(t:Topic {id: $id})
            WHERE r.score >= 0.7
            RETURN s.id AS id, s.profile_type AS profile,
                   round(r.score, 3) AS score
            ORDER BY r.score DESC
        """, id=topic_id))
        weak = list(session.run("""
            MATCH (s:Student)-[r:SCORED]->(t:Topic {id: $id})
            WHERE r.score < 0.4
            RETURN s.id AS id, s.profile_type AS profile,
                   round(r.score, 3) AS score
            ORDER BY r.score ASC
        """, id=topic_id))
        topic = session.run("""
            MATCH (t:Topic {id: $id})
            RETURN t.name AS name, t.subject AS subject,
                   t.difficulty AS difficulty
        """, id=topic_id).single()
        if not topic:
            return jsonify({"error": "Topic not found"}), 404
        teaches = list(session.run("""
            MATCH (a:Student)-[r:TEACHES]->(b:Student)
            WHERE r.topic_id = $id
            RETURN a.id AS tutor, b.id AS learner,
                   r.strong_score AS tutor_score,
                   r.weak_score AS learner_score,
                   r.score_gap AS gap
            ORDER BY r.score_gap DESC
        """, id=topic_id))
    return jsonify({
        "topic_id": topic_id,
        "topic_name": topic["name"],
        "subject": topic["subject"],
        "difficulty": topic["difficulty"],
        "strong_students": [dict(r) for r in strong],
        "weak_students": [dict(r) for r in weak],
        "teaching_pairs": [dict(r) for r in teaches],
        "diffusion_possible": len(strong) > 0
    })


@app.route("/api/peer-pairing/summary", methods=["GET"])
def get_topic_pairs_summary():
    try:
        with open("topic_peer_pairs.json", "r", encoding="utf-8") as f:
            data = json.load(f)
        return jsonify(data)
    except FileNotFoundError:
        return jsonify({"message": "Run topic_peer_pairing.py first."}), 404

if __name__ == "__main__":
    print("\n" + "=" * 50)
    print("BECE SLN — API SERVER")
    print("=" * 50)
    print("Starting Flask server ...")
    print("API running at: http://localhost:5000")
    print("Test it:         http://localhost:5000/api/health")
    print("Dashboard data:  http://localhost:5000/api/dashboard")
    print("\nPress Ctrl+C to stop the server.\n")
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)