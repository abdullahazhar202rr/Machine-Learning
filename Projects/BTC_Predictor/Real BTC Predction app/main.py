from fastapi import FastAPI
from fastapi.responses import JSONResponse
import yfinance as yf
import pandas as pd
import numpy as np
import joblib

app = FastAPI()

MODEL_PATH = "models/rf.pkl"
SCALER_PATH = "models/scaler.pkl"
FEATURES_PATH = "models/feature_cols.pkl"

model = joblib.load(MODEL_PATH)
scaler = joblib.load(SCALER_PATH)
feature_cols = joblib.load(FEATURES_PATH)

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

@app.get("/")
async def predict():
    df = yf.download('BTC-USD', period='3y', interval='1d', progress=False)
    df.reset_index(inplace=True)

    df = create_features(df)
    latest_data = df.iloc[-1][feature_cols].values.reshape(1, -1)


    latest_scaled = scaler.transform(latest_data)


    pred = model.predict(latest_scaled)[0]


    result = "Up" if pred == 1 else "Down"

    return JSONResponse({
        "prediction": int(pred),
        "prediction_label": result,
        "message": f"BTC price is predicted to go {result} tomorrow."
    })
