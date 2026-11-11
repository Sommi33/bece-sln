# Samuel's Module — AI Clustering and Peer Group Formation

**Objective 4 of the project:** "Design and evaluate a graph-based social learning network that forms efficient peer study groups among JSS3 students to improve knowledge sharing and learning outcomes."

---

## What this module does (in plain English)

You take all 50 students and their scores across 80 topics, and you **form 10 study groups of 5 students each**. The goal is NOT to group similar students together — the goal is the opposite. You want every group to contain a **balanced mix** of students, so that for every topic:

- At least one student in the group is strong (can tutor others)
- Students who struggle in that topic have peers who can help them

This is the module that makes the system *useful*. Without it, the whole project is just analytics. With it, a teacher can look at the output and say "Group 3: put STU007, STU019, STU024, STU041, STU048 together — they complement each other well."

---

## Where your output fits in the bigger picture

- **Your output IS the final product** the teacher dashboard displays
- Your groups are based on **Chisom's complementarity analysis** and **Adebayo's topic failure data**
- The React dashboard shows your recommended groups as the main screen

So your module is the **delivery layer** — where all the other modules' work converges into a concrete recommendation.

---

## What your final output looks like

### `peer_groups.json`
```json
{
  "algorithm": "KMeans with complementarity-balanced grouping",
  "num_groups": 10,
  "group_size": 5,
  "groups": [
    {
      "group_id": "GRP01",
      "members": ["STU003", "STU011", "STU027", "STU035", "STU044"],
      "average_score": 0.54,
      "strongest_subjects": ["Mathematics", "English Studies"],
      "weakest_subjects": ["Basic Science and Technology"],
      "complementarity_score": 0.72
    },
    ...
  ],
  "quality_metrics": {
    "average_complementarity": 0.68,
    "average_score_range_per_group": 0.35,
    "vs_random_baseline": "+42%"
  }
}
```

### `chart_group_composition.png`
A visualisation showing each group's internal balance across subjects — the teacher can see at a glance how each group is structured.

---

## The concept — why clustering is the right approach

Think of each student as a **point in 80-dimensional space** (one dimension per topic, where the value is their score on that topic). Students with similar scores are "close" in this space; students with different strengths are "far apart."

Traditional clustering (K-Means) groups **similar** students together. But we want the **opposite** — groups of diverse students. So we use clustering in a clever way:

1. First, K-Means finds 5 "archetypes" — the 5 distinct learning profiles in the class
2. Then, we build groups by picking ONE student from each archetype
3. Result: every group has 5 students with different strengths

This is called **stratified sampling based on clusters**. It's a standard technique in machine learning, and it's surprisingly simple to implement with scikit-learn.

---

## How to get started

### Step 1 — Make sure SETUP.md is done

Before anything else, finish every step in `SETUP.md`. You must be able to run `python load_to_neo4j.py` and see "KNOWLEDGE GRAPH SUCCESSFULLY BUILT". If not, message Chisom first.

### Step 2 — Pull the latest code

In Command Prompt, inside the `bece-sln` folder:

```
git pull
```

You should see a new file called `ai_clustering.py` — this is your starter file.

### Step 3 — Install scikit-learn and matplotlib

```
python -m pip install scikit-learn matplotlib
```

### Step 4 — Open `ai_clustering.py` in VS Code

Read it top to bottom first. The code is about 75% written. You fill in 6 TODOs, each with clear hints.

### Step 5 — Run it as you go

```
python ai_clustering.py
```

After each TODO, run the script. If something's wrong, you'll see a clear error message telling you which TODO is unfinished.

---

## How to know when you're done

Your module is complete when:

- ✅ Running `python ai_clustering.py` completes without errors
- ✅ `peer_groups.json` exists with 10 groups of 5 students each
- ✅ `chart_group_composition.png` is saved
- ✅ The terminal prints a summary showing all 10 groups

---

## How to submit your work

```
git pull --rebase
git add ai_clustering.py peer_groups.json chart_group_composition.png
git commit -m "AI clustering and peer group formation complete"
git push
```

Then message Chisom in the group.

---

## Timeline

Aim for **5-7 days** from when you start. This is the 2nd hardest module — the code is scaffolded, but the concepts take a bit of thinking to grok. That's fine, take your time to understand it.

---

## Getting stuck

**First 20 minutes:** try to figure it out yourself — read the error, re-read the TODO, check the hints.

**If still stuck:** screenshot the error and send to Chisom. He has context on the whole system and can help faster than you expect.

---

Don't be intimidated by "AI clustering" — scikit-learn does the heavy lifting. You're mostly writing glue code. Go read the file. 🚀
