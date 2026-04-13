"""
generate_students.py
--------------------
Generates synthetic performance data for 50 JSS3 students across the 80 BECE
topics defined in topics.json.

Each student is assigned a "profile type" (strong, average, struggling, or mixed)
which controls how their scores are distributed across subjects. This produces
realistic patterns — not every student is equally good at every subject.

OUTPUT: students.json  (the file that load_to_neo4j.py will read)

Run from terminal:
    python generate_students.py
"""

import json
import random
import numpy as np
from pathlib import Path

# -------------------------------------------------------------------
# CONFIGURATION — change these if you want to tune the simulation
# -------------------------------------------------------------------
NUM_STUDENTS = 50            # matches Chapter 3 Section 3.1
RANDOM_SEED = 42             # fixed so results are reproducible every run
OUTPUT_FILE = "students.json"
TOPICS_FILE = "topics.json"

# Difficulty multipliers — harder topics pull scores down
DIFFICULTY_FACTOR = {
    "Easy":   1.00,   # no penalty
    "Medium": 0.85,   # 15% reduction on average
    "Hard":   0.70    # 30% reduction on average
}

# Student profile distribution (out of NUM_STUDENTS)
#   strong     -> consistently high scores
#   average    -> moderate scores across all subjects
#   struggling -> consistently low scores
#   mixed      -> strong in some subjects, weak in others (ideal for complementarity)
PROFILE_DISTRIBUTION = {
    "strong":     10,   # 20% of class
    "average":    15,   # 30%
    "struggling": 10,   # 20%
    "mixed":      15    # 30% — most important for peer pairing
}

# Base score ranges per profile (before difficulty adjustment)
#   (mean, standard_deviation) — scores are drawn from a normal distribution
PROFILE_RANGES = {
    "strong":     (0.85, 0.08),   # mean 85%, tight spread
    "average":    (0.65, 0.12),
    "struggling": (0.40, 0.10),
    "mixed":      (0.60, 0.20)    # wide spread = strong in some, weak in others
}


# -------------------------------------------------------------------
# LOAD TOPICS
# -------------------------------------------------------------------
def load_topics():
    """Read topics.json and return a flat list of all 80 topics with subject names attached."""
    with open(TOPICS_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    all_topics = []
    for subject in data["subjects"]:
        for topic in subject["topics"]:
            all_topics.append({
                "id": topic["id"],
                "name": topic["name"],
                "difficulty": topic["difficulty"],
                "subject": subject["name"]
            })
    return all_topics


# -------------------------------------------------------------------
# GENERATE STUDENT SCORES
# -------------------------------------------------------------------
def generate_score(profile, difficulty, subject_bias=0.0):
    """
    Generate a single score for a student on a topic.
    Returns a float between 0.0 and 1.0.

    profile      -> the student's general ability level
    difficulty   -> the topic's difficulty (Easy/Medium/Hard)
    subject_bias -> adjustment for students who are stronger in certain subjects
                    (used for 'mixed' profile students)
    """
    mean, std = PROFILE_RANGES[profile]
    raw_score = np.random.normal(mean, std)       # draw from normal distribution
    raw_score += subject_bias                     # apply subject-level bias
    raw_score *= DIFFICULTY_FACTOR[difficulty]    # apply difficulty penalty
    # Clamp to valid range [0.0, 1.0]
    return max(0.0, min(1.0, raw_score))


def assign_profiles():
    """Create a list of profile labels for all students, then shuffle."""
    profiles = []
    for profile_type, count in PROFILE_DISTRIBUTION.items():
        profiles.extend([profile_type] * count)
    random.shuffle(profiles)
    return profiles


def generate_subject_biases(subjects):
    """
    For 'mixed' profile students, create per-subject bias values.
    Some subjects get a boost (+0.15), others get a penalty (-0.15).
    This creates the complementary strength/weakness pattern we need.
    """
    biases = {}
    # Randomly pick ~half the subjects as "strong" for this student
    strong_subjects = random.sample(subjects, len(subjects) // 2)
    for subj in subjects:
        biases[subj] = 0.15 if subj in strong_subjects else -0.15
    return biases


def generate_students(topics):
    """Build the full student list with scores on every topic."""
    # Get unique subject names for the bias system
    subjects = list({t["subject"] for t in topics})

    profiles = assign_profiles()
    students = []

    for i in range(NUM_STUDENTS):
        student_id = f"STU{(i+1):03d}"   # STU001, STU002, ... STU050
        profile = profiles[i]

        # For mixed students, generate per-subject biases
        if profile == "mixed":
            biases = generate_subject_biases(subjects)
        else:
            biases = {subj: 0.0 for subj in subjects}

        # Generate scores for all 80 topics
        scores = []
        for topic in topics:
            score = generate_score(
                profile=profile,
                difficulty=topic["difficulty"],
                subject_bias=biases[topic["subject"]]
            )
            scores.append({
                "topic_id": topic["id"],
                "score": round(score, 3)   # keep 3 decimal places
            })

        students.append({
            "student_id": student_id,
            "profile_type": profile,        # stored for analysis/validation
            "scores": scores
        })

    return students


# -------------------------------------------------------------------
# SUMMARY STATISTICS — useful for confirming the data looks realistic
# -------------------------------------------------------------------
def print_summary(students, topics):
    print("\n" + "=" * 60)
    print("SYNTHETIC STUDENT DATA SUMMARY")
    print("=" * 60)
    print(f"Total students generated: {len(students)}")
    print(f"Total topics per student: {len(topics)}")
    print(f"Total edges (student-topic scores): {len(students) * len(topics)}")

    # Profile breakdown
    profile_counts = {}
    for s in students:
        profile_counts[s["profile_type"]] = profile_counts.get(s["profile_type"], 0) + 1
    print("\nProfile distribution:")
    for p, c in profile_counts.items():
        print(f"  {p:12s}: {c} students")

    # Overall average score
    all_scores = [score["score"] for s in students for score in s["scores"]]
    print(f"\nOverall average score: {np.mean(all_scores):.3f}")
    print(f"Overall score std dev: {np.std(all_scores):.3f}")
    print(f"Min score: {min(all_scores):.3f}   Max score: {max(all_scores):.3f}")

    # Average by difficulty
    print("\nAverage score by difficulty:")
    for difficulty in ["Easy", "Medium", "Hard"]:
        topic_ids_of_difficulty = {t["id"] for t in topics if t["difficulty"] == difficulty}
        scores_of_difficulty = [
            score["score"]
            for s in students
            for score in s["scores"]
            if score["topic_id"] in topic_ids_of_difficulty
        ]
        print(f"  {difficulty:7s}: {np.mean(scores_of_difficulty):.3f}")

    print("=" * 60 + "\n")


# -------------------------------------------------------------------
# MAIN
# -------------------------------------------------------------------
def main():
    # Set random seeds for reproducibility
    random.seed(RANDOM_SEED)
    np.random.seed(RANDOM_SEED)

    # Confirm topics file exists
    if not Path(TOPICS_FILE).exists():
        print(f"ERROR: {TOPICS_FILE} not found in current folder.")
        print("Make sure you run this script from the backend folder.")
        return

    # Load topics and generate students
    topics = load_topics()
    print(f"Loaded {len(topics)} topics from {TOPICS_FILE}")

    students = generate_students(topics)
    print(f"Generated {len(students)} synthetic students")

    # Save to students.json
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump({"students": students}, f, indent=2)
    print(f"Saved to {OUTPUT_FILE}")

    # Print summary statistics
    print_summary(students, topics)


if __name__ == "__main__":
    main()