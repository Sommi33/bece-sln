# BECE-SLN — Teammate Setup Guide

Hey team 👋

This guide walks you through setting up your laptop so you can work on the project. Follow every step in order. It takes about **45 minutes** total if nothing goes wrong.

If you get stuck at any point, **screenshot the error and send it to Chisom** — don't spend more than 15 minutes on one error alone.

---

## What you need

- A Windows laptop
- Stable internet
- Admin access to install software (most personal laptops have this by default)

---

## Step 1 — Install Python (10 min)

Python is the programming language we're using for the backend.

1. Go to **https://www.python.org/downloads/**
2. Click the big yellow **"Download Python 3.14.x"** button (or whatever the latest version is shown)
3. Open the downloaded `.exe` file from your Downloads folder
4. **CRITICAL:** On the first screen of the installer, tick ✅ **"Add python.exe to PATH"** at the bottom. This is the #1 mistake people make — don't skip it.
5. Click **"Install Now"**
6. Wait until you see "Setup was successful"
7. Close the installer

**Verify it worked:**

1. Press Windows key, type `cmd`, press Enter (this opens Command Prompt)
2. Type:
   ```
   python --version
   ```
3. You should see something like `Python 3.14.4`

If you see "not recognized" → you didn't tick the PATH box. Uninstall Python from Control Panel and reinstall, making sure to tick the box this time.

---

## Step 2 — Install VS Code (3 min)

VS Code is the editor where you'll write code.

1. Go to **https://code.visualstudio.com**
2. Click **"Download for Windows"**
3. Run the downloaded installer
4. Click **Next** through every screen using defaults
5. Click **Install**, then **Finish**

---

## Step 3 — Install the Python extension in VS Code (1 min)

1. Open VS Code
2. On the left sidebar, click the **Extensions icon** (four squares, or press `Ctrl+Shift+X`)
3. In the search box, type **"Python"**
4. Install the one published by **Microsoft** (blue verified badge, first result)

---

## Step 4 — Install Git (5 min)

Git is the tool that connects your laptop to GitHub.

1. Go to **https://git-scm.com/download/win**
2. The installer auto-downloads — run it from your Downloads folder
3. Click **Next** through every screen using defaults — don't customise anything
4. When you see **"Adjusting your PATH environment,"** make sure **"Git from the command line and also from 3rd-party software"** is selected (it's the default middle option)
5. Finish installation

**Verify:**

1. **Close all open Command Prompt windows** (important — PATH updates don't apply to already-open terminals)
2. Open a fresh Command Prompt
3. Type:
   ```
   git --version
   ```
4. You should see something like `git version 2.47.x`

---

## Step 5 — Configure Git with your identity (1 min)

So your commits show up under your name, not "Anonymous":

```
git config --global user.name "Your Full Name"
```

```
git config --global user.email "your_github_email@example.com"
```

Use the **same email you signed up to GitHub with**. Replace "Your Full Name" with your actual name.

---

## Step 6 — Accept the GitHub invite (1 min)

1. Check your email inbox for an email from GitHub titled something like **"Chisom Ihedoro invited you to collaborate on Sommi33/bece-sln"**
2. Click the link, log into GitHub, and click **"Accept invitation"**
3. You should now see the repository at **https://github.com/Sommi33/bece-sln**

---

## Step 7 — Clone the project (3 min)

"Cloning" means downloading the project from GitHub to your laptop.

1. Choose where you want to keep the project — I recommend your **Documents** folder
2. Open Command Prompt (Windows key → `cmd` → Enter)
3. Navigate to Documents:
   ```
   cd Documents
   ```
4. Clone the repo:
   ```
   git clone https://github.com/Sommi33/bece-sln.git
   ```
5. A browser window may open asking you to log into GitHub — do it
6. The project downloads into a new folder called `bece-sln`

**Navigate into the folder:**
```
cd bece-sln
```

You're now inside the project folder.

---

## Step 8 — Install Python libraries (2 min)

We need four libraries: neo4j, pandas, numpy, python-dotenv.

In Command Prompt (still inside the `bece-sln` folder):

```
python -m pip install neo4j pandas numpy python-dotenv
```

If you see a Device Guard error or similar, try:

```
python -m pip install --user neo4j pandas numpy python-dotenv
```

Wait for "Successfully installed ..." to appear.

---

## Step 9 — Create your `.env` file (2 min)

This file holds the database password. Chisom will send you the credentials **privately** (via WhatsApp) — do NOT post them in the group or commit them to GitHub.

1. Open VS Code
2. **File → Open Folder** → navigate to `Documents\bece-sln` → click **Select Folder**
3. In VS Code: **File → New File** (`Ctrl+N`)
4. Save (`Ctrl+S`) with the exact name **`.env`** (with the dot at the start, no extension)
5. Paste this content and replace the placeholders with what Chisom sends you:

```
NEO4J_URI=neo4j+s://xxxxxxxx.databases.neo4j.io
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=paste_the_password_here
```

6. Save (`Ctrl+S`)

**Rules:**
- No spaces around the `=` sign
- No quotes around the values
- Do NOT commit this file — the `.gitignore` handles this automatically, but don't force it

---

## Step 10 — Verify everything works (1 min)

Let's confirm you can connect to the database.

In VS Code, press `` Ctrl+` `` (Ctrl + backtick) to open a terminal inside VS Code. It opens inside the project folder.

Run the loader script:

```
python load_to_neo4j.py
```

If everything is set up correctly, you'll see output ending with:

```
============================================================
KNOWLEDGE GRAPH SUCCESSFULLY BUILT
============================================================
```

**If you see "KNOWLEDGE GRAPH SUCCESSFULLY BUILT" → your setup is complete!** 🎉

If you see an error, screenshot it and send to Chisom.

---

## What happens next

Once your setup is verified, Chisom will send you your **module starter pack**. This contains:

- A Python file with skeleton code you fill in
- A clear explanation of what your module does
- A test script that checks if your code is working

You'll work on your module inside the `bece-sln` folder, commit your changes with Git, and push them to GitHub so everyone can see progress.

---

## Quick Git reference (for later)

When you finish some work and want to save it to GitHub:

```
git add .
git commit -m "short description of what you changed"
git push
```

When you want to pull the latest work from the team:

```
git pull
```

That's basically it for Git in this project.

---

## Need help?

WhatsApp Chisom with a screenshot of the error. Please include:
- What command you ran
- The exact error message
- What step of this guide you were on

Don't suffer in silence — everyone hits issues at first.

Welcome to the project. Let's build something good. 🚀
