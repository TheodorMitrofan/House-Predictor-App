"""
Model Benchmark — Compares multiple regression models on house_prices.csv
to find the best model for house price prediction.

Models tested:
  1. Random Forest (current baseline)
  2. Gradient Boosting
  3. XGBoost
  4. LightGBM
  5. Ridge Regression
  6. Lasso Regression

Metrics: R², MAE, RMSE, MAPE
"""

import numpy as np
import pandas as pd
from datetime import datetime

from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.linear_model import Ridge, Lasso
from sklearn.metrics import r2_score, mean_absolute_error, mean_squared_error
from xgboost import XGBRegressor
from lightgbm import LGBMRegressor

# ── Load & Prepare Data ─────────────────────────────────────────────

CSV_PATH = "../house_prices.csv"

def load_and_prepare():
    df = pd.read_csv(CSV_PATH)
    print(f"Dataset: {df.shape[0]} rows, {df.shape[1]} columns")
    print(f"Columns: {list(df.columns)}\n")

    # Drop id and date
    df = df.drop(columns=["id", "date"], errors="ignore")

    # Derived features
    current_year = datetime.now().year
    df["house_age"] = current_year - df["yr_built"]
    df["renovated"] = (df["yr_renovated"] > 0).astype(int)
    df["years_since_renovation"] = np.where(
        df["yr_renovated"] > 0,
        current_year - df["yr_renovated"],
        df["house_age"]
    )
    df["total_sqft"] = df["sqft_above"] + df["sqft_basement"]
    df["has_basement"] = (df["sqft_basement"] > 0).astype(int)
    df["price_per_sqft_area"] = df["sqft_living"] / (df["sqft_lot"] + 1)
    df["bath_per_bed"] = df["bathrooms"] / (df["bedrooms"] + 1)
    df["living_lot_ratio"] = df["sqft_living"] / (df["sqft_lot"] + 1)

    # Encode condition (ordinal)
    condition_map = {
        "Poor": 1, "Fair": 2, "Average": 3, "Good": 4, "Very Good": 5
    }
    df["condition_enc"] = df["condition"].map(condition_map).fillna(3).astype(int)

    # Encode waterfront
    df["waterfront_enc"] = df["waterfront"].map({"N": 0, "Y": 1}).fillna(0).astype(int)

    # Drop original string columns
    df = df.drop(columns=["yr_built", "yr_renovated", "condition", "waterfront"], errors="ignore")

    # Target
    y = df["price"]
    X = df.drop(columns=["price"])

    print(f"Features ({X.shape[1]}): {list(X.columns)}")
    print(f"Target: price | min={y.min():.0f}, max={y.max():.0f}, mean={y.mean():.0f}\n")

    return X, y


# ── Model Definitions ────────────────────────────────────────────────

def get_models():
    return {
        "Random Forest (baseline)": RandomForestRegressor(
            n_estimators=100, max_depth=15, min_samples_split=5,
            n_jobs=-1, random_state=42,
        ),
        "Gradient Boosting": GradientBoostingRegressor(
            n_estimators=300, max_depth=6, learning_rate=0.1,
            min_samples_split=5, random_state=42,
        ),
        "XGBoost": XGBRegressor(
            n_estimators=500, max_depth=6, learning_rate=0.05,
            subsample=0.8, colsample_bytree=0.8,
            n_jobs=-1, random_state=42, verbosity=0,
        ),
        "LightGBM": LGBMRegressor(
            n_estimators=500, max_depth=8, learning_rate=0.05,
            subsample=0.8, colsample_bytree=0.8,
            n_jobs=-1, random_state=42, verbose=-1,
        ),
        "Ridge": Ridge(alpha=1.0),
        "Lasso": Lasso(alpha=100.0),
    }


# ── Evaluation ───────────────────────────────────────────────────────

def evaluate_model(model, X_train, X_test, y_train, y_test):
    model.fit(X_train, y_train)
    y_pred = model.predict(X_test)

    r2 = r2_score(y_test, y_pred)
    mae = mean_absolute_error(y_test, y_pred)
    rmse = np.sqrt(mean_squared_error(y_test, y_pred))
    mape = np.mean(np.abs((y_test - y_pred) / (y_test + 1e-9))) * 100

    return {
        "R²": round(r2, 4),
        "MAE": round(mae, 2),
        "RMSE": round(rmse, 2),
        "MAPE (%)": round(mape, 2),
    }


def run_benchmark():
    X, y = load_and_prepare()

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )
    print(f"Train: {X_train.shape[0]} rows | Test: {X_test.shape[0]} rows\n")

    # Scale for linear models
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    models = get_models()
    results = {}

    print("=" * 70)
    print(f"{'Model':<30} {'R²':>8} {'MAE':>12} {'RMSE':>12} {'MAPE%':>8}")
    print("=" * 70)

    for name, model in models.items():
        # Use scaled data for linear models
        if name in ("Ridge", "Lasso"):
            metrics = evaluate_model(model, X_train_scaled, X_test_scaled, y_train, y_test)
        else:
            metrics = evaluate_model(model, X_train, X_test, y_train, y_test)

        results[name] = metrics
        print(f"{name:<30} {metrics['R²']:>8.4f} {metrics['MAE']:>12,.2f} {metrics['RMSE']:>12,.2f} {metrics['MAPE (%)']:>8.2f}")

    print("=" * 70)

    # Find the best model
    best_name = max(results, key=lambda k: results[k]["R²"])
    best = results[best_name]
    print(f"\n>>> Best model: {best_name}")
    print(f"   R² = {best['R²']} | MAE = ${best['MAE']:,.2f} | RMSE = ${best['RMSE']:,.2f}")

    # Cross-validation for the best model
    print(f"\n-- 5-Fold Cross Validation for {best_name} --")
    best_model = get_models()[best_name]
    cv_scores = cross_val_score(best_model, X, y, cv=5, scoring="r2", n_jobs=-1)
    print(f"   CV R² scores: {[round(s, 4) for s in cv_scores]}")
    print(f"   CV R² mean:   {cv_scores.mean():.4f} ± {cv_scores.std():.4f}")

    # Feature importance for the best tree-based model
    if hasattr(get_models()[best_name], "feature_importances_"):
        print(f"\n-- Top 10 Feature Importances ({best_name}) --")
        best_model.fit(X, y)
        importances = best_model.feature_importances_
        feature_imp = sorted(
            zip(X.columns, importances),
            key=lambda x: x[1],
            reverse=True,
        )
        for feat, imp in feature_imp[:10]:
            bar = "#" * int(imp * 100)
            print(f"   {feat:<25} {imp:.4f}  {bar}")

    return best_name, results


if __name__ == "__main__":
    run_benchmark()
