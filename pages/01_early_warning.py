import json
from pathlib import Path

import pandas as pd
import streamlit as st

from core.database import get_connection, init_db
from services.prediction import assess_academic_risk


ROOT = Path(__file__).resolve().parent.parent
METRICS_PATH = (
    ROOT / "models" / "early_warning_metrics.json"
)

init_db()

st.title("Academic Warning")
st.caption("Learning Support | Owner: Huang")

st.write(
    "Uses academic performance, assignment submissions, and platform activity up to day 60 of the course "
    "to support the manual identification of students who may require further attention."
)


def save_alert(student_ref, inputs, result):
    connection = get_connection()

    try:
        with connection:
            connection.execute(
                """
                INSERT INTO academic_alerts (
                    student_ref,
                    attendance_rate,
                    avg_score,
                    submission_rate,
                    total_clicks,
                    active_days,
                    quiz_clicks,
                    model_probability,
                    attendance_penalty,
                    risk_score,
                    risk_band,
                    recommendation
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    student_ref,
                    inputs["attendance_rate"],
                    inputs["avg_score"],
                    inputs["submission_rate"],
                    inputs["total_clicks"],
                    inputs["active_days"],
                    inputs["quiz_clicks"],
                    result["model_probability"],
                    result["attendance_penalty"],
                    result["risk_score"],
                    result["risk_band"],
                    result["recommendation"],
                ),
            )
    finally:
        connection.close()


def load_recent_alerts():
    connection = get_connection()

    try:
        return pd.read_sql_query(
            """
            SELECT
                student_ref,
                model_probability,
                risk_score,
                risk_band,
                created_at
            FROM academic_alerts
            ORDER BY id DESC
            LIMIT 12
            """,
            connection,
        )
    finally:
        connection.close()


with st.form("early_warning_form"):
    student_ref = st.text_input(
        "Student ID",
        value="GCU-DEMO-01",
        max_chars=40,
    )

    col1, col2 = st.columns(2)

    with col1:
        attendance_rate = st.number_input(
            "Attendance rate (%)",
            min_value=0.0,
            max_value=100.0,
            value=82.0,
            step=1.0,
        )

        avg_score = st.number_input(
            "Average assignment score (%)",
            min_value=0.0,
            max_value=100.0,
            value=58.0,
            step=0.1,
        )

        submission_rate = st.number_input(
            "Assignment submission rate (0-1)",
            min_value=0.0,
            max_value=1.0,
            value=0.75,
            step=0.01,
        )

    with col2:
        total_clicks = st.number_input(
            "Total learning platform clicks",
            min_value=0,
            max_value=100000,
            value=820,
            step=1,
        )

        active_days = st.number_input(
            "Active days on the learning platform",
            min_value=0,
            max_value=61,
            value=28,
            step=1,
        )

        quiz_clicks = st.number_input(
            "Quiz clicks",
            min_value=0,
            max_value=10000,
            value=96,
            step=1,
        )

    submitted = st.form_submit_button("Start Academic Risk Assessment")

if submitted:
    if len(student_ref.strip()) < 3:
        st.error("The ID must contain at least 3 characters.")
    else:
        try:
            inputs = {
                "attendance_rate": float(attendance_rate),
                "avg_score": float(avg_score),
                "submission_rate": float(submission_rate),
                "total_clicks": int(total_clicks),
                "active_days": int(active_days),
                "quiz_clicks": int(quiz_clicks),
            }

            result = assess_academic_risk(**inputs)
            save_alert(
                student_ref.strip(),
                inputs,
                result,
            )

            st.session_state["latest_warning_result"] = (
                result
            )

        except FileNotFoundError as error:
            st.error(str(error))
        except Exception as error:
            st.error(f"Assessment failed: {error}")

if "latest_warning_result" in st.session_state:
    result = st.session_state["latest_warning_result"]

    st.divider()
    st.subheader("Current Assessment Results")

    col1, col2, col3 = st.columns(3)

    col1.metric(
        "Model Risk Probability",
        f"{result['model_probability']:.1%}",
    )

    col2.metric(
        "Attendance Rule Adjustment",
        f"+{result['attendance_penalty']:.1%}",
    )

    col3.metric(
        "Overall Risk Score",
        f"{result['risk_score']:.1%}",
    )

    band_names = {
        "low": "Low Risk",
        "medium": "Medium Risk",
        "high": "High Risk",
    }

    band_text = band_names[result["risk_band"]]

    if result["risk_band"] == "high":
        st.error(f"Risk Level: {band_text}")
    elif result["risk_band"] == "medium":
        st.warning(f"Risk Level: {band_text}")
    else:
        st.success(f"Risk Level: {band_text}")

    st.write("**Recommended Actions:**")
    st.write(result["recommendation"])

    st.write("**Risk Explanation:**")
    for factor in result["factors"]:
        st.write(f"- {factor}")

st.divider()
st.subheader("Model Test Information")

if METRICS_PATH.exists():
    with open(
        METRICS_PATH,
        "r",
        encoding="utf-8",
    ) as file:
        metrics = json.load(file)

    col1, col2, col3, col4 = st.columns(4)

    col1.metric(
        "ROC-AUC",
        f"{metrics['roc_auc']:.4f}",
    )
    col2.metric(
        "Accuracy",
        f"{metrics['accuracy']:.4f}",
    )
    col3.metric(
        "Recall",
        f"{metrics['recall']:.4f}",
    )
    col4.metric(
        "Number of Test Records",
        metrics["test_samples"],
    )

    st.caption(
        "The metrics above describe only the OULAD test set."

    )
else:
    st.info("Test metrics will appear here after the model is trained.")

st.warning(
    "OULAD does not contain an attendance rate field. Attendance rate is used as an additional rule-based adjustment."

)

st.divider()
st.subheader("Recent Anonymized Assessment Records")

alerts = load_recent_alerts()

if alerts.empty:
    st.info("Records will appear here after an assessment is completed.")
else:
    alerts = alerts.rename(
        columns={
            "student_ref": "ID",
            "model_probability": "Model Probability",
            "risk_score": "Overall Risk",
            "risk_band": "Risk Level",
            "created_at": "Created At",
        }
    )

    alerts["Model Probability"] = alerts["Model Probability"].map(
        lambda value: f"{value:.1%}"
    )
    alerts["Overall Risk"] = alerts["Overall Risk"].map(
        lambda value: f"{value:.1%}"
    )
    alerts["Risk Level"] = alerts["Risk Level"].map(
        {
            "low": "Low Risk",
            "medium": "Medium Risk",
            "high": "High Risk",
        }
    )

    st.dataframe(
        alerts,
        use_container_width=True,
        hide_index=True,
    )

st.caption(
    "Data Source: Open University Learning Analytics Dataset, "
    "Kuzilek, Hlosta, and Zdrahal, CC BY 4.0."
)