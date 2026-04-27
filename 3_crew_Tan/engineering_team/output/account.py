from transaction import Transaction
from portfolio import Portfolio


class Account:
    def __init__(self, initial_deposit: float = 0.0):
        self.balance = 0.0
        self.initial_deposit = 0.0
        self.transactions = []
        self.portfolio = Portfolio()

        if initial_deposit > 0:
            self.deposit(initial_deposit)
            self.initial_deposit = initial_deposit

    def deposit(self, amount: float):
        if amount <= 0:
            raise ValueError("Deposit amount must be positive.")
        self.balance += amount
        transaction = Transaction(transaction_type="deposit", amount=amount)
        self.transactions.append(transaction)

    def withdraw(self, amount: float):
        if amount <= 0:
            raise ValueError("Withdrawal amount must be positive.")
        if amount > self.balance:
            raise ValueError("Insufficient funds: withdrawal would result in a negative balance.")
        self.balance -= amount
        transaction = Transaction(transaction_type="withdrawal", amount=amount)
        self.transactions.append(transaction)

    def buy_shares(self, symbol: str, quantity: int, get_share_price):
        if quantity <= 0:
            raise ValueError("Quantity must be positive.")
        price = get_share_price(symbol)
        total_cost = price * quantity
        if total_cost > self.balance:
            raise ValueError(f"Insufficient funds to buy {quantity} shares of {symbol}.")
        self.balance -= total_cost
        self.portfolio.add_shares(symbol, quantity)
        transaction = Transaction(
            transaction_type="buy",
            symbol=symbol,
            quantity=quantity,
            price=price,
            amount=total_cost
        )
        self.transactions.append(transaction)

    def sell_shares(self, symbol: str, quantity: int, get_share_price):
        if quantity <= 0:
            raise ValueError("Quantity must be positive.")
        if not self.portfolio.has_shares(symbol, quantity):
            raise ValueError(f"Insufficient shares: cannot sell {quantity} shares of {symbol}.")
        price = get_share_price(symbol)
        total_value = price * quantity
        self.balance += total_value
        self.portfolio.remove_shares(symbol, quantity)
        transaction = Transaction(
            transaction_type="sell",
            symbol=symbol,
            quantity=quantity,
            price=price,
            amount=total_value
        )
        self.transactions.append(transaction)

    def get_holdings(self):
        return self.portfolio.get_holdings()

    def get_portfolio_value(self, get_share_price):
        return self.portfolio.get_total_value(get_share_price)

    def get_total_value(self, get_share_price):
        return self.balance + self.get_portfolio_value(get_share_price)

    def get_profit_loss(self, get_share_price):
        return self.get_total_value(get_share_price) - self.initial_deposit

    def get_transactions(self):
        return list(self.transactions)