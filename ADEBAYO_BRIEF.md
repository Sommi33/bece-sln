# Adebayo's Module — Topic Failure Analysis

**Objective 2 of the project:** "Analyze students' performance in BECE practice questions to determine the topics in which students fail most frequently."

---

## What this module does (in plain English)

You look at all 50 students' scores across all 80 topics, and you figure out:

1. **Which topics does the class fail the most?** — the "weakest" topics overall
2. **Which subjects have the lowest average scores?**
3. **How does difficulty (Easy/Medium/Hard) affect failure rates?**
4. **Which students are struggling the most overall?**

You produce:
- A **JSON report file** with all the numbers (`topic_failure_report.json`)
- Three **charts** saved as images (for Chapter 4 screenshots)
- A clear summary printed to the terminal

This module is the **evidence layer** for the whole project. Every other module uses your findings to justify its decisions. Your charts will go directly into Chapter 4 of the thesis.

---

## Where your output fits in the bigger picture

- **Complementarity analysis (Chisom's module)** uses your per-topic failure rates to identify which students can tutor which peers
- **Clustering (Samuel's module)** uses your per-student weak-topic lists to form balanced study groups
- **Chapter 4** uses your charts as Figures 4.1, 4.2, 4.3 — visual proof that the system identifies real learning gaps

So your work is the **foundation the other modules build on**. No pressure 🙂

---

## What your final output looks like

### `topic_failure_report.json`
```json
{
  "class_average": 0.543,
  "weakest_topics": [
    {
      "topic_id": "MTH17",
      "topic_name": "Algebraic Expressions",
      "subject": "Mathematics",
      "difficulty": "Hard",
      "class_average": 0.312,
      "students_below_threshold": 38
    },
    ...
  ],
  "weakest_subjects": [
    {
      "subject": "Mathematics",
      "average": 0.48,
      "hardest_topic": "Algebraic Expressions"
    },
    ...
  ],
  "difficulty_breakdown": {
    "Easy": 0.62,
    "Medium": 0.53,
    "Hard": 0.41
  },
  "struggling_students": [
    {"student_id": "STU003", "average": 0.32, "profile": "struggling"},
    ...
  ]
}
```

### 3 chart images (saved as PNG)
1. `chart_weakest_topics.png` — bar chart of the 10 weakest topics
2. `chart_subjects_avg.png` — bar chart of average scores per subject
3. `chart_difficulty_avg.png` — bar chart of Easy vs Medium vs Hard

---

## How to get started

### Step 1 — Make sure SETUP.md is done

Before anything else, finish every step in `SETUP.md`. You must be able to run `python load_to_neo4j.py` and see "KNOWLEDGE GRAPH SUCCESSFULLY BUILT". If not, message Chisom first.

### Step 2 — Pull the latest code

In Command Prompt, inside the `bece-sln` folder:

```
git pull
```

You should see a new file called `topic_failure_analysis.py` — this is your starter file.

### Step 3 — Install the charting library

```
python -m pip install matplotlib
```

### Step 4 — Open `topic_failure_analysis.py` in VS Code

Read through it top to bottom first. The code is 70% written — there are sections marked `# TODO:` where you fill in the logic. Each TODO has hints.

### Step 5 — Run it as you go

Don't wait until you finish everything. After each TODO, run:

```
python topic_failure_analysis.py
```

It will print what's working and what's not. When everything is done, you'll see all three charts saved as PNG files in your folder.

---

## How to know when you're done

Your module is complete when:

- ✅ Running `python topic_failure_analysis.py` completes without errors
- ✅ `topic_failure_report.json` exists in your folder and has real data
- ✅ Three PNG charts are saved
- ✅ The summary printed in the terminal matches what's in the JSON file

---

## How to submit your work

When you think it's done:

1. Commit your changes:
   ```
   git add topic_failure_analysis.py topic_failure_report.json
   git commit -m "Topic failure analysis complete"
   git push
   ```
2. Attach the three PNG charts in the WhatsApp group
3. Message Chisom that you're done so he can integrate

---

## Timeline

Aim for **4-5 days** from when you start. Most of that is understanding the code, not writing it. The actual writing is maybe 2 hours of focused work.

---

## Getting stuck

**First 15 minutes:** try to figure it out yourself — read the error, re-read the TODO, check the hints.

**If you're still stuck:** screenshot the error and send to Chisom. Don't suffer in silence. A 5-minute question from Chisom saves you 2 hours of frustration.

---

You got this. Go open `topic_failure_analysis.py` and start reading. 🚀
