import os
import sys
import psycopg2
import requests
from dotenv import load_dotenv
from github import Auth, Github

# ============================
# LOAD ENV VARIABLES
# ============================

load_dotenv()

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
REPO_NAME = os.getenv("REPO_NAME")

DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")

API_URL = os.getenv("PREDICT_API_URL", "https://intelli-cicd.onrender.com/predict")


def fail(message):
    print(f"ERROR: {message}")
    sys.exit(1)


required_env = {
    "GITHUB_TOKEN": GITHUB_TOKEN,
    "REPO_NAME": REPO_NAME,
    "DB_NAME": DB_NAME,
    "DB_USER": DB_USER,
    "DB_PASSWORD": DB_PASSWORD,
    "DB_HOST": DB_HOST,
    "DB_PORT": DB_PORT,
}

missing = [name for name, value in required_env.items() if not value]
if missing:
    fail(f"Missing required environment variable(s): {', '.join(missing)}")

# ============================
# CONNECT TO GITHUB
# ============================

try:
    auth = Auth.Token(GITHUB_TOKEN)
    github_client = Github(auth=auth)

    repo = github_client.get_repo(REPO_NAME)
    commits = repo.get_commits()

    # Check workflow status (optional info)
    try:
        workflow_runs = repo.get_workflow_runs()
        if workflow_runs.totalCount == 0:
            print("WARN: No GitHub Actions workflow runs found.")
        else:
            latest_run = workflow_runs[0]
            print("Latest Workflow Status:", latest_run.conclusion)
    except Exception:
        print("WARN: Unable to check workflow runs.")

    commit = commits[0]
    files = list(commit.files)

    files_changed = len(files)
    lines_added = sum(changed_file.additions for changed_file in files)
    lines_deleted = sum(changed_file.deletions for changed_file in files)

    code_churn = lines_added + lines_deleted

    commit_hour = commit.commit.author.date.hour
    commit_day = commit.commit.author.date.weekday()

    is_weekend = 1 if commit_day >= 5 else 0
    large_commit_flag = 1 if code_churn > 400 else 0

except IndexError:
    fail("This repository has no commits yet.")

except Exception as e:
    fail(f"GitHub Error: {str(e)}")


# ============================
# CALCULATE HISTORICAL FAILURE RATE
# FROM DATABASE
# ============================

try:
    conn = psycopg2.connect(
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST,
        port=DB_PORT,
    )

    cur = conn.cursor()

    cur.execute(
        """
        SELECT failure_probability
        FROM commit_history
        ORDER BY created_at DESC
        LIMIT 20
        """
    )

    rows = cur.fetchall()

    if len(rows) == 0:
        historical_failure_rate = 0
    else:
        probs = [r[0] for r in rows]
        historical_failure_rate = sum(probs) / len(probs)

    cur.close()
    conn.close()

except Exception as e:
    print("WARN: Could not compute historical failure rate:", e)
    historical_failure_rate = 0


# Placeholder for future logic
recent_failure_flag = 0
execution_time = 15

print("\n========= INTELLI-CI ANALYSIS =========")
print("Repository:", REPO_NAME)
print("Commit SHA:", commit.sha)
print("Files Changed:", files_changed)
print("Code Churn:", code_churn)
print("Historical Failure Rate:", round(historical_failure_rate, 3))
print("----------------------------------------")


# ============================
# CALL ML API
# ============================

payload = {
    "files_changed": files_changed,
    "lines_added": lines_added,
    "lines_deleted": lines_deleted,
    "code_churn": code_churn,
    "commit_hour": commit_hour,
    "commit_day": commit_day,
    "historical_failure_rate": historical_failure_rate,
    "is_weekend": is_weekend,
    "large_commit_flag": large_commit_flag,
    "recent_failure_flag": recent_failure_flag,
    "execution_time": execution_time,
}

try:
    response = requests.post(API_URL, json=payload, timeout=10)
    response.raise_for_status()

    ml_result = response.json()

    if "failure_probability" not in ml_result or "decision" not in ml_result:
        fail(f"Unexpected API response: {ml_result}")

    print("ML Decision:", ml_result)
    print("========================================\n")

except Exception as e:
    fail(f"API Error: {str(e)}")


# ============================
# STORE RESULT IN DATABASE
# ============================

try:
    conn = psycopg2.connect(
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST,
        port=DB_PORT,
    )

    cur = conn.cursor()

    cur.execute(
        """
        INSERT INTO commit_history
        (commit_sha, files_changed, code_churn, historical_failure_rate,
         failure_probability, decision)
        VALUES (%s, %s, %s, %s, %s, %s)
        ON CONFLICT (commit_sha) DO UPDATE
        SET files_changed = EXCLUDED.files_changed,
            code_churn = EXCLUDED.code_churn,
            historical_failure_rate = EXCLUDED.historical_failure_rate,
            failure_probability = EXCLUDED.failure_probability,
            decision = EXCLUDED.decision,
            created_at = NOW()
        """,
        (
            commit.sha,
            files_changed,
            code_churn,
            historical_failure_rate,
            ml_result["failure_probability"],
            ml_result["decision"],
        ),
    )

    conn.commit()

    cur.close()
    conn.close()

    print("Commit data stored successfully in PostgreSQL.\n")

except Exception as e:
    fail(f"Database Error: {str(e)}")
