from transaction import Transaction

class Portfolio:
    def __init__(self):
        self.holdings = {}

    def buy(self, symbol, quantity):
        if quantity <= 0:
            raise ValueError("Quantity must be positive")
        symbol = symbol.upper()
        if symbol in self.holdings:
            self.holdings[symbol] += quantity
        else:
            self.holdings[symbol] = quantity

    def sell(self, symbol, quantity):
        if quantity <= 0:
            raise ValueError("Quantity must be positive")
        symbol = symbol.upper()
        current_quantity = self.holdings.get(symbol, 0)
        if current_quantity < quantity:
            raise ValueError(f"Insufficient shares: hold {current_quantity} of {symbol}, cannot sell {quantity}")
        self.holdings[symbol] -= quantity
        if self.holdings[symbol] == 0:
            del self.holdings[symbol]

    def get_holdings(self):
        return dict(self.holdings)

    def get_quantity(self, symbol):
        return self.holdings.get(symbol.upper(), 0)

    def has_sufficient_shares(self, symbol, quantity):
        return self.get_quantity(symbol) >= quantity

    def get_total_value(self, get_share_price):
        total = 0.0
        for symbol, quantity in self.holdings.items():
            price = get_share_price(symbol)
            total += price * quantity
        return total

    def rebuild_from_transactions(self, transactions):
        self.holdings = {}
        for transaction in transactions:
            if transaction.transaction_type == Transaction.BUY:
                self.buy(transaction.symbol, transaction.quantity)
            elif transaction.transaction_type == Transaction.SELL:
                self.sell(transaction.symbol, transaction.quantity)