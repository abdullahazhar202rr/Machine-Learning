import os
import pickle
import numpy as np
import pandas as pd
import yfinance as yf
from sklearn.metrics import accuracy_score, roc_auc_score, f1_score, precision_score, recall_score, confusion_matrix
from sklearn.preprocessing import StandardScaler
from xgboost import XGBClassifier

MODELS_DIR = "models"

def create_features(df):
    df = df.copy()
    df['month'] = pd.to_datetime(df['Date']).dt.month
    df['is_quarter_end'] = np.where(df['month'] % 3 == 0, 1, 0)
    df['open-close'] = df['Open'] - df['Close']
    df['low-high'] = df['Low'] - df['High']
    df['vol_change'] = df['Volume'].pct_change().fillna(0)
    df['lag_return'] = df['Close'].pct_change().fillna(0)
    
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14, min_periods=1).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14, min_periods=1).mean()
    rs = gain / (loss + 1e-9)
    df['rsi_14'] = 100 - (100 / (1 + rs))
    
    ema_fast = df['Close'].ewm(span=12, adjust=False).mean()
    ema_slow = df['Close'].ewm(span=26, adjust=False).mean()
    df['macd'] = ema_fast - ema_slow
    
    df['sma_fast'] = df['Close'].rolling(window=12, min_periods=1).mean()
    
    df['obv'] = (np.sign(df['Close'].diff()) * df['Volume']).fillna(0).cumsum()
    
    ma20 = df['Close'].rolling(window=20, min_periods=1).mean()
    std20 = df['Close'].rolling(window=20, min_periods=1).std()
    
    # Make sure they are 1D Series
    ma20 = pd.Series(ma20.values.flatten(), index=df.index)
    std20 = pd.Series(std20.values.flatten(), index=df.index)
    
    df['bb_high'] = ma20 + 2 * std20
    df['bb_low'] = ma20 - 2 * std20
    
    bb_high = pd.Series(df['bb_high'].values.flatten(), index=df.index)
    bb_low = pd.Series(df['bb_low'].values.flatten(), index=df.index)
    close = pd.Series(df['Close'].values.flatten(), index=df.index)
    
    df['bb_pos'] = (close - bb_low) / (bb_high - bb_low + 1e-9)
    
    df['atr_14'] = (df['High'] - df['Low']).rolling(window=14, min_periods=1).mean()
    
    df['target'] = np.where(df['Close'].shift(-1) > df['Close'], 1, 0)
    
    df = df.dropna()
    return df

def download_btc(years=5):
    print(f"Downloading BTC-USD data for last {years} years...")
    df = yf.download('BTC-USD', period=f'{years}y', interval='1d', progress=False)
    if 'Adj Close' in df.columns:
        df = df.drop(columns=['Adj Close'])
    df = df.reset_index()
    return df

def main():
    # Load scaler, model, and feature columns
    scaler = pickle.load(open(os.path.join(MODELS_DIR, 'scaler.pkl'), 'rb'))
    xgb_model = pickle.load(open(os.path.join(MODELS_DIR, 'xgb.pkl'), 'rb'))
    feature_cols = pickle.load(open(os.path.join(MODELS_DIR, 'feature_cols.pkl'), 'rb'))

    df = download_btc()
    df = create_features(df)

    X = df[feature_cols].values
    y = df['target'].values

    split_idx = int(0.8 * len(df))
    X_train, X_test = X[:split_idx], X[split_idx:]
    y_train, y_test = y[:split_idx], y[split_idx:]

    X_test_scaled = scaler.transform(X_test)

    # Real-time simulation: check accuracy on 150 predictions sequentially
    n_predictions = 150
    n_predictions = min(n_predictions, len(X_test_scaled))  # safeguard
    
    correct = 0
    y_preds = []
    y_probas = []

    for i in range(n_predictions):
        X_current = X_test_scaled[i].reshape(1, -1)
        y_true = y_test[i]

        y_proba = xgb_model.predict_proba(X_current)[:, 1]
        y_pred = int(y_proba[0] > 0.5)  # <-- Fix here to avoid warning

        y_preds.append(y_pred)
        y_probas.append(y_proba[0])
        if y_pred == y_true:
            correct += 1

    y_preds = np.array(y_preds)
    y_probas = np.array(y_probas)
    y_true = y_test[:n_predictions]

    acc = accuracy_score(y_true, y_preds)
    auc = roc_auc_score(y_true, y_probas)
    f1 = f1_score(y_true, y_preds)
    prec = precision_score(y_true, y_preds)
    rec = recall_score(y_true, y_preds)
    cm = confusion_matrix(y_true, y_preds)

    print(f"Real-time simulated test metrics over {n_predictions} predictions:")
    print(f"  Accuracy:  {acc:.4f}")
    print(f"  ROC AUC:   {auc:.4f}")
    print(f"  F1 Score:  {f1:.4f}")
    print(f"  Precision: {prec:.4f}")
    print(f"  Recall:    {rec:.4f}")
    print("Confusion Matrix:")
    print(cm)

if __name__ == "__main__":
    main()
