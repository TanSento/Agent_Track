# Cryptocurrency Investment Simulation

# Current prices of cryptocurrencies
bitcoin_price = 80957.16  # in USD
ethereum_price = 2376.64  # in USD
solana_price = 84.87  # in USD

# Investment amount
total_investment = 1500
amount_per_coin = total_investment / 3

# Calculate how many units of each coin can be bought
bitcoin_units = amount_per_coin / bitcoin_price
ethereum_units = amount_per_coin / ethereum_price
solana_units = amount_per_coin / solana_price

# Calculate values after a 15% pump
bitcoin_value_pump = bitcoin_units * bitcoin_price * 1.15
ethereum_value_pump = ethereum_units * ethereum_price * 1.15
solana_value_pump = solana_units * solana_price * 1.15

# Calculate values after a 40% dump
bitcoin_value_dump = bitcoin_units * bitcoin_price * 0.60
ethereum_value_dump = ethereum_units * ethereum_price * 0.60
solana_value_dump = solana_units * solana_price * 0.60

# Calculate net differences
bitcoin_net_difference = bitcoin_value_pump - bitcoin_value_dump
ethereum_net_difference = ethereum_value_pump - ethereum_value_dump
solana_net_difference = solana_value_pump - solana_value_dump

# Print results
print(bitcoin_units, ethereum_units, solana_units)
print(bitcoin_value_pump, ethereum_value_pump, solana_value_pump)
print(bitcoin_value_dump, ethereum_value_dump, solana_value_dump)
print(bitcoin_net_difference, ethereum_net_difference, solana_net_difference)