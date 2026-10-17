from datetime import date
import numpy as np
import yfinance as yf
from black_scholes import bs_call_price, implied_vol

TICKER = "AAPL"
R = 0.04  # interest rate

stock = yf.Ticker(TICKER)

# 1. Current price and historical volatility
hist = stock.history(period="1y")["Close"]
S = hist.iloc[-1]
daily_returns = np.log(hist / hist.shift(1)).dropna()
sigma = daily_returns.std() * np.sqrt(252)  # 252 trading days per year

# 2. Pick the first expiration at least 30 days away
expiry = next(e for e in stock.options
              if (date.fromisoformat(e) - date.today()).days >= 30)
T = (date.fromisoformat(expiry) - date.today()).days / 365

# 3. Get calls near the current price, use the bid/ask midpoint
calls = stock.option_chain(expiry).calls
calls = calls[(calls["bid"] > 0) & (calls["ask"] > 0)]
calls = calls[(calls["strike"] > S * 0.85) & (calls["strike"] < S * 1.15)].copy()
calls["market"] = (calls["bid"] + calls["ask"]) / 2

# 4. What Black-Scholes says, and the gap
calls["model"] = calls["strike"].apply(lambda K: bs_call_price(S, K, T, R, sigma))
calls["diff"] = calls["market"] - calls["model"]

calls["iv"] = calls.apply(
    lambda row: implied_vol(row["market"], S, row["strike"], T, R), axis=1
)

print(f"{TICKER} price: {S:.2f}   volatility: {sigma:.1%}   expiry: {expiry}")
# print(calls[["strike", "market", "model", "diff"]].round(2).to_string(index=False))
print(calls[["strike", "market", "model", "diff", "iv"]].round(3).to_string(index=False))