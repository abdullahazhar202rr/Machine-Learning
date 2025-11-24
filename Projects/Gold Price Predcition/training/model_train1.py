import numpy as np
import pandas as pd
import yfinance as yf
from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics import mean_absolute_percentage_error
from keras import Model
from keras.layers import Input, Dense, Dropout, LSTM

# Fetch latest gold price data automatically (GLD ETF tracks gold closely)
df = yf.download('GLD', start='2013-01-01')['Close'].reset_index()
df.rename(columns={'Date': 'Date', 'Close': 'Price'}, inplace=True)
df['Date'] = pd.to_datetime(df['Date'])
df.sort_values(by='Date', ascending=True, inplace=True)
df.reset_index(drop=True, inplace=True)

# Prepare data
NumCols = df.columns.drop(['Date'])
df[NumCols] = df[NumCols].astype('float64')

# Test set: 2024 data (adjust year if needed for future runs)
test_start = '2024-01-01'
test_mask = df['Date'] >= pd.to_datetime(test_start)
test_size = test_mask.sum()
print(f"Training on data up to 2023; testing on {test_size} days in 2024.")

scaler = MinMaxScaler()
scaler.fit(df.Price.values.reshape(-1, 1))

window_size = 60
train_data = df.Price[~test_mask]
train_data = scaler.transform(train_data.values.reshape(-1, 1))

X_train = []
y_train = []
for i in range(window_size, len(train_data)):
    X_train.append(train_data[i - 60:i, 0])
    y_train.append(train_data[i, 0])

# For test, include window from end of train
train_end_idx = len(train_data)
test_data_full_start = train_end_idx - window_size
test_data_full = df.Price.iloc[test_data_full_start:]
test_data_full = scaler.transform(test_data_full.values.reshape(-1, 1))

X_test = []
y_test = []
for i in range(window_size, len(test_data_full)):
    X_test.append(test_data_full[i - 60:i, 0])
    y_test.append(test_data_full[i, 0])

X_train = np.array(X_train)
X_test = np.array(X_test)
y_train = np.array(y_train)
y_test = np.array(y_test)

X_train = np.reshape(X_train, (X_train.shape[0], X_train.shape[1], 1))
X_test = np.reshape(X_test, (X_test.shape[0], X_test.shape[1], 1))
y_train = np.reshape(y_train, (-1, 1))
y_test = np.reshape(y_test, (-1, 1))

def define_model():
    input1 = Input(shape=(window_size, 1))
    x = LSTM(units=64, return_sequences=True)(input1)
    x = Dropout(0.2)(x)
    x = LSTM(units=64, return_sequences=True)(x)
    x = Dropout(0.2)(x)
    x = LSTM(units=64)(x)
    x = Dropout(0.2)(x)
    x = Dense(32, activation='relu')(x)  # Fixed: relu for regression
    dnn_output = Dense(1)(x)
    model = Model(inputs=input1, outputs=[dnn_output])
    model.compile(loss='mean_squared_error', optimizer='Nadam')
    return model

model = define_model()
history = model.fit(X_train, y_train, epochs=200, batch_size=32, validation_split=0.1, verbose=0)  # Increased epochs

result = model.evaluate(X_test, y_test, verbose=0)
y_pred = model.predict(X_test, verbose=0)
MAPE = mean_absolute_percentage_error(y_test, y_pred)
Accuracy = 1 - MAPE
print(f"Model Accuracy: {Accuracy * 100:.2f}%")