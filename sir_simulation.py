"""
sir_simulation.py
-----------------
Module owner: Chisom
SIR Knowledge Diffusion Simulation

Simulates how knowledge of a topic spreads through the peer learning
network over time, using the SIR (Susceptible-Informed-Recovered) model
adapted from epidemiology.

This module:
  1. Picks a topic and classifies students as S, I, or R based on scores
  2. Runs the SIR differential equations using SciPy
  3. Produces S/I/R curves over time (the classic epidemic curve)
  4. Repeats for multiple topics and compares diffusion speed
  5. Saves charts and a JSON report

The SIR equations:
  dS/dt = -β * S * I      (susceptible students learn from informed ones)
  dI/dt =  β * S * I - γ * I   (informed students either teach or master)
  dR/dt =  γ * I           (informed students eventually master the topic)

Where:
  β = learning rate (how fast knowledge spreads between peers)
  γ = mastery rate (how fast a student goes from "just learned" to "mastered")

Run from the bece-sln folder:
    python sir_simulation.py
"""

import json
import os
import numpy as np
from scipy.integrate import odeint
from neo4j import GraphDatabase
from dotenv import load_dotenv
import matplotlib.pyplot as plt

# -------------------------------------------------------------------
# CONFIGURATION
# -------------------------------------------------------------------
# SIR model parameters
BETA = 0.3          # learning rate — how fast knowledge spreads
GAMMA = 0.1         # mastery rate — how fast students fully master a topic
TIME_DAYS = 60      # simulate over 60 days of peer learning
TIME_POINTS = 200   # number of time points to compute (more = smoother curves)

# Score thresholds for classifying students
INFORMED_THRESHOLD = 0.7    # students scoring above this already know the topic
SUSCEPTIBLE_THRESHOLD = 0.4  # students scoring below this need to learn it
# Students between 0.4 and 0.7 are treated as "partially informed" -> Susceptible

# Topics to simulate (we'll pick the 5 hardest + 5 easiest for comparison)
NUM_TOPICS_PER_CATEGORY = 5

OUTPUT_FILE = "sir_simulation_report.json"

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

def load_topic_scores():
    """
    For each topic, get the list of all 50 student scores.
    Returns a dict: topic_id -> {name, subject, difficulty, scores: [list of 50 floats]}
    """
    with driver.session() as session:
        topics = {}
        results = session.run("""
            MATCH (s:Student)-[r:SCORED]->(t:Topic)
            RETURN t.id AS topic_id, t.name AS topic_name,
                   t.subject AS subject, t.difficulty AS difficulty,
                   collect(r.score) AS scores
            ORDER BY t.id
        """)
        for record in results:
            topics[record["topic_id"]] = {
                "name": record["topic_name"],
                "subject": record["subject"],
                "difficulty": record["difficulty"],
                "scores": record["scores"],
            }
    return topics


def select_topics_for_simulation(topics):
    """
    Pick the 5 hardest topics (lowest class average) and 5 easiest
    (highest class average) for simulation comparison.
    """
    topic_avgs = []
    for tid, data in topics.items():
        avg = np.mean(data["scores"])
        topic_avgs.append((tid, avg, data))

    topic_avgs.sort(key=lambda x: x[1])  # sort by average ascending

    hardest = [(tid, data) for tid, avg, data in topic_avgs[:NUM_TOPICS_PER_CATEGORY]]
    easiest = [(tid, data) for tid, avg, data in topic_avgs[-NUM_TOPICS_PER_CATEGORY:]]

    return hardest, easiest


# ===================================================================
# SECTION 2 — SIR MODEL
# ===================================================================

def classify_students(scores):
    """
    Given a list of scores for one topic, classify each student:
      - score >= INFORMED_THRESHOLD  -> Informed (I) — already knows the topic
      - score < SUSCEPTIBLE_THRESHOLD -> Susceptible (S) — needs to learn
      - in between -> also Susceptible (hasn't fully grasped it yet)

    Returns the initial S, I, R counts as fractions of total population.
    R starts at 0 because nobody has "mastered and moved on" yet.
    """
    n = len(scores)
    informed = sum(1 for s in scores if s >= INFORMED_THRESHOLD)
    susceptible = n - informed
    recovered = 0

    # Return as fractions (SIR model works with proportions, not counts)
    return susceptible / n, informed / n, recovered / n


def sir_equations(y, t, beta, gamma):
    """
    The SIR differential equations.

    y = [S, I, R] at time t
    beta = learning rate
    gamma = mastery rate

    Returns [dS/dt, dI/dt, dR/dt]

    This is the math from Chapter 3 Section 3.4:
      dS/dt = -β * S * I
      dI/dt =  β * S * I - γ * I
      dR/dt =  γ * I
    """
    S, I, R = y
    dSdt = -beta * S * I
    dIdt = beta * S * I - gamma * I
    dRdt = gamma * I
    return [dSdt, dIdt, dRdt]


def run_sir_simulation(S0, I0, R0, beta=BETA, gamma=GAMMA):
    """
    Run the SIR model for one topic.

    Inputs:
      S0, I0, R0 = initial fractions of susceptible, informed, recovered
      beta, gamma = model parameters

    Returns:
      t = array of time points
      S, I, R = arrays of S/I/R values at each time point
    """
    t = np.linspace(0, TIME_DAYS, TIME_POINTS)
    y0 = [S0, I0, R0]

    # odeint = SciPy's ordinary differential equation integrator
    # It takes the equations, initial conditions, and time points,
    # then computes the solution at each time point
    solution = odeint(sir_equations, y0, t, args=(beta, gamma))

    S = solution[:, 0]
    I = solution[:, 1]
    R = solution[:, 2]

    return t, S, I, R


# ===================================================================
# SECTION 3 — ANALYSIS
# ===================================================================

def analyse_simulation(t, S, I, R):
    """
    Extract key metrics from one simulation run:
      - peak_informed: maximum fraction of students learning at once
      - peak_day: when the peak occurs
      - mastery_50_day: when 50% of students have mastered the topic
      - mastery_90_day: when 90% have mastered it
      - final_mastered: fraction mastered at the end of the simulation
    """
    peak_informed = float(np.max(I))
    peak_day = float(t[np.argmax(I)])

    # Find when R crosses 0.5 and 0.9
    mastery_50_day = None
    mastery_90_day = None
    for i in range(len(t)):
        if R[i] >= 0.5 and mastery_50_day is None:
            mastery_50_day = float(t[i])
        if R[i] >= 0.9 and mastery_90_day is None:
            mastery_90_day = float(t[i])

    return {
        "peak_informed_fraction": round(peak_informed, 3),
        "peak_day": round(peak_day, 1),
        "mastery_50_percent_day": round(mastery_50_day, 1) if mastery_50_day else "not reached",
        "mastery_90_percent_day": round(mastery_90_day, 1) if mastery_90_day else "not reached",
        "final_mastered_fraction": round(float(R[-1]), 3),
    }


# ===================================================================
# SECTION 4 — CHARTS
# ===================================================================

def chart_single_topic(t, S, I, R, topic_name, filename):
    """
    Classic SIR curve for a single topic.
    Three lines: S (blue), I (orange), R (green).
    """
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.plot(t, S, label="S (Need to learn)", color="#3498db", linewidth=2)
    ax.plot(t, I, label="I (Currently learning)", color="#e67e22", linewidth=2)
    ax.plot(t, R, label="R (Mastered)", color="#2ecc71", linewidth=2)

    ax.set_xlabel("Days of Peer Learning")
    ax.set_ylabel("Fraction of Students")
    ax.set_title(f"Knowledge Diffusion: {topic_name}")
    ax.legend(fontsize=11)
    ax.set_ylim(0, 1)
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(filename, dpi=150)
    plt.close()


def chart_comparison(simulation_results, filename, title):
    """
    Compare how fast knowledge spreads across multiple topics.
    Shows the R (mastered) curve for each topic on the same chart.
    """
    fig, ax = plt.subplots(figsize=(12, 6))

    colors = plt.cm.viridis(np.linspace(0, 0.9, len(simulation_results)))
    for i, result in enumerate(simulation_results):
        ax.plot(result["t"], result["R"],
                label=f"{result['topic_name'][:25]}",
                color=colors[i], linewidth=2)

    ax.set_xlabel("Days of Peer Learning")
    ax.set_ylabel("Fraction of Students Who Mastered Topic")
    ax.set_title(title)
    ax.legend(fontsize=9, loc="lower right")
    ax.set_ylim(0, 1)
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(filename, dpi=150)
    plt.close()


def chart_beta_sensitivity(topic_name, S0, I0, R0, filename):
    """
    Show how different learning rates (β) affect knowledge spread.
    This answers: "what if students interact more/less frequently?"
    """
    fig, ax = plt.subplots(figsize=(10, 6))
    beta_values = [0.1, 0.2, 0.3, 0.5, 0.8]
    colors = ["#e74c3c", "#e67e22", "#2ecc71", "#3498db", "#9b59b6"]

    for beta, color in zip(beta_values, colors):
        t, S, I, R = run_sir_simulation(S0, I0, R0, beta=beta, gamma=GAMMA)
        ax.plot(t, R, label=f"β = {beta}", color=color, linewidth=2)

    ax.set_xlabel("Days of Peer Learning")
    ax.set_ylabel("Fraction of Students Who Mastered Topic")
    ax.set_title(f"Effect of Learning Rate (β) on Knowledge Diffusion\nTopic: {topic_name}")
    ax.legend(fontsize=11)
    ax.set_ylim(0, 1)
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(filename, dpi=150)
    plt.close()


# ===================================================================
# SECTION 5 — PRINT SUMMARY
# ===================================================================

def print_summary(report):
    print("\n" + "=" * 70)
    print("SIR KNOWLEDGE DIFFUSION SIMULATION REPORT")
    print("=" * 70)
    print(f"Parameters: β (learning rate) = {report['parameters']['beta']}, "
          f"γ (mastery rate) = {report['parameters']['gamma']}")
    print(f"Simulation period: {report['parameters']['time_days']} days")

    print(f"\nHardest topics (slowest knowledge spread):")
    print(f"  {'Topic':<35} {'Initial S':<10} {'Initial I':<10} "
          f"{'Peak Day':<10} {'50% Day':<10} {'Final R'}")
    for result in report["hardest_topics"]:
        print(f"  {result['topic_name'][:33]:<35} "
              f"{result['initial_S']:<10} {result['initial_I']:<10} "
              f"{result['metrics']['peak_day']:<10} "
              f"{str(result['metrics']['mastery_50_percent_day']):<10} "
              f"{result['metrics']['final_mastered_fraction']}")

    print(f"\nEasiest topics (fastest knowledge spread):")
    print(f"  {'Topic':<35} {'Initial S':<10} {'Initial I':<10} "
          f"{'Peak Day':<10} {'50% Day':<10} {'Final R'}")
    for result in report["easiest_topics"]:
        print(f"  {result['topic_name'][:33]:<35} "
              f"{result['initial_S']:<10} {result['initial_I']:<10} "
              f"{result['metrics']['peak_day']:<10} "
              f"{str(result['metrics']['mastery_50_percent_day']):<10} "
              f"{result['metrics']['final_mastered_fraction']}")

    print("=" * 70 + "\n")


# ===================================================================
# MAIN
# ===================================================================

def main():
    print("Connecting to Neo4j ...")
    driver.verify_connectivity()
    print("  Connected.\n")

    print("Loading topic scores ...")
    topics = load_topic_scores()
    print(f"  Loaded {len(topics)} topics\n")

    print("Selecting topics for simulation ...")
    hardest, easiest = select_topics_for_simulation(topics)
    print(f"  Selected {len(hardest)} hardest and {len(easiest)} easiest topics\n")

    # Run simulations for hardest topics
    print("Simulating knowledge diffusion for HARDEST topics ...")
    hardest_results = []
    for tid, data in hardest:
        S0, I0, R0 = classify_students(data["scores"])
        t, S, I, R = run_sir_simulation(S0, I0, R0)
        metrics = analyse_simulation(t, S, I, R)

        # Save individual SIR chart for the single hardest topic
        if len(hardest_results) == 0:
            chart_single_topic(t, S, I, R, data["name"],
                             "chart_sir_hardest_topic.png")
            print(f"  Saved chart_sir_hardest_topic.png")

        hardest_results.append({
            "topic_id": tid,
            "topic_name": data["name"],
            "subject": data["subject"],
            "difficulty": data["difficulty"],
            "initial_S": round(S0, 3),
            "initial_I": round(I0, 3),
            "initial_R": round(R0, 3),
            "metrics": metrics,
            "t": t.tolist(),
            "S": S.tolist(),
            "I": I.tolist(),
            "R": R.tolist(),
        })
        print(f"  {data['name']}: S0={S0:.2f}, I0={I0:.2f} -> "
              f"final mastery {metrics['final_mastered_fraction']}")

    # Run simulations for easiest topics
    print("\nSimulating knowledge diffusion for EASIEST topics ...")
    easiest_results = []
    for tid, data in easiest:
        S0, I0, R0 = classify_students(data["scores"])
        t, S, I, R = run_sir_simulation(S0, I0, R0)
        metrics = analyse_simulation(t, S, I, R)

        if len(easiest_results) == 0:
            chart_single_topic(t, S, I, R, data["name"],
                             "chart_sir_easiest_topic.png")
            print(f"  Saved chart_sir_easiest_topic.png")

        easiest_results.append({
            "topic_id": tid,
            "topic_name": data["name"],
            "subject": data["subject"],
            "difficulty": data["difficulty"],
            "initial_S": round(S0, 3),
            "initial_I": round(I0, 3),
            "initial_R": round(R0, 3),
            "metrics": metrics,
            "t": t.tolist(),
            "S": S.tolist(),
            "I": I.tolist(),
            "R": R.tolist(),
        })
        print(f"  {data['name']}: S0={S0:.2f}, I0={I0:.2f} -> "
              f"final mastery {metrics['final_mastered_fraction']}")

    # Comparison charts
    print("\nBuilding comparison charts ...")
    chart_comparison(hardest_results,
                    "chart_sir_hardest_comparison.png",
                    "Knowledge Diffusion: 5 Hardest Topics")
    print("  Saved chart_sir_hardest_comparison.png")

    chart_comparison(easiest_results,
                    "chart_sir_easiest_comparison.png",
                    "Knowledge Diffusion: 5 Easiest Topics")
    print("  Saved chart_sir_easiest_comparison.png")

    # Beta sensitivity chart (using the single hardest topic)
    hardest_tid, hardest_data = hardest[0]
    S0, I0, R0 = classify_students(hardest_data["scores"])
    chart_beta_sensitivity(hardest_data["name"], S0, I0, R0,
                          "chart_sir_beta_sensitivity.png")
    print("  Saved chart_sir_beta_sensitivity.png")

    # Build report (remove the raw t/S/I/R arrays for the JSON — too large)
    report_hardest = [{k: v for k, v in r.items() if k not in ["t", "S", "I", "R"]}
                      for r in hardest_results]
    report_easiest = [{k: v for k, v in r.items() if k not in ["t", "S", "I", "R"]}
                      for r in easiest_results]

    report = {
        "parameters": {
            "beta": BETA,
            "gamma": GAMMA,
            "time_days": TIME_DAYS,
            "informed_threshold": INFORMED_THRESHOLD,
            "susceptible_threshold": SUSCEPTIBLE_THRESHOLD,
        },
        "hardest_topics": report_hardest,
        "easiest_topics": report_easiest,
    }

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
    print(f"\n  Saved {OUTPUT_FILE}")

    print_summary(report)

    driver.close()
    print("All done. Charts saved:")
    print("  - chart_sir_hardest_topic.png      (single topic SIR curve)")
    print("  - chart_sir_easiest_topic.png      (single topic SIR curve)")
    print("  - chart_sir_hardest_comparison.png  (5 hardest topics compared)")
    print("  - chart_sir_easiest_comparison.png  (5 easiest topics compared)")
    print("  - chart_sir_beta_sensitivity.png    (effect of learning rate)\n")


if __name__ == "__main__":
    main()