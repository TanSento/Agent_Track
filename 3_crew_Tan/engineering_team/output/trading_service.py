from account import Account
from portfolio import Portfolio
from share_price_service import SharePriceService
from transaction import Transaction


class TradingService:
    def __init__(self, account: Account, portfolio: Portfolio, share_price_service: SharePriceService):
        self.account = account
        self.portfolio = portfolio
        self.share_price_service = share_price_service

    def buy_shares(self, symbol: str, quantity: int) -> Transaction:
        if quantity <= 0:
            raise ValueError("Quantity must be positive")
        
        price = self.share_price_service.get_price(symbol)
        total_cost = price * quantity
        
        if self.account.balance < total_cost:
            raise ValueError(
                f"Insufficient funds: need {total_cost:.2f} but have {self.account.balance:.2f}"
            )
        
        self.account.withdraw(total_cost)
        self.portfolio.add_shares(symbol, quantity, price)
        
        transaction = Transaction(
            transaction_type="BUY",
            symbol=symbol,
            quantity=quantity,
            price=price
        )
        self.account.add_transaction(transaction)
        
        return transaction

    def sell_shares(self, symbol: str, quantity: int) -> Transaction:
        if quantity <= 0:
            raise ValueError("Quantity must be positive")
        
        current_holding = self.portfolio.get_quantity(symbol)
        if current_holding < quantity:
            raise ValueError(
                f"Insufficient shares: need {quantity} but have {current_holding}"
            )
        
        price = self.share_price_service.get_price(symbol)
        total_proceeds = price * quantity
        
        self.portfolio.remove_shares(symbol, quantity)
        self.account.deposit(total_proceeds)
        
        transaction = Transaction(
            transaction_type="SELL",
            symbol=symbol,
            quantity=quantity,
            price=price
        )
        self.account.add_transaction(transaction)
        
        return transaction