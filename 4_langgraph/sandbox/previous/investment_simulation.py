# Investment simulation script

# Investment amount
investment_amount = 1000.0

# Current prices
price_bitcoin = 81116.00
price_ethereum = 2386.99

# Splitting the investment
investment_per_coin = investment_amount / 2

# Amount of Bitcoin and Ethereum bought
amount_bitcoin = investment_per_coin / price_bitcoin
amount_ethereum = investment_per_coin / price_ethereum

# New prices after a 20% increase
new_price_bitcoin = price_bitcoin * 1.20
new_price_ethereum = price_ethereum * 1.20

# Value of each position after the increase
value_bitcoin = amount_bitcoin * new_price_bitcoin
value_ethereum = amount_ethereum * new_price_ethereum

print(value_bitcoin, value_ethereum)