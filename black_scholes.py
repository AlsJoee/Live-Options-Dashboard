import math

def norm_cdf(x):
    """Probability that a standard normal random number is below x."""
    return 0.5 * (1 + math.erf(x / math.sqrt(2)))

def bs_call_price(S, K, T, r, sigma):
    """Fair price of a call option using Black-Scholes."""
    if T <= 0:
        return max(S - K, 0.0)  # expired: just intrinsic value

    d1 = (math.log(S / K) + (r + sigma**2 / 2) * T) / (sigma * math.sqrt(T))
    d2 = d1 - sigma * math.sqrt(T)
    return S * norm_cdf(d1) - K * math.exp(-r * T) * norm_cdf(d2)

def implied_vol(market_price, S, K, T, r, low=0.01, high=3.0, tol=1e-6):
    """Find the sigma that makes Black-Scholes match the market price (binary search)."""
    for _ in range(100):
        mid = (low + high) / 2
        price = bs_call_price(S, K, T, r, mid)
        if abs(price - market_price) < tol:
            return mid
        if price > market_price:
            high = mid   # guess too high, search lower half
        else:
            low = mid    # guess too low, search upper half
    return mid

if __name__ == "__main__":
    print(round(bs_call_price(S=100, K=100, T=1, r=0.05, sigma=0.2), 2))