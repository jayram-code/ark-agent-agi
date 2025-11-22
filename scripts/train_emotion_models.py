# scripts/train_emotion_models.py
import os

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.impute import SimpleImputer
from sklearn.metrics import accuracy_score, classification_report, mean_squared_error
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

CSV_PATH = "data/Hide_and_Seek_DATASET.csv"  # adjust if located elsewhere
OUT_DIR = "src/models"
os.makedirs(OUT_DIR, exist_ok=True)

print("Loading dataset:", CSV_PATH)
df = pd.read_csv(CSV_PATH)

# Quick sanity: ensure target columns exist
assert 'stress' in df.columns, "Column 'stress' not found in CSV"
assert 'call_label' in df.columns, "Column 'call_label' not found in CSV"

# drop columns that are non-numeric or identifiers if needed
# we'll keep only numeric features for modeling
numeric = df.select_dtypes(include=[np.number]).copy()

# remove target columns from features
X = numeric.drop(columns=['stress', 'call_label'], errors='ignore')
y_reg = numeric['stress'].values
y_clf = numeric['call_label'].astype(int).values

# small preprocessing: impute + scale
imputer = SimpleImputer(strategy='median')
scaler = StandardScaler()

# Train/test split
X_train, X_test, y_reg_train, y_reg_test = train_test_split(X, y_reg, test_size=0.2, random_state=42)
_, _, y_clf_train, y_clf_test = train_test_split(X, y_clf, test_size=0.2, random_state=42)

# Regression pipeline
reg_pipeline = Pipeline([
    ('impute', imputer),
    ('scale', scaler),
    ('rf', RandomForestRegressor(n_estimators=200, random_state=42, n_jobs=-1))
])
print("Training stress regressor...")
reg_pipeline.fit(X_train, y_reg_train)
y_reg_pred = reg_pipeline.predict(X_test)
mse = mean_squared_error(y_reg_test, y_reg_pred)
print(f"Stress regressor MSE: {mse:.4f}")

# Classification pipeline
clf_pipeline = Pipeline([
    ('impute', imputer),
    ('scale', scaler),
    ('rf', RandomForestClassifier(n_estimators=200, random_state=42, n_jobs=-1))
])
print("Training call_label classifier...")
clf_pipeline.fit(X_train, y_clf_train)
y_clf_pred = clf_pipeline.predict(X_test)
acc = accuracy_score(y_clf_test, y_clf_pred)
print(f"Call label classifier accuracy: {acc:.4f}")
print("Classification report:")
print(classification_report(y_clf_test, y_clf_pred))

# Save models
reg_path = os.path.join(OUT_DIR, "stress_model.joblib")
clf_path = os.path.join(OUT_DIR, "call_model.joblib")
joblib.dump(reg_pipeline, reg_path)
joblib.dump(clf_pipeline, clf_path)
print("Saved models to:", reg_path, clf_path)

# scripts/train_emotion_models.py
import os

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.impute import SimpleImputer
from sklearn.metrics import accuracy_score, classification_report, mean_squared_error
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

# allow override so we can point to the sample csv without editing again
CSV_PATH = os.getenv("CSV_PATH_OVERRIDE", "data/Hide_and_Seek_DATASET.csv")
OUT_DIR = "src/models"
os.makedirs(OUT_DIR, exist_ok=True)

# tune down complexity for faster local training
N_ESTIMATORS = int(os.getenv("RF_TREES", "80"))

print("Loading dataset:", CSV_PATH)
df = pd.read_csv(CSV_PATH)

# Quick sanity: ensure target columns exist
if 'stress' not in df.columns or 'call_label' not in df.columns:
    raise RuntimeError("Required columns 'stress' or 'call_label' not found in CSV")

# keep only numeric columns
numeric = df.select_dtypes(include=[np.number]).copy()

# drop target columns from features
X = numeric.drop(columns=['stress', 'call_label'], errors='ignore')
y_reg = numeric['stress'].values
y_clf = numeric['call_label'].astype(int).values

# small preprocessing: impute + scale
imputer = SimpleImputer(strategy='median')
scaler = StandardScaler()

# Train/test split
X_train, X_test, y_reg_train, y_reg_test = train_test_split(X, y_reg, test_size=0.2, random_state=42)
_, _, y_clf_train, y_clf_test = train_test_split(X, y_clf, test_size=0.2, random_state=42)

# Regression pipeline
reg_pipeline = Pipeline([
    ('impute', imputer),
    ('scale', scaler),
    ('rf', RandomForestRegressor(n_estimators=N_ESTIMATORS, random_state=42, n_jobs=-1))
])
print(f"Training stress regressor (n_estimators={N_ESTIMATORS})...")
reg_pipeline.fit(X_train, y_reg_train)
y_reg_pred = reg_pipeline.predict(X_test)
mse = mean_squared_error(y_reg_test, y_reg_pred)
print(f"Stress regressor MSE: {mse:.4f}")

# Classification pipeline
clf_pipeline = Pipeline([
    ('impute', imputer),
    ('scale', scaler),
    ('rf', RandomForestClassifier(n_estimators=N_ESTIMATORS, random_state=42, n_jobs=-1))
])
print(f"Training call_label classifier (n_estimators={N_ESTIMATORS})...")
clf_pipeline.fit(X_train, y_clf_train)
y_clf_pred = clf_pipeline.predict(X_test)
acc = accuracy_score(y_clf_test, y_clf_pred)
print(f"Call label classifier accuracy: {acc:.4f}")
print("Classification report:")
print(classification_report(y_clf_test, y_clf_pred))

# Save models
reg_path = os.path.join(OUT_DIR, "stress_model.joblib")
clf_path = os.path.join(OUT_DIR, "call_model.joblib")
joblib.dump(reg_pipeline, reg_path)
joblib.dump(clf_pipeline, clf_path)
print("Saved models to:", reg_path, clf_path)
