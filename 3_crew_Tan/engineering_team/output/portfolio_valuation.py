from portfolio import Portfolio
from account import Account
from share_price_service import SharePriceService


class PortfolioValuation:
    def __init__(self, account: Account, portfolio: Portfolio, share_price_service: SharePriceService):
        self.account = account
        self.portfolio = portfolio
        self.share_price_service = share_price_service

    def calculate_portfolio_value(self) -> float:
        total_value = 0.0
        holdings = self.portfolio.get_holdings()
        for symbol, quantity in holdings.items():
            if quantity > 0:
                price = self.share_price_service.get_share_price(symbol)
                total_value += price * quantity
        return total_value

    def calculate_total_value(self) -> float:
        portfolio_value = self.calculate_portfolio_value()
        cash_balance = self.account.get_balance()
        return portfolio_value + cash_balance

    def calculate_profit_or_loss(self) -> float:
        total_value = self.calculate_total_value()
        initial_deposit = self.account.get_initial_deposit()
        return total_value - initial_deposit