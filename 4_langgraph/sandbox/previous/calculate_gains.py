bitcoin_price = 79741.72

gain_10_percent = round(bitcoin_price * 0.10, 2)
gain_20_percent = round(bitcoin_price * 0.20, 2)

results = f'Bitcoin price: {bitcoin_price}\n10% gain: {gain_10_percent}\n20% gain: {gain_20_percent}'

with open('results.txt', 'w') as file:
    file.write(results)
print('Results calculated and written to results.txt')