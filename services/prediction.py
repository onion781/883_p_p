from functools import lru_cache
from pathlib import Path

import joblib
import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parent.parent
MODEL_PATH = ROOT / "models" / "early_warning.joblib"


@lru_cache(maxsize=1)
def load_model():
    if not MODEL_PATH.exists():
        raise FileNotFoundError(
            "Model not found. Run: "
            "python scripts/train_early_warning.py"
        )

    artifact = joblib.load(MODEL_PATH)
    return artifact["pipeline"]


def assess_academic_risk(
    attendance_rate,
    avg_score,
    submission_rate,
    total_clicks,
    active_days,
    quiz_clicks,
):
    features = pd.DataFrame(
        [
            {
                "avg_score": avg_score,
                "submission_rate": submission_rate,
                "log_total_clicks": np.log1p(total_clicks),
                "active_days": active_days,
                "log_quiz_clicks": np.log1p(quiz_clicks),
            }
        ]
    )

    model = load_model()
    model_probability = float(
        model.predict_proba(features)[0, 1]
    )

    attendance_penalty = (
        max(0, 75 - attendance_rate) / 100 * 0.15
    )

    risk_score = min(
        0.99,
        model_probability + attendance_penalty,
    )

    if risk_score >= 0.7:
        risk_band = "high"
    elif risk_score >= 0.4:
        risk_band = "medium"
    else:
        risk_band = "low"

    factors = [
        (
            "早期平均成绩低于50分。"
            if avg_score < 50
            else "早期平均成绩处于可接受范围。"
        ),
        (
            "作业提交率需要关注。"
            if submission_rate < 0.7
            else "作业提交情况较稳定。"
        ),
        (
            "出勤率低于75%，已增加透明规则修正。"
            if attendance_rate < 75
            else "出勤率未触发额外风险修正。"
        ),
        (
            "学习平台活跃天数较少。"
            if active_days < 12
            else "学习平台活跃天数处于预期范围。"
        ),
    ]

    if risk_band == "high":
        recommendation = (
            "建议在五个工作日内安排导师沟通，"
            "并与学生商定学习改进计划。"
        )
    elif risk_band == "medium":
        recommendation = (
            "建议发送支持性提醒，"
            "下周复查作业提交和学习参与情况。"
        )
    else:
        recommendation = (
            "继续常规观察，"
            "当前原型没有提示紧急干预。"
        )

    return {
        "model_probability": model_probability,
        "attendance_penalty": attendance_penalty,
        "risk_score": risk_score,
        "risk_band": risk_band,
        "factors": factors,
        "recommendation": recommendation,
    }