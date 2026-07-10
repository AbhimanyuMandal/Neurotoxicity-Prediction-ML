"""
06_train_models.py

Train multiple machine learning models on RDKit molecular descriptors.

Author: Abhimanyu Mandal
"""

from importlib.metadata import metadata
from pathlib import Path
import warnings
warnings.filterwarnings("ignore")

import joblib
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from sklearn.model_selection import (
    train_test_split,
    cross_val_score,
)

from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
    classification_report,
    confusion_matrix,
    ConfusionMatrixDisplay,
    RocCurveDisplay,
)

from sklearn.ensemble import (
    RandomForestClassifier,
    GradientBoostingClassifier,
)

from sklearn.linear_model import LogisticRegression
from sklearn.svm import SVC


# ======================================================
# PATHS
# ======================================================

BASE_DIR = Path(__file__).resolve().parent.parent

DATA_FILE = BASE_DIR / "data" / "processed" / "rdkit_descriptors.csv"

MODEL_DIR = BASE_DIR / "models"
REPORT_DIR = BASE_DIR / "reports"
FIGURE_DIR = BASE_DIR / "figures"

for directory in [MODEL_DIR, REPORT_DIR, FIGURE_DIR]:
    directory.mkdir(parents=True, exist_ok=True)


# ======================================================
# LOAD DATA
# ======================================================

def load_data():

    print("\nLoading descriptor dataset...")

    df = pd.read_csv(DATA_FILE)

    print(f"Samples : {len(df)}")

    return df


# ======================================================
# PREPARE FEATURES
# ======================================================

def prepare_features(df):

    metadata_columns = [

        "Compound_Name",
        "Label",
        "CID",
        "Canonical_SMILES",
        "MolecularFormula",
        "MolecularWeight",
        "InChIKey",

        "Class",
        "Category",

        "Connectivity_SMILES",
        "RDKit_SMILES",
        "RDKit_InChIKey",
        "Validation_Status",
        "InChI",
        "IUPACName",

    ]

    metadata_columns = [

        c for c in metadata_columns

        if c in df.columns

    ]

    feature_columns = [

        c for c in df.columns

        if c not in metadata_columns

    ]

    feature_columns = [

        c for c in feature_columns

        if pd.api.types.is_numeric_dtype(df[c])

    ]

    X = df[feature_columns].copy()

    print("\nChecking descriptors...")

    # Find infinite values
    inf_cols = X.columns[np.isinf(X.select_dtypes(include=[np.number])).any()]
    print("Columns with Inf:", list(inf_cols))

    # Find very large values
    numeric = X.select_dtypes(include=[np.number])

    for col in numeric.columns:
        max_val = numeric[col].abs().max()
        if pd.notna(max_val) and max_val > 1e10:
            print(f"{col}: max={max_val}")

    X.replace([np.inf, -np.inf], np.nan, inplace=True)

    X.dropna(axis=1, how="all", inplace=True)

    X = X.loc[:, X.nunique() > 1]

    X.fillna(X.median(numeric_only=True), inplace=True)

    X = X.astype(float)

    feature_columns = X.columns.tolist()

    print(f"Final descriptor count : {len(feature_columns)}")

    pd.Series(feature_columns).to_csv(

        REPORT_DIR / "features_used.csv",

        index=False

    )

    if df["Label"].dtype == object:

        y = df["Label"].map({

            "Neuroprotective": 0,

            "Neurotoxic": 1

        })

    else:

        y = df["Label"]

    if y.isna().any():

        raise ValueError(

            "Unknown class labels detected."

        )

    print("\nClass Distribution")

    print(df["Label"].value_counts())

    return X, y, feature_columns

# ======================================================
# MODEL DEFINITIONS
# ======================================================

def get_models():

    return {

        "Random Forest": RandomForestClassifier(
            n_estimators=500,
            random_state=42,
            class_weight="balanced",
            n_jobs=-1,
        ),

        "Logistic Regression": Pipeline([
            ("scaler", StandardScaler()),
            ("classifier",
                LogisticRegression(
                    max_iter=5000,
                    random_state=42
                )
            )
        ]),

        "Support Vector Machine": Pipeline([
            ("scaler", StandardScaler()),
            ("classifier",
                SVC(
                    probability=True,
                    random_state=42
                )
            )
        ])

    }


# ======================================================
# TRAIN ALL MODELS
# ======================================================

def train_models(X, y, feature_columns):

    print("\nSplitting dataset...")

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.20,
        random_state=42,
        stratify=y,
    )

    print(f"Training samples : {len(X_train)}")
    print(f"Testing samples  : {len(X_test)}")

    models = get_models()

    results = []

    trained_models = {}

    best_model = None
    best_name = None
    best_auc = -1

    for name, model in models.items():

        print("\n" + "=" * 60)
        print(name)
        print("=" * 60)

        # --------------------------
        # Cross Validation
        # --------------------------

        cv_scores = cross_val_score(
            model,
            X_train,
            y_train,
            cv=5,
            scoring="roc_auc",
            n_jobs=-1,
        )

        # --------------------------
        # Train
        # --------------------------

        model.fit(X_train, y_train)

        trained_models[name] = model

        # --------------------------
        # Predictions
        # --------------------------

        y_pred = model.predict(X_test)

        if hasattr(model, "predict_proba"):

            y_score = model.predict_proba(X_test)[:, 1]

        else:

            y_score = model.decision_function(X_test)

        # --------------------------
        # Metrics
        # --------------------------

        accuracy = accuracy_score(y_test, y_pred)

        precision = precision_score(y_test, y_pred)

        recall = recall_score(y_test, y_pred)

        f1 = f1_score(y_test, y_pred)

        roc_auc = roc_auc_score(y_test, y_score)

        print(f"Accuracy : {accuracy:.4f}")
        print(f"Precision: {precision:.4f}")
        print(f"Recall   : {recall:.4f}")
        print(f"F1       : {f1:.4f}")
        print(f"ROC AUC  : {roc_auc:.4f}")
        print(
            f"CV ROC AUC : {cv_scores.mean():.4f} ± {cv_scores.std():.4f}"
        )

        results.append({

            "Model": name,

            "Accuracy": accuracy,

            "Precision": precision,

            "Recall": recall,

            "F1": f1,

            "ROC_AUC": roc_auc,

            "CV_ROC_AUC": cv_scores.mean(),

            "CV_STD": cv_scores.std(),

        })

        # --------------------------
        # Save model
        # --------------------------

        filename = name.replace(" ", "_") + ".joblib"

        joblib.dump(
            model,
            MODEL_DIR / filename
        )

        # --------------------------
        # Track best model
        # --------------------------

        if roc_auc > best_auc:

            best_auc = roc_auc
            best_model = model
            best_name = name

    # Save best model

    joblib.dump(
        best_model,
        MODEL_DIR / "best_model.joblib"
    )

    # Save feature names used during training
    joblib.dump(
    feature_columns,
    MODEL_DIR / "feature_columns.pkl"
     )

    print("Saved feature_columns.pkl")


    # Create results dataframe

    results_df = pd.DataFrame(results)

    results_df.sort_values(
        "ROC_AUC",
        ascending=False,
        inplace=True
    )

    results_df.to_csv(
        REPORT_DIR / "model_comparison.csv",
        index=False
    )

    print("\n" + "=" * 60)
    print("BEST MODEL")
    print("=" * 60)

    print(best_name)
    print(f"ROC AUC : {best_auc:.4f}")

    return (
        trained_models,
        best_model,
        best_name,
        results_df,
        X_test,
        y_test,
        feature_columns,
    )
    metadata = {
    "best_model": best_name,
    "n_features": len(feature_columns),
    "classes": {
        0: "Neuroprotective",
        1: "Neurotoxic"
    }
}

joblib.dump(
    metadata,
    MODEL_DIR / "model_metadata.pkl"
)

# ======================================================
# SAVE REPORTS AND FIGURES
# ======================================================

def save_reports(
    best_model,
    best_name,
    results_df,
    X_test,
    y_test,
    feature_columns,
):

    # --------------------------
    # Predictions
    # --------------------------

    y_pred = best_model.predict(X_test)

    if hasattr(best_model, "predict_proba"):
        y_score = best_model.predict_proba(X_test)[:, 1]
    else:
        y_score = best_model.decision_function(X_test)

    # --------------------------
    # Metrics
    # --------------------------

    report = classification_report(
        y_test,
        y_pred,
        target_names=[
            "Neuroprotective",
            "Neurotoxic",
        ]
    )

    with open(REPORT_DIR / "classification_report.txt", "w") as f:
        f.write(report)

    with open(REPORT_DIR / "metrics.txt", "w") as f:
        f.write("=" * 70 + "\n")
        f.write("MODEL COMPARISON\n")
        f.write("=" * 70 + "\n\n")
        f.write(results_df.to_string(index=False))
        f.write("\n\n")
        f.write("=" * 70 + "\n")
        f.write(f"Best Model : {best_name}\n")
        f.write("=" * 70 + "\n")

    # --------------------------
    # Confusion Matrix
    # --------------------------

    fig, ax = plt.subplots(figsize=(6, 6))

    ConfusionMatrixDisplay.from_predictions(
        y_test,
        y_pred,
        display_labels=[
            "Neuroprotective",
            "Neurotoxic"
        ],
        cmap="Blues",
        ax=ax,
    )

    plt.tight_layout()
    plt.savefig(
        FIGURE_DIR / "confusion_matrix.png",
        dpi=300
    )
    plt.close()

    # --------------------------
    # ROC Curve
    # --------------------------

    fig, ax = plt.subplots(figsize=(6, 6))

    RocCurveDisplay.from_predictions(
        y_test,
        y_score,
        name=best_name,
        ax=ax,
    )

    plt.plot(
        [0, 1],
        [0, 1],
        "--",
        linewidth=1,
    )

    plt.tight_layout()

    plt.savefig(
        FIGURE_DIR / "roc_curve.png",
        dpi=300,
    )

    plt.close()

    # --------------------------
    # Feature Importance
    # --------------------------

    if best_name in [
        "Random Forest",
        "Gradient Boosting",
    ]:

        importance = pd.DataFrame({

            "Feature": feature_columns,

            "Importance": best_model.feature_importances_

        })

        importance.sort_values(
            "Importance",
            ascending=False,
            inplace=True,
        )

        importance.to_csv(
            REPORT_DIR / "feature_importance.csv",
            index=False,
        )

        top20 = importance.head(20)

        plt.figure(figsize=(8, 7))

        plt.barh(
            top20["Feature"][::-1],
            top20["Importance"][::-1],
        )

        plt.xlabel("Importance")

        plt.title(
            f"{best_name}\nTop 20 Molecular Descriptors"
        )

        plt.tight_layout()

        plt.savefig(
            FIGURE_DIR / "feature_importance.png",
            dpi=300,
        )

        plt.close()

    print("\nReports generated successfully.")


# ======================================================
# MAIN
# ======================================================

def main():

    df = load_data()

    X, y, feature_columns = prepare_features(df)

    (
    trained_models,
    best_model,
    best_name,
    results_df,
    X_test,
    y_test,
    feature_columns,) = train_models(X, y, feature_columns)

    save_reports(
        best_model,
        best_name,
        results_df,
        X_test,
        y_test,
        feature_columns,
    )

    print("\n" + "=" * 70)
    print("PIPELINE COMPLETED SUCCESSFULLY")
    print("=" * 70)

    print(f"Best model : {best_name}")

    print("\nOutputs")

    print("models/")
    print("reports/")
    print("figures/")


if __name__ == "__main__":
    main()

    