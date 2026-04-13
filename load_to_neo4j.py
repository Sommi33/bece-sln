"""
load_to_neo4j.py
----------------
Loads the topics and synthetic student data into Neo4j AuraDB.

GRAPH STRUCTURE:
  Nodes:
    (:Student  {id, profile_type})                    -- 50 nodes
    (:Topic    {id, name, subject, difficulty})       -- 80 nodes
    (:Subject  {name})                                -- 9 nodes (helper grouping)

  Relationships:
    (Student)-[:SCORED {score}]->(Topic)              -- 4000 weighted edges
    (Topic)-[:BELONGS_TO]->(Subject)                  -- 80 edges

The :Subject node isn't required by Chapter 3 but it makes visualisation and
subject-level queries much easier. Add/remove freely.

Run from terminal (inside backend folder):
    python load_to_neo4j.py
"""

import json
import os
from pathlib import Path
from neo4j import GraphDatabase
from dotenv import load_dotenv

# -------------------------------------------------------------------
# LOAD ENVIRONMENT VARIABLES FROM .env
# -------------------------------------------------------------------
load_dotenv()

NEO4J_URI      = os.getenv("NEO4J_URI")
NEO4J_USERNAME = os.getenv("NEO4J_USERNAME")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")

TOPICS_FILE   = "topics.json"
STUDENTS_FILE = "students.json"


# -------------------------------------------------------------------
# VALIDATION — make sure everything is ready before we start
# -------------------------------------------------------------------
def validate_setup():
    errors = []
    if not NEO4J_URI:
        errors.append("NEO4J_URI missing from .env")
    if not NEO4J_USERNAME:
        errors.append("NEO4J_USERNAME missing from .env")
    if not NEO4J_PASSWORD:
        errors.append("NEO4J_PASSWORD missing from .env")
    if not Path(TOPICS_FILE).exists():
        errors.append(f"{TOPICS_FILE} not found — did you save it in the backend folder?")
    if not Path(STUDENTS_FILE).exists():
        errors.append(f"{STUDENTS_FILE} not found — run generate_students.py first")
    if errors:
        print("SETUP ERRORS:")
        for e in errors:
            print(f"  - {e}")
        return False
    return True


# -------------------------------------------------------------------
# NEO4J LOADER CLASS
# -------------------------------------------------------------------
class GraphLoader:
    def __init__(self, uri, user, password):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self):
        self.driver.close()

    # ----- Step 1: Wipe existing data so re-runs start clean -----
    def clear_database(self):
        with self.driver.session() as session:
            session.run("MATCH (n) DETACH DELETE n")
        print("  Cleared all existing data")

    # ----- Step 2: Create uniqueness constraints -----
    def create_constraints(self):
        """
        Constraints prevent duplicate nodes and speed up lookups.
        Neo4j automatically creates an index for each constraint.
        """
        queries = [
            "CREATE CONSTRAINT student_id IF NOT EXISTS FOR (s:Student) REQUIRE s.id IS UNIQUE",
            "CREATE CONSTRAINT topic_id   IF NOT EXISTS FOR (t:Topic)   REQUIRE t.id IS UNIQUE",
            "CREATE CONSTRAINT subject_name IF NOT EXISTS FOR (sub:Subject) REQUIRE sub.name IS UNIQUE",
        ]
        with self.driver.session() as session:
            for q in queries:
                session.run(q)
        print("  Created uniqueness constraints on Student.id, Topic.id, Subject.name")

    # ----- Step 3: Load subjects and topics from topics.json -----
    def load_topics(self, topics_data):
        total_topics = 0
        total_subjects = 0
        with self.driver.session() as session:
            for subject in topics_data["subjects"]:
                # Create Subject node
                session.run(
                    "MERGE (s:Subject {name: $name})",
                    name=subject["name"]
                )
                total_subjects += 1

                # Create Topic nodes and link to Subject
                for topic in subject["topics"]:
                    session.run(
                        """
                        MERGE (t:Topic {id: $id})
                        SET   t.name = $name,
                              t.difficulty = $difficulty,
                              t.subject = $subject
                        WITH t
                        MATCH (s:Subject {name: $subject})
                        MERGE (t)-[:BELONGS_TO]->(s)
                        """,
                        id=topic["id"],
                        name=topic["name"],
                        difficulty=topic["difficulty"],
                        subject=subject["name"]
                    )
                    total_topics += 1
        print(f"  Loaded {total_subjects} subjects and {total_topics} topics")
        return total_topics, total_subjects

    # ----- Step 4: Load students and their SCORED relationships -----
    def load_students(self, students_data):
        total_students = 0
        total_scores = 0
        with self.driver.session() as session:
            for student in students_data["students"]:
                # Create Student node
                session.run(
                    """
                    MERGE (s:Student {id: $id})
                    SET   s.profile_type = $profile_type
                    """,
                    id=student["student_id"],
                    profile_type=student["profile_type"]
                )
                total_students += 1

                # Batch-create all SCORED relationships for this student using UNWIND
                # (much faster than one query per score)
                session.run(
                    """
                    MATCH (s:Student {id: $student_id})
                    UNWIND $scores AS entry
                    MATCH (t:Topic {id: entry.topic_id})
                    MERGE (s)-[r:SCORED]->(t)
                    SET   r.score = entry.score
                    """,
                    student_id=student["student_id"],
                    scores=student["scores"]
                )
                total_scores += len(student["scores"])
        print(f"  Loaded {total_students} students and {total_scores} SCORED relationships")
        return total_students, total_scores

    # ----- Step 5: Verify the graph by running summary queries -----
    def verify(self):
        with self.driver.session() as session:
            counts = session.run("""
                MATCH (s:Student) WITH count(s) AS students
                MATCH (t:Topic)   WITH students, count(t) AS topics
                MATCH (sub:Subject) WITH students, topics, count(sub) AS subjects
                MATCH ()-[r:SCORED]->() WITH students, topics, subjects, count(r) AS scored
                MATCH ()-[b:BELONGS_TO]->() RETURN students, topics, subjects, scored, count(b) AS belongs_to
            """).single()

            print("\n  GRAPH VERIFICATION:")
            print(f"    Student nodes:        {counts['students']}")
            print(f"    Topic nodes:          {counts['topics']}")
            print(f"    Subject nodes:        {counts['subjects']}")
            print(f"    SCORED relationships: {counts['scored']}")
            print(f"    BELONGS_TO rels:      {counts['belongs_to']}")

            # Sample a student to sanity-check
            sample = session.run("""
                MATCH (s:Student)-[r:SCORED]->(t:Topic)
                WITH s, avg(r.score) AS avg_score, count(r) AS topic_count
                RETURN s.id AS id, s.profile_type AS profile,
                       round(avg_score, 3) AS avg_score, topic_count
                ORDER BY s.id
                LIMIT 5
            """)
            print("\n  Sample of first 5 students:")
            print(f"    {'ID':<8} {'Profile':<12} {'Avg Score':<12} {'Topics'}")
            for record in sample:
                print(f"    {record['id']:<8} {record['profile']:<12} "
                      f"{record['avg_score']:<12} {record['topic_count']}")


# -------------------------------------------------------------------
# MAIN
# -------------------------------------------------------------------
def main():
    print("=" * 60)
    print("BECE SLN — NEO4J GRAPH LOADER")
    print("=" * 60)

    if not validate_setup():
        return

    # Load JSON files
    with open(TOPICS_FILE, "r", encoding="utf-8") as f:
        topics_data = json.load(f)
    with open(STUDENTS_FILE, "r", encoding="utf-8") as f:
        students_data = json.load(f)

    print(f"Connecting to Neo4j at {NEO4J_URI} ...")
    loader = GraphLoader(NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD)

    try:
        # Verify connectivity
        loader.driver.verify_connectivity()
        print("  Connection successful\n")

        print("Step 1/4: Clearing existing data")
        loader.clear_database()

        print("Step 2/4: Creating constraints")
        loader.create_constraints()

        print("Step 3/4: Loading subjects and topics")
        loader.load_topics(topics_data)

        print("Step 4/4: Loading students and scores")
        loader.load_students(students_data)

        loader.verify()

        print("\n" + "=" * 60)
        print("KNOWLEDGE GRAPH SUCCESSFULLY BUILT")
        print("=" * 60)
        print("\nNext step: open Neo4j Aura -> Query, and try:")
        print("  MATCH (n) RETURN n LIMIT 100")
        print("to see your graph visualised.\n")

    except Exception as e:
        print(f"\nERROR: {e}")
        print("\nCommon fixes:")
        print("  - Wrong password in .env -> reset and update")
        print("  - Instance paused -> resume in Neo4j Aura console")
        print("  - No internet connection")
    finally:
        loader.close()


if __name__ == "__main__":
    main()