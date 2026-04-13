# BECE Social Learning Network (BECE-SLN)

**Using Graph Analytics to Optimize Peer Learning and Knowledge Diffusion in BECE Preparation**

A final year Information Technology project at Redeemer's University, Ede, Nigeria.

---

## Overview

This project develops a Social Learning Network (SLN) system that uses graph analytics, complementarity analysis, SIR-model knowledge diffusion simulation, and AI clustering to optimise peer study group formation among JSS3 students preparing for the Basic Education Certificate Examination (BECE).

Instead of forming study groups randomly, the system analyses each student's topic-level performance, identifies complementary strengths and weaknesses, and recommends peer groups that maximise knowledge exchange.

## Objectives

1. Classify BECE past questions according to topic and difficulty level
2. Analyse student performance to identify frequently-failed topics
3. Develop a predictive model for topic-to-topic learning dependencies
4. Design and evaluate a graph-based peer learning network

## System Architecture

- **Database:** Neo4j AuraDB (graph database)
- **Backend:** Python 3.14 (NetworkX, SciPy, scikit-learn)
- **Frontend:** React (teacher dashboard + student portal) — *coming soon*

## Graph Structure

- **50 Student nodes** (synthetic JSS3 students)
- **80 Topic nodes** (classified BECE topics across 9 subjects)
- **9 Subject nodes** (Mathematics, Basic Science & Technology, English Studies, Business Studies, National Value Education, Cultural & Creative Arts, Pre-Vocational Studies, History, Christian Religious Studies)
- **4,000 SCORED relationships** (weighted student–topic performance)
- **80 BELONGS_TO relationships** (topic–subject grouping)

## Getting Started

### Prerequisites

- Python 3.14+ installed with "Add to PATH" enabled
- A Neo4j AuraDB Free instance (see https://neo4j.com/cloud/aura-free/)
- VS Code or any code editor

### Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/Sommi33/bece-sln.git
   cd bece-sln
   ```

2. Install Python dependencies:
   ```bash
   python -m pip install neo4j pandas numpy python-dotenv
   ```

3. Create a `.env` file in the project root with your Neo4j credentials:
   ```
   NEO4J_URI=neo4j+s://<your-instance-id>.databases.neo4j.io
   NEO4J_USERNAME=<your-username>
   NEO4J_PASSWORD=<your-password>
   ```

4. Generate synthetic student data:
   ```bash
   python generate_students.py
   ```

5. Load everything into Neo4j:
   ```bash
   python load_to_neo4j.py
   ```

## Project Structure

```
bece-sln/
├── topics.json              # 80 classified BECE topics
├── generate_students.py     # Synthetic student data generator
├── load_to_neo4j.py         # Knowledge graph loader
├── .env                     # Neo4j credentials (gitignored)
└── README.md
```

## Team

- **Chisom Ihedoro** — Knowledge Graph, Complementarity Analysis, SIR Simulation
- **Samuel** — AI Clustering & Peer Group Formation
- **Semilore** — Predictive Model for Topic Dependencies
- **Adebayo** — Topic Failure Analysis

**Supervisor:** Dr. T. V. Igbe

**Department:** Information Technology, Redeemer's University, Ede

## License

Academic project — not for commercial use.
