import yfinance as yf
import pandas as pd
import numpy as np
from statsmodels.tsa.arima.model import ARIMA
import matplotlib.pyplot as plt
from datetime import datetime, timedelta

# Step 1: Fetch historical gold price data (daily closes, last 5 years for robustness)
end_date = datetime.now()
start_date = end_date - timedelta(days=5*365)
gold_data = yf.download('GC=F', start=start_date, end=end_date, progress=False)
prices = gold_data['Close'].dropna()

print(f"Data fetched: {len(prices)} days from {prices.index[0].date()} to {prices.index[-1].date()}")
print(f"Latest price: ${prices.iloc[-1]:.2f}/oz")

# Step 2: Split into train/test (80/20)
split = int(0.8 * len(prices))
train = prices.iloc[:split]
test = prices.iloc[split:]

# Step 3: Fit ARIMA(3,1,2) on train data
model = ARIMA(train, order=(3, 1, 2))
fitted_model = model.fit()
print(fitted_model.summary())

# Step 4: Forecast on test set and compute accuracy
test_forecast = fitted_model.forecast(steps=len(test))
rmse = np.sqrt(np.mean((test - test_forecast)**2))
mape = np.mean(np.abs((test - test_forecast) / test)) * 100
print(f"Test RMSE: ${rmse:.2f}")
print(f"Test MAPE: {mape:.2f}%")

# Step 5: Forecast next 30 days
future_days = 30
future_forecast = fitted_model.forecast(steps=future_days)
future_index = pd.date_range(start=prices.index[-1] + timedelta(days=1), periods=future_days, freq='B')  # Business days
future_df = pd.DataFrame({'Forecast': future_forecast}, index=future_index)

print("\nNext 30-day Gold Price Forecast (USD/oz):")
print(future_df.head(10))  # Show first 10 for brevity

# Step 6: Plot actual vs forecast (historical + test + future)
plt.figure(figsize=(12, 6))
plt.plot(prices.index, prices, label='Actual', color='gold')
plt.plot(test.index, test_forecast, label='Test Forecast', color='orange', linestyle='--')
plt.plot(future_df.index, future_df['Forecast'], label='Future Forecast', color='red', linestyle='--')
plt.title('Gold Price Prediction with ARIMA(3,1,2)')
plt.xlabel('Date')
plt.ylabel('Price (USD/oz)')
plt.legend()
plt.grid(True)
plt.show()