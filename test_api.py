import requests
import os

url = os.getenv("PREDICT_API_URL", "https://intelli-cicd.onrender.com/predict")

data = {
    "files_changed": 2,
    "lines_added": 25,
    "lines_deleted": 5,
    "code_churn": 30,
    "commit_hour": 14,
    "commit_day": 2,
    "historical_failure_rate": 0.1,
    "is_weekend": 0,
    "large_commit_flag": 0,
    "recent_failure_flag": 0,
    "execution_time": 15
}

response = requests.post(url, json=data, timeout=10)
response.raise_for_status()

print(response.json())
