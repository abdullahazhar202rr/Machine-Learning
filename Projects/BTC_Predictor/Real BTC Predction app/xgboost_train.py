import pickle
import os

MODELS_DIR = "models"
TARGET_DIR = "flask_model"  # folder for your flask app model files
os.makedirs(TARGET_DIR, exist_ok=True)

# Load the existing model and scaler
xgb_model = pickle.load(open(os.path.join(MODELS_DIR, 'xgb.pkl'), 'rb'))
scaler = pickle.load(open(os.path.join(MODELS_DIR, 'scaler.pkl'), 'rb'))
feature_cols = pickle.load(open(os.path.join(MODELS_DIR, 'feature_cols.pkl'), 'rb'))

# Save only what you need in your flask app folder
pickle.dump(xgb_model, open(os.path.join(TARGET_DIR, 'xgb.pkl'), 'wb'))
pickle.dump(scaler, open(os.path.join(TARGET_DIR, 'scaler.pkl'), 'wb'))
pickle.dump(feature_cols, open(os.path.join(TARGET_DIR, 'feature_cols.pkl'), 'wb'))

print("XGBoost model, scaler, and feature columns saved for Flask app.")
