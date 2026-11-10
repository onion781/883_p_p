from pathlib import Path
import json
import sys

import joblib
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import GroupShuffleSplit
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler


ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = (
    Path(sys.argv[1])
    if len(sys.argv) > 1
    else ROOT / "data" / "raw" / "anonymisedData"
)
MODEL_DIR = ROOT / "models"
CUTOFF = 60
FEATURES = [
    "avg_score",
    "submission_rate",
    "log_total_clicks",
    "active_days",
    "log_quiz_clicks",
]
KEYS = ["code_module", "code_presentation", "id_student"]


def main():
    required_files = [
        "studentInfo.csv",
        "assessments.csv",
        "studentAssessment.csv",
        "studentVle.csv",
        "vle.csv",
    ]

    for filename in required_files:
        file_path = DATA_DIR / filename
        if not file_path.exists():
            raise FileNotFoundError(f"Missing data file: {file_path}")

    print("Reading OULAD data...")

    students = pd.read_csv(DATA_DIR / "studentInfo.csv")
    assessments = pd.read_csv(DATA_DIR / "assessments.csv")
    student_assessments = pd.read_csv(
        DATA_DIR / "studentAssessment.csv"
    )
    vle = pd.read_csv(
        DATA_DIR / "vle.csv",
        usecols=["id_site", "activity_type"],
    )

    early_assessments = assessments.loc[
        assessments["date"].notna()
        & (assessments["date"] <= CUTOFF),
        [
            "code_module",
            "code_presentation",
            "id_assessment",
            "date",
        ],
    ]

    due_count = (
        early_assessments
        .groupby(["code_module", "code_presentation"])
        .size()
        .rename("due_count")
    )

    marks = student_assessments.merge(
        early_assessments,
        on="id_assessment",
        how="inner",
    )

    marks = marks.loc[
        (marks["date_submitted"] <= CUTOFF)
        & marks["score"].notna()
    ].copy()

    assessment_features = (
        marks
        .groupby(KEYS)
        .agg(
            avg_score=("score", "mean"),
            submitted_count=("id_assessment", "nunique"),
        )
    )

    assessment_features = assessment_features.join(
        due_count,
        on=["code_module", "code_presentation"],
    )

    assessment_features["submission_rate"] = (
        assessment_features["submitted_count"]
        / assessment_features["due_count"]
    ).clip(0, 1)

    quiz_sites = set(
        vle.loc[
            vle["activity_type"] == "quiz",
            "id_site",
        ].tolist()
    )

    vle_parts = []
    day_parts = []

    print("Processing studentVle.csv in chunks...")

    with pd.read_csv(
        DATA_DIR / "studentVle.csv",
        usecols=[
            "code_module",
            "code_presentation",
            "id_student",
            "id_site",
            "date",
            "sum_click",
        ],
        chunksize=500000,
    ) as reader:
        for index, chunk in enumerate(reader, start=1):
            print(f"Processing chunk {index}...")

            chunk = chunk.loc[
                (chunk["date"] >= 0)
                & (chunk["date"] <= CUTOFF)
            ].copy()

            if chunk.empty:
                continue

            chunk["quiz_click"] = np.where(
                chunk["id_site"].isin(quiz_sites),
                chunk["sum_click"],
                0,
            )

            grouped = chunk.groupby(KEYS).agg(
                total_clicks=("sum_click", "sum"),
                quiz_clicks=("quiz_click", "sum"),
            )

            vle_parts.append(grouped)
            day_parts.append(
                chunk[KEYS + ["date"]].drop_duplicates()
            )

    vle_features = (
        pd.concat(vle_parts)
        .groupby(level=KEYS)
        .sum()
    )

    active_days = (
        pd.concat(day_parts)
        .drop_duplicates()
        .groupby(KEYS)
        .size()
        .rename("active_days")
    )

    vle_features = vle_features.join(active_days)

    data = (
        students
        .set_index(KEYS)[["final_result"]]
        .join(assessment_features)
        .join(vle_features)
        .reset_index()
    )

    fill_columns = [
        "avg_score",
        "submission_rate",
        "total_clicks",
        "active_days",
        "quiz_clicks",
    ]

    data[fill_columns] = data[fill_columns].fillna(0)

    data["log_total_clicks"] = np.log1p(
        data["total_clicks"]
    )
    data["log_quiz_clicks"] = np.log1p(
        data["quiz_clicks"]
    )

    data = data.loc[
        data["final_result"].isin(
            ["Pass", "Distinction", "Fail", "Withdrawn"]
        )
    ].copy()

    data["at_risk"] = data["final_result"].isin(
        ["Fail", "Withdrawn"]
    ).astype(int)

    X = data[FEATURES]
    y = data["at_risk"]

    groups = (
        data["code_module"]
        + "-"
        + data["code_presentation"]
    ).to_numpy()

    splitter = GroupShuffleSplit(
        n_splits=1,
        test_size=0.25,
        random_state=42,
    )

    train_index, test_index = next(
        splitter.split(X, y, groups)
    )

    X_train = X.iloc[train_index]
    X_test = X.iloc[test_index]
    y_train = y.iloc[train_index]
    y_test = y.iloc[test_index]

    pipeline = Pipeline(
        [
            ("scaler", StandardScaler()),
            (
                "classifier",
                LogisticRegression(
                    class_weight="balanced",
                    max_iter=2000,
                    random_state=42,
                ),
            ),
        ]
    )

    print("Training logistic regression...")
    pipeline.fit(X_train, y_train)

    probabilities = pipeline.predict_proba(X_test)[:, 1]
    predictions = (probabilities >= 0.5).astype(int)

    metrics = {
        "dataset": "Open University Learning Analytics Dataset",
        "source": "https://doi.org/10.6084/m9.figshare.5081998.v1",
        "license": "CC BY 4.0",
        "cutoff_day": CUTOFF,
        "samples": int(len(data)),
        "train_samples": int(len(train_index)),
        "test_samples": int(len(test_index)),
        "roc_auc": round(
            float(roc_auc_score(y_test, probabilities)),
            4,
        ),
        "accuracy": round(
            float(accuracy_score(y_test, predictions)),
            4,
        ),
        "precision": round(
            float(precision_score(y_test, predictions)),
            4,
        ),
        "recall": round(
            float(recall_score(y_test, predictions)),
            4,
        ),
        "f1": round(
            float(f1_score(y_test, predictions)),
            4,
        ),
    }

    MODEL_DIR.mkdir(parents=True, exist_ok=True)

    joblib.dump(
        {
            "pipeline": pipeline,
            "features": FEATURES,
            "cutoff_day": CUTOFF,
        },
        MODEL_DIR / "early_warning.joblib",
    )

    with open(
        MODEL_DIR / "early_warning_metrics.json",
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            metrics,
            file,
            ensure_ascii=False,
            indent=2,
        )

    print("Training completed.")
    print(json.dumps(metrics, indent=2))


if __name__ == "__main__":
    main()