# Semilore's Module — System Testing and Documentation

**Your role:** Verify the entire system works end-to-end and produce all the screenshots and documentation needed for Chapter 4 of the thesis.

---

## What this module does (in plain English)

You are the **quality assurance person**. Your job is to:

1. Run every module in the system from scratch
2. Confirm each one produces the correct output
3. Take screenshots of every dashboard page and Neo4j visualisation
4. Generate a test report that proves the system works

This is not "less important" work — it's what makes the difference between a project that looks finished and one that IS finished. Without your screenshots and test report, Chapter 4 has no figures, no evidence, and no proof.

---

## Where your output fits in the bigger picture

- **Chapter 4** uses your screenshots as Figures 4.1 through 4.12+
- **Defence day** — if the panel asks "does it actually work?" your test report is the answer
- **Your test script** runs all modules automatically and logs success/failure for each one

---

## How to get started

### Step 1 — Make sure SETUP.md is done

Before anything else, finish every step in `SETUP.md`. You must be able to run `python load_to_neo4j.py` and see "KNOWLEDGE GRAPH SUCCESSFULLY BUILT". If not, message Chisom first.

### Step 2 — Pull the latest code

```
git pull
```

### Step 3 — Install all required libraries

```
python -m pip install neo4j pandas numpy python-dotenv matplotlib scipy scikit-learn flask flask-cors
```

### Step 4 — Run the automated test script

```
python system_test.py
```

This script runs every module in the correct order and tells you if each one passed or failed. Follow the prompts.

### Step 5 — Take screenshots manually

After the test script finishes successfully, take the screenshots listed below. Save each one with the exact filename shown.

---

## Screenshots needed (save with these exact filenames)

### Dashboard screenshots
Start the API first: `python app.py` then open `http://localhost:5000` in Chrome.

1. **`screenshot_dashboard_overview.png`** — the Overview page (stat cards + charts + struggling students)
2. **`screenshot_dashboard_students.png`** — the Students page (full table)
3. **`screenshot_dashboard_student_detail.png`** — click on any student (e.g. STU001) to show their topic breakdown
4. **`screenshot_dashboard_topics.png`** — the Topics page (all 80 topics)
5. **`screenshot_dashboard_peer_pairs.png`** — the Peer Pairs page
6. **`screenshot_dashboard_study_groups.png`** — the Study Groups page (may say "waiting" if Samuel hasn't finished)
7. **`screenshot_dashboard_dependencies.png`** — the Dependencies page

### Neo4j screenshots
Go to your Neo4j Aura Query tab. Run each query and screenshot the graph visualisation.

8. **`screenshot_neo4j_full_graph.png`** — query: `MATCH (n) RETURN n LIMIT 100`
9. **`screenshot_neo4j_student_topics.png`** — query: `MATCH (s:Student {id: "STU001"})-[r:SCORED]->(t:Topic) RETURN s, r, t LIMIT 30`
10. **`screenshot_neo4j_complements.png`** — query: `MATCH (a:Student)-[r:COMPLEMENTS]-(b:Student) RETURN a, r, b`
11. **`screenshot_neo4j_depends_on.png`** — query: `MATCH (a:Topic)-[r:DEPENDS_ON]->(b:Topic) RETURN a, r, b`
12. **`screenshot_neo4j_subjects.png`** — query: `MATCH (t:Topic)-[r:BELONGS_TO]->(s:Subject) RETURN t, r, s`

### Chart screenshots (already generated as PNG files in the folder)
These should already exist after running the test script. Just confirm they're there:

13. `chart_complementarity_heatmap.png`
14. `chart_sir_hardest_topic.png`
15. `chart_sir_easiest_topic.png`
16. `chart_sir_beta_sensitivity.png`
17. `chart_topic_dependencies.png`
18. `chart_prediction_accuracy.png`

---

## How to take good screenshots

- **Use full screen** (press F11 in Chrome for fullscreen mode)
- **Make sure data is visible** — scroll if needed to show the important parts
- **Dark mode is fine** — that's how the dashboard looks
- **Save as PNG** — not JPG (higher quality)
- **Use Windows Snipping Tool** — press `Win+Shift+S`, drag to select area, paste into Paint, save as PNG

---

## How to know when you're done

- ✅ `system_test.py` ran with all modules passing
- ✅ `system_test_report.json` exists with all results
- ✅ All 12+ screenshots are saved in the `screenshots/` folder
- ✅ All chart PNGs exist in the main folder

---

## How to submit your work

```
git pull --rebase
git add system_test.py system_test_report.json
git commit -m "System testing complete - all modules verified"
git push
```

Then send screenshots to the WhatsApp group (they're too large for GitHub).

---

## Timeline

This should take **1-2 days**. Most of the time is waiting for scripts to run and taking screenshots carefully.

---

## Getting stuck

If any module fails during the test:
1. Screenshot the error
2. Send it to Chisom
3. Don't try to fix the code yourself — just report the error

Your job is to TEST, not to FIX. Finding problems is valuable work.

---

Welcome back to the project. Let's finish strong. 🚀
