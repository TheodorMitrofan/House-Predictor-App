import os
import sys
import numpy as np
import pandas as pd
from datetime import datetime
from sklearn.model_selection import train_test_split
from sklearn.metrics import r2_score, mean_squared_error
from sklearn.linear_model import Ridge
from sklearn.ensemble import RandomForestRegressor
from lightgbm import LGBMRegressor
import matplotlib.pyplot as plt

# 1. Configuration & Path Setup
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CSV_PATH = os.path.join(ROOT_DIR, "house_prices.csv")
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

def print_header(title):
    print("\n" + "=" * 80)
    print(f" {title.upper()} ".center(80, "="))
    print("=" * 80)

def main():
    print_header("ProphetAI Model Demonstration & Comparative Benchmark")
    
    # Check if dataset is available
    if not os.path.exists(CSV_PATH):
        print(f"Error: Could not find dataset at: {CSV_PATH}")
        print("Please ensure 'house_prices.csv' is in the root directory before running this script.")
        sys.exit(1)
        
    print(f"[OK] Found dataset at: {CSV_PATH}")
    
    # 2. Loading the Raw Data
    print("\n[Step 1] Loading raw dataset...")
    df = pd.read_csv(CSV_PATH)
    print(f"  Shape of dataset: {df.shape[0]} rows, {df.shape[1]} columns")
    print(f"  Available Columns: {list(df.columns)}")
    
    # 3. Preprocessing & Derived Feature Engineering
    print("\n[Step 2] Applying Preprocessing & Feature Engineering...")
    print("  Applying identical transformation steps as trainer.py & features.py:")
    print("  - Calculating 'house_age' relative to the current year")
    print("  - Engineering 'renovated' binary indicator from 'yr_renovated'")
    print("  - Engineering 'years_since_renovation' feature")
    print("  - Computing 'total_sqft' (above ground + basement)")
    print("  - Engineering 'has_basement' binary indicator")
    print("  - Generating ratios: 'price_per_sqft_area', 'bath_per_bed', 'living_lot_ratio'")
    
    current_year = datetime.now().year
    
    # Compute derived features
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
    
    # 4. Encoding Categoricals
    print("  - Encoding ordinal condition string column to 'condition_enc'")
    condition_map = {
        "Poor": 1, "Fair": 2, "Average": 3, "Good": 4, "Very Good": 5
    }
    df["condition_enc"] = df["condition"].map(condition_map).fillna(3).astype(int)
    
    print("  - Encoding waterfront string column ('N'/'Y') to binary 'waterfront_enc'")
    df["waterfront_enc"] = df["waterfront"].map({"N": 0, "Y": 1}).fillna(0).astype(int)
    
    # 5. Extract Feature Matrix
    FEATURE_COLS = [
        "bedrooms", "bathrooms", "sqft_living", "sqft_lot", "floors", "view", "grade",
        "sqft_above", "sqft_basement", "zipcode", "lat", "long", "sqft_living15", "sqft_lot15",
        "house_age", "renovated", "years_since_renovation", "total_sqft", "has_basement",
        "price_per_sqft_area", "bath_per_bed", "living_lot_ratio", "condition_enc", "waterfront_enc",
    ]
    TARGET_COL = "price"
    
    # Drop NaNs
    clean_df = df.dropna(subset=FEATURE_COLS + [TARGET_COL])
    print(f"  Rows remaining after cleaning NaNs: {len(clean_df)} (from {len(df)})")
    
    X = clean_df[FEATURE_COLS]
    y = clean_df[TARGET_COL]
    
    # 6. Train/Test Split
    print("\n[Step 3] Splitting data into Train (80%) and Test (20%) sets...")
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )
    print(f"  Training set size: {X_train.shape[0]} rows")
    print(f"  Test set size: {X_test.shape[0]} rows")
    
    # 7. Comparative Benchmarking
    print_header("Step 4: Comparative Benchmarking")
    print("  Training and comparing multiple models to find the absolute champion...")
    
    models = {
        "Ridge Regression": Ridge(alpha=1.0),
        "Random Forest": RandomForestRegressor(n_estimators=50, max_depth=10, random_state=42, n_jobs=-1),
        "LightGBM Regressor": LGBMRegressor(
            n_estimators=500, max_depth=8, learning_rate=0.05,
            subsample=0.8, colsample_bytree=0.8, n_jobs=-1, random_state=42, verbose=-1
        )
    }
    
    results = {}
    
    for name, model in models.items():
        print(f"  - Training {name}...")
        start_t = datetime.now()
        model.fit(X_train, y_train)
        duration = (datetime.now() - start_t).total_seconds()
        
        y_pred = model.predict(X_test)
        accuracy = r2_score(y_test, y_pred)
        rmse = np.sqrt(mean_squared_error(y_test, y_pred))
        
        results[name] = {
            "model": model,
            "accuracy": accuracy,
            "rmse": rmse,
            "duration": duration,
            "y_pred": y_pred
        }
        
    # Print Console comparison table
    print("\n" + "-" * 75)
    print(f"{'Model Name':<28} | {'R2 Accuracy (%)':<18} | {'RMSE ($)':<14} | {'Time (s)':<8}")
    print("-" * 75)
    for name, res in results.items():
        print(f"{name:<28} | {res['accuracy']*100:>16.2f}% | {res['rmse']:>12,.2f} | {res['duration']:>7.3f}")
    print("-" * 75)
    
    # Identify Champion
    champion_name = max(results, key=lambda k: results[k]["accuracy"])
    champion = results[champion_name]
    print(f"\n*** CHAMPION MODEL: {champion_name} (Accuracy: {champion['accuracy']*100:.2f}%)")
    
    # 8. Showing Feature Importances for Champion
    print_header(f"Feature Importances - {champion_name}")
    print("How features impact the predictions (Top 10):")
    
    champion_model = champion["model"]
    if hasattr(champion_model, "feature_importances_"):
        importances = champion_model.feature_importances_
        sorted_idx = np.argsort(importances)[::-1]
        for idx in sorted_idx[:10]:
            feat_name = FEATURE_COLS[idx]
            val = importances[idx]
            bar = "#" * int(val / max(importances) * 30)
            print(f"  {feat_name:<25} : {val:>5}  {bar}")
    else:
        print("  (Feature importances are not available for this model type)")
        
    # 9. Sample Demonstration
    print_header("Simulation: Predicting House Value")
    sample_index = X_test.index[0]
    sample_features = X_test.loc[[sample_index]]
    actual_price = y_test.loc[sample_index]
    
    predicted_price = champion_model.predict(sample_features)[0]
    
    print("Testing on a real house from the test dataset:")
    print(f"  - Location Zipcode: {sample_features['zipcode'].values[0]}")
    print(f"  - Bedrooms: {sample_features['bedrooms'].values[0]}")
    print(f"  - Bathrooms: {sample_features['bathrooms'].values[0]}")
    print(f"  - Total Sqft: {sample_features['total_sqft'].values[0]}")
    print(f"  - Age of house: {sample_features['house_age'].values[0]} years")
    print("-" * 50)
    print(f"  Actual Price:    ${actual_price:,.2f}")
    print(f"  Predicted Price: ${predicted_price:,.2f}")
    diff = predicted_price - actual_price
    print(f"  Difference:      ${diff:,.2f} ({diff / actual_price * 100:+.2f}%)")
    
    # 10. Plot Generation
    print_header("Generating Fancy Visualizations")
    
    try:
        # Plot 1: Model Accuracy Comparison Bar Chart
        plt.figure(figsize=(9, 5))
        names_list = list(results.keys())
        acc_list = [results[n]["accuracy"] * 100 for n in names_list]
        colors = ['#cbd5e1', '#94a3b8', '#3b82f6'] # Sleek grey to dynamic blue for champion
        
        bars = plt.bar(names_list, acc_list, color=colors, edgecolor='none', width=0.5)
        plt.title("Model Accuracy (R2 Score) Comparison", fontsize=13, fontweight='bold', pad=15)
        plt.ylabel("R2 Accuracy (%)", fontsize=11)
        plt.ylim(0, 100)
        plt.grid(axis='y', linestyle='--', alpha=0.5)
        
        # Add labels on top of bars
        for bar in bars:
            height = bar.get_height()
            plt.text(bar.get_x() + bar.get_width()/2., height + 2,
                     f'{height:.2f}%', ha='center', va='bottom', fontweight='bold')
            
        plt.tight_layout()
        img1_path = os.path.join(SCRIPT_DIR, "models_comparison.png")
        plt.savefig(img1_path, dpi=200)
        print(f"  [OK] Plot 1 Saved successfully: {img1_path}")
        
        # Plot 2: Feature Importances
        if hasattr(champion_model, "feature_importances_"):
            plt.figure(figsize=(10, 6))
            top_feats = [FEATURE_COLS[idx] for idx in sorted_idx[:10]]
            top_vals = [importances[idx] for idx in sorted_idx[:10]]
            colors = plt.cm.viridis(np.linspace(0.3, 0.85, 10))
            
            plt.barh(top_feats[::-1], top_vals[::-1], color=colors, edgecolor='none', height=0.6)
            plt.title(f"ProphetAI Model - {champion_name} Top 10 Feature Importances", fontsize=13, fontweight='bold', pad=15)
            plt.xlabel("Gini Importance Score", fontsize=11)
            plt.grid(axis='x', linestyle='--', alpha=0.5)
            plt.tight_layout()
            
            img2_path = os.path.join(SCRIPT_DIR, "feature_importances.png")
            plt.savefig(img2_path, dpi=200)
            print(f"  [OK] Plot 2 Saved successfully: {img2_path}")
            
        # Plot 3: Actual vs Predicted Prices Scatter Plot (Champion)
        plt.figure(figsize=(7, 7))
        y_pred_ch = champion["y_pred"]
        plt.scatter(y_test / 1000, y_pred_ch / 1000, alpha=0.3, color='#1e3a8a', label='Predictions')
        
        min_val = min(y_test.min() / 1000, y_pred_ch.min() / 1000)
        max_val = max(y_test.max() / 1000, y_pred_ch.max() / 1000)
        plt.plot([min_val, max_val], [min_val, max_val], '--', color='#ef4444', linewidth=2.5, label='Perfect prediction (y=x)')
        
        plt.title(f"ProphetAI Champion Model - Actual vs Predicted", fontsize=13, fontweight='bold', pad=15)
        plt.xlabel("Actual Price (thousands $)", fontsize=11)
        plt.ylabel("Predicted Price (thousands $)", fontsize=11)
        plt.gca().xaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: format(int(x), ',')))
        plt.gca().yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: format(int(x), ',')))
        plt.legend()
        plt.grid(True, linestyle='--', alpha=0.5)
        plt.tight_layout()
        
        img3_path = os.path.join(SCRIPT_DIR, "predictions_comparison.png")
        plt.savefig(img3_path, dpi=200)
        print(f"  [OK] Plot 3 Saved successfully: {img3_path}")
        
        print("\n  [INFO] Opening comparison charts window. Close the window to exit...")
        plt.show()
        
    except Exception as chart_err:
        print(f"  [WARNING] Could not open interactive graphical interface: {chart_err}")
        
    print("=" * 80 + "\n")

if __name__ == "__main__":
    main()
