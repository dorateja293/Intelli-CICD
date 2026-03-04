import os
from flask import Flask, jsonify, request
import joblib
import pandas as pd

app = Flask(__name__)

# ============================
# LOAD ML MODEL
# ============================

MODEL_PATH = os.path.join("model", "intelli_ci_model.pkl")

try:
    model = joblib.load(MODEL_PATH)
except Exception as e:
    raise RuntimeError(f"Failed to load ML model: {str(e)}")


FEATURE_COLUMNS = [
    "files_changed",
    "lines_added",
    "lines_deleted",
    "code_churn",
    "commit_hour",
    "commit_day",
    "historical_failure_rate",
    "is_weekend",
    "large_commit_flag",
    "recent_failure_flag",
    "execution_time",
]

FEATURE_SET = set(FEATURE_COLUMNS)

DECISION_THRESHOLD = 0.4


# ============================
# VALIDATE INPUT
# ============================

def validate_payload(data):

    if not isinstance(data, dict):
        return "Payload must be JSON object"

    missing = [f for f in FEATURE_COLUMNS if f not in data]
    if missing:
        return f"Missing features: {missing}"

    extra = set(data.keys()) - FEATURE_SET
    if extra:
        return f"Unknown features: {extra}"

    return None


# ============================
# HEALTH CHECK
# ============================

@app.route("/")
def home():
    return jsonify({
        "service": "INTELLI-CI API",
        "status": "running"
    })


# ============================
# PREDICTION ENDPOINT
# ============================

@app.route("/predict", methods=["POST"])
def predict():

    try:

        if not request.is_json:
            return jsonify({"error": "Content-Type must be application/json"}), 415

        data = request.get_json(silent=True)

        if data is None:
            return jsonify({"error": "Invalid JSON payload"}), 400

        error = validate_payload(data)

        if error:
            return jsonify({"error": error}), 400

        features_df = pd.DataFrame([data], columns=FEATURE_COLUMNS)
        features_df = features_df.apply(pd.to_numeric, errors="raise")

        probability = model.predict_proba(features_df)[0][1]

        decision = (
            "RUN_FULL_TESTS"
            if probability > DECISION_THRESHOLD
            else "SKIP_TESTS"
        )

        return jsonify(
            {
                "failure_probability": float(probability),
                "decision": decision,
            }
        )

    except ValueError as e:
        return jsonify({"error": f"Invalid feature value: {str(e)}"}), 400

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ============================
# SERVER START
# ============================

if __name__ == "__main__":

    port = int(os.environ.get("PORT", 5000))

    app.run(
        host="0.0.0.0",
        port=port,
        debug=False
    )