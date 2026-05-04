# Investment simulation script

total_investment = 1000  # total investment amount in USD

# Top 10 coins and their prices
coins = {
    'Bitcoin': 78355.49,
    'Ethereum': 2308.71,
    'Tether': 0.9998,
    'XRP': 1.38,
    'BNB': 617.15,
    'USDC': 0.9997,
    'Solana': 83.93,
    'TRON': 0.3369,
    'Dogecoin': 0.1080,
    'Hyperliquid': 40.99
}

# Split investment equally
investment_per_coin = total_investment / len(coins)

# Simulation results
results = []
for coin, price in coins.items():
    coins_held = investment_per_coin / price  # coins purchased
    value_after_pump = coins_held * price * 1.2  # assuming a 20% increase
    results.append({
        'Coin': coin,
        'Entry Price': price,
        'Coins Held': coins_held,
        'Value After 20% Pump': value_after_pump
    })

# Output results
for result in results:
    print(result)