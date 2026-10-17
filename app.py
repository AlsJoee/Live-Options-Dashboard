from datetime import date
import numpy as np
import streamlit as st
import yfinance as yf
from black_scholes import bs_call_price, implied_vol

st.set_page_config(page_title="Options Dashboard", layout="wide")
st.title("Options Pricing Dashboard")
st.caption("Black-Scholes fair value vs. live market prices, with implied volatility from Yahoo Finance (yfinance) open source library.")

# ---- Inputs ----
POPULAR = ["AAPL", "TSLA", "NVDA", "MSFT", "AMZN", "GOOGL", "META", "SPY", "Other..."]

choice = st.selectbox("Ticker", POPULAR)
if choice == "Other...":
    ticker = st.text_input("Ticker symbol", value="", placeholder="Input ticker here").upper().strip()
    if not ticker:
        st.info("Type a ticker symbol above and press Enter.")
        st.stop()
else:
    ticker = choice

@st.cache_data(ttl=3600)
def get_risk_free_rate():
    """Current 13-week US Treasury bill yield, as a decimal."""
    try:
        irx = yf.Ticker("^IRX").history(period="5d")["Close"]
        return float(irx.iloc[-1]) / 100   # ^IRX is quoted in percent, e.g. 4.1
    except Exception:
        return 0.04                         # fallback if the fetch fails

r = st.number_input(
    "Risk-free rate (13-week T-bill, live)",
    value=get_risk_free_rate(),
    step=0.0025,
    format="%.4f",
)

# ---- Data (cached for 5 min so it doesn't refetch on every click) ----
@st.cache_data(ttl=300)
def get_history(ticker):
    return yf.Ticker(ticker).history(period="1y")["Close"]

@st.cache_data(ttl=300)
def get_expiries(ticker):
    return list(yf.Ticker(ticker).options)

@st.cache_data(ttl=300)
def get_calls(ticker, expiry):
    return yf.Ticker(ticker).option_chain(expiry).calls

hist = get_history(ticker)
if hist.empty:
    st.error(f"No data found for {ticker}")
    st.stop()

S = hist.iloc[-1]
daily_returns = np.log(hist / hist.shift(1)).dropna()
hist_vol = daily_returns.std() * np.sqrt(252)

# ---- Expiration picker (default: first one 30+ days out) ----
today = date.today()
expiries = [e for e in get_expiries(ticker) if (date.fromisoformat(e) - today).days >= 1]
if not expiries:
    st.error(f"No options listed for {ticker}")
    st.stop()
default = next((i for i, e in enumerate(expiries)
                if (date.fromisoformat(e) - today).days >= 30), 0)
expiry = st.selectbox("Expiration", expiries, index=default)
T = (date.fromisoformat(expiry) - today).days / 365

# ---- Build the table ----
calls = get_calls(ticker, expiry)
calls = calls[(calls["bid"] > 0) & (calls["ask"] > 0)]
calls = calls[(calls["strike"] > S * 0.85) & (calls["strike"] < S * 1.15)].copy()
calls["market"] = (calls["bid"] + calls["ask"]) / 2
calls["model"] = calls["strike"].apply(lambda K: bs_call_price(S, K, T, r, hist_vol))
calls["diff"] = calls["market"] - calls["model"]
calls["iv"] = calls.apply(lambda row: implied_vol(row["market"], S, row["strike"], T, r), axis=1)

# ---- Headline numbers ----
c1, c2, c3 = st.columns(3)
c1.metric("Stock price", f"${S:.2f}")
c2.metric("Historical volatility (1y)", f"{hist_vol:.1%}")
c3.metric("Median implied volatility", f"{calls['iv'].median():.1%}")

# ---- Charts ----
left, right = st.columns(2)
with left:
    st.subheader("Market price vs. Black-Scholes")
    st.line_chart(calls.set_index("strike")[["market", "model"]])
with right:
    st.subheader("Implied volatility by strike (the skew)")
    iv_chart = calls.set_index("strike")[["iv"]].copy()
    iv_chart["historical vol"] = hist_vol
    st.line_chart(iv_chart)

# ---- Raw table ----
st.subheader("All calls")
st.dataframe(calls[["strike", "bid", "ask", "market", "model", "diff", "iv"]].round(3),
             width="stretch", hide_index=True)