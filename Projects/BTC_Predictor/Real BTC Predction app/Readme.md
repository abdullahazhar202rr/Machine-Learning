Here is your full **README.md** content for your FastAPI Bitcoin predictor app:

````md
# 🚀 Advanced Bitcoin Price Predictor API

## 📋 Required Libraries Installation

Install all required libraries using pip:

```bash
# Core libraries
pip install fastapi uvicorn pandas numpy yfinance scikit-learn joblib

# Optional for advanced analysis or additional features
pip install matplotlib seaborn tqdm
````

## 📁 File Structure

```
btc_predictor/
├── main.py                 # FastAPI application code
├── models/
│   ├── rf.pkl              # Trained Random Forest model
│   ├── scaler.pkl          # Feature scaler
│   └── feature_cols.pkl    # Feature column names list
├── requirements.txt        # Python dependencies list
└── README.md               # This documentation
```

## 🏃‍♂️ Quick Start Guide

### Step 1: Prepare your environment

Make sure you have the models saved in the `models/` directory:

* `rf.pkl`
* `scaler.pkl`
* `feature_cols.pkl`

### Step 2: Run the FastAPI app

Start the server with Uvicorn:

```bash
uvicorn main:app --reload
```

The API will be available at:

```
http://127.0.0.1:8000/
```

### Step 3: Make a prediction request

Send a GET request to the root endpoint `/` to get the BTC price movement prediction for the next day.

Example response:

```json
{
  "prediction": 1,
  "prediction_label": "Up",
  "message": "BTC price is predicted to go Up tomorrow."
}
```

---

## 🔧 How It Works

1. Downloads the last 5 years of BTC historical data via Yahoo Finance.
2. Generates technical features like RSI, MACD, Bollinger Bands, ATR, etc.
3. Loads the pre-trained Random Forest model and scaler.
4. Scales the latest feature row and predicts the next day price movement.
5. Returns the prediction in JSON format.

---

## 📈 Model Details

* **Model Type:** Random Forest Classifier
* **Input Features:** Technical indicators generated from price and volume data
* **Output:** Binary classification — 1 (Price Up), 0 (Price Down)

---

## ⚠️ Important Notes & Troubleshooting

* **Yahoo Finance Limits:**
  Downloading data frequently may result in temporary blocks or empty data responses. Cache data if possible or add retry logic.

* **Empty Data Issue:**
  If the API returns errors or empty data, check internet connectivity and Yahoo Finance availability.

* **Model Compatibility:**
  Ensure scikit-learn versions used to save and load the model are compatible.

* **File Paths:**
  The app expects model files in the `models/` folder relative to the script.

---

## 🔄 Future Improvements

* Add caching of downloaded data to reduce API calls.
* Implement async data fetching for faster response.
* Add endpoints to accept custom tickers or timeframes.
* Include model retraining endpoints for automated updates.

---

## 📞 Contact & Support

**Author:** Abdullah Azhar

**Email:** [abdullahazhar202rr@gmail.com](mailto:abdullahazhar202rr@gmail.com)

**GitHub:** [https://github.com/abdullahazhar202rr](https://github.com/abdullahazhar202rr)

**LinkedIn:** [https://www.linkedin.com/in/abdullahazhar202](https://www.linkedin.com/in/abdullahazhar202)

---

## 🙏 Acknowledgments

* [Yahoo Finance](https://finance.yahoo.com) for free financial data
* [FastAPI](https://fastapi.tiangolo.com/) for the web framework
* [scikit-learn](https://scikit-learn.org/) for machine learning tools
* [yfinance](https://github.com/ranaroussi/yfinance) for data download

---

*Last updated: August 2025*

---

⭐ If this project helps you, please give it a star on GitHub!

