from account import Account
from portfolio import Portfolio
from portfolio_valuation import PortfolioValuation
from transaction import Transaction


class ReportingService:
    def __init__(self, account: Account, portfolio: Portfolio, portfolio_valuation: PortfolioValuation):
        self.account = account
        self.portfolio = portfolio
        self.portfolio_valuation = portfolio_valuation

    def holdings_report(self) -> str:
        holdings = self.portfolio.get_holdings()
        lines = ["=== Current Holdings ==="]
        if not holdings:
            lines.append("No shares currently held.")
        else:
            for symbol, quantity in holdings.items():
                lines.append(f"  {symbol}: {quantity} shares")
        cash_balance = self.account.get_balance()
        lines.append(f"Cash Balance: ${cash_balance:.2f}")
        total_value = self.portfolio_valuation.total_value()
        lines.append(f"Portfolio Market Value: ${total_value:.2f}")
        return "\n".join(lines)

    def profit_loss_report(self) -> str:
        profit_loss = self.portfolio_valuation.profit_or_loss()
        total_value = self.portfolio_valuation.total_value()
        cash_balance = self.account.get_balance()
        lines = ["=== Profit / Loss Report ==="]
        lines.append(f"Cash Balance: ${cash_balance:.2f}")
        lines.append(f"Portfolio Market Value: ${total_value:.2f}")
        direction = "Profit" if profit_loss >= 0 else "Loss"
        lines.append(f"{direction}: ${abs(profit_loss):.2f}")
        return "\n".join(lines)

    def transaction_history_report(self) -> str:
        transactions = self.account.get_transactions()
        lines = ["=== Transaction History ==="]
        if not transactions:
            lines.append("No transactions recorded.")
        else:
            for txn in transactions:
                lines.append(str(txn))
        return "\n".join(lines)

    def full_report(self) -> str:
        sections = [
            self.holdings_report(),
            self.profit_loss_report(),
            self.transaction_history_report(),
        ]
        return "\n\n".join(sections)