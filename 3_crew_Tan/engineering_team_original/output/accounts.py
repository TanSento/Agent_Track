"""
accounts.py - A simple account management system for a trading simulation platform.
"""

from datetime import datetime


class InsufficientFundsError(Exception):
    """Raised when there are insufficient funds for a withdrawal or purchase."""
    pass


class InsufficientSharesError(Exception):
    """Raised when there are insufficient shares for a sale."""
    pass


def get_share_price(symbol: str) -> float:
    """
    Test implementation providing fixed share prices for AAPL, TSLA, GOOGL.
    Returns the current price of a share for the given symbol.
    
    Args:
        symbol: The stock ticker symbol.
        
    Returns:
        The current price of the share.
        
    Raises:
        ValueError: If the symbol is not recognized.
    """
    prices = {
        'AAPL': 150.00,
        'TSLA': 250.00,
        'GOOGL': 2800.00
    }
    
    symbol = symbol.upper()
    if symbol not in prices:
        raise ValueError(f"Unknown symbol: {symbol}. Available symbols: {', '.join(prices.keys())}")
    
    return prices[symbol]


class Account:
    """
    Represents a user's account in the trading simulation platform.
    Maintains the user's balance, transactions, and portfolio holdings.
    """
    
    def __init__(self, initial_deposit: float) -> None:
        """
        Initializes a new account with a specified initial deposit.
        
        Args:
            initial_deposit: The initial amount to deposit into the account.
            
        Raises:
            ValueError: If the initial deposit is negative.
        """
        if initial_deposit < 0:
            raise ValueError("Initial deposit cannot be negative.")
        
        self._balance = initial_deposit
        self._initial_deposit = initial_deposit
        self._holdings = {}  # symbol -> quantity
        self._transactions = []
        
        if initial_deposit > 0:
            self._record_transaction('deposit', amount=initial_deposit)
    
    def _record_transaction(self, transaction_type: str, **kwargs) -> None:
        """
        Records a transaction with a timestamp.
        
        Args:
            transaction_type: The type of transaction (deposit, withdrawal, buy, sell).
            **kwargs: Additional transaction details.
        """
        transaction = {
            'type': transaction_type,
            'timestamp': datetime.now().isoformat(),
            **kwargs
        }
        self._transactions.append(transaction)
    
    def deposit(self, amount: float) -> None:
        """
        Adds the specified amount to the user's balance.
        
        Args:
            amount: The amount to deposit.
            
        Raises:
            ValueError: If the deposit amount is negative.
        """
        if amount < 0:
            raise ValueError("Deposit amount cannot be negative.")
        
        self._balance += amount
        self._record_transaction('deposit', amount=amount)
    
    def withdraw(self, amount: float) -> None:
        """
        Deducts the specified amount from the user's balance.
        
        Args:
            amount: The amount to withdraw.
            
        Raises:
            ValueError: If the withdrawal amount is negative.
            InsufficientFundsError: If the amount exceeds the current balance.
        """
        if amount < 0:
            raise ValueError("Withdrawal amount cannot be negative.")
        
        if amount > self._balance:
            raise InsufficientFundsError(
                f"Insufficient funds. Requested: ${amount:.2f}, Available: ${self._balance:.2f}"
            )
        
        self._balance -= amount
        self._record_transaction('withdrawal', amount=amount)
    
    def get_balance(self) -> float:
        """
        Returns the current balance in the account.
        
        Returns:
            The current account balance.
        """
        return self._balance
    
    def buy_shares(self, symbol: str, quantity: int) -> None:
        """
        Records the purchase of the specified quantity of shares at the current price.
        
        Args:
            symbol: The stock ticker symbol.
            quantity: The number of shares to buy.
            
        Raises:
            ValueError: If the quantity is not positive.
            InsufficientFundsError: If the total purchase price exceeds the available balance.
        """
        if quantity <= 0:
            raise ValueError("Quantity must be a positive integer.")
        
        symbol = symbol.upper()
        price = get_share_price(symbol)
        total_cost = price * quantity
        
        if total_cost > self._balance:
            raise InsufficientFundsError(
                f"Insufficient funds to buy {quantity} shares of {symbol}. "
                f"Cost: ${total_cost:.2f}, Available: ${self._balance:.2f}"
            )
        
        self._balance -= total_cost
        self._holdings[symbol] = self._holdings.get(symbol, 0) + quantity
        
        self._record_transaction(
            'buy',
            symbol=symbol,
            quantity=quantity,
            price=price,
            total_cost=total_cost
        )
    
    def sell_shares(self, symbol: str, quantity: int) -> None:
        """
        Records the sale of the specified quantity of shares at the current price.
        
        Args:
            symbol: The stock ticker symbol.
            quantity: The number of shares to sell.
            
        Raises:
            ValueError: If the quantity is not positive.
            InsufficientSharesError: If the user tries to sell more shares than they own.
        """
        if quantity <= 0:
            raise ValueError("Quantity must be a positive integer.")
        
        symbol = symbol.upper()
        current_holdings = self._holdings.get(symbol, 0)
        
        if quantity > current_holdings:
            raise InsufficientSharesError(
                f"Insufficient shares to sell. Requested: {quantity}, "
                f"Available: {current_holdings} shares of {symbol}"
            )
        
        price = get_share_price(symbol)
        total_proceeds = price * quantity
        
        self._balance += total_proceeds
        self._holdings[symbol] -= quantity
        
        if self._holdings[symbol] == 0:
            del self._holdings[symbol]
        
        self._record_transaction(
            'sell',
            symbol=symbol,
            quantity=quantity,
            price=price,
            total_proceeds=total_proceeds
        )
    
    def calculate_portfolio_value(self) -> float:
        """
        Returns the total value of the portfolio based on current share prices.
        
        Returns:
            The total value of all shares currently held.
        """
        total_value = 0.0
        for symbol, quantity in self._holdings.items():
            price = get_share_price(symbol)
            total_value += price * quantity
        return total_value
    
    def calculate_profit_loss(self) -> float:
        """
        Calculates and returns the profit or loss since the initial deposit.
        
        Returns:
            The profit or loss amount. Positive means profit, negative means loss.
        """
        total_deposited = sum(
            t['amount'] for t in self._transactions if t['type'] == 'deposit'
        )
        total_withdrawn = sum(
            t['amount'] for t in self._transactions if t['type'] == 'withdrawal'
        )
        
        current_total_value = self._balance + self.calculate_portfolio_value()
        net_invested = total_deposited - total_withdrawn
        
        return current_total_value - net_invested
    
    def get_holdings(self) -> dict:
        """
        Returns a dictionary of shares owned by the user and their quantities.
        
        Returns:
            A dictionary mapping stock symbols to quantities held.
        """
        return dict(self._holdings)
    
    def get_transactions(self) -> list:
        """
        Returns a list of all transactions made by the user.
        
        Returns:
            A list of transaction dictionaries.
        """
        return list(self._transactions)
    
    def get_profit_loss(self) -> dict:
        """
        Returns a report of the profit or loss value and percentage since the initial deposit.
        
        Returns:
            A dictionary containing:
                - profit_loss: The absolute profit or loss amount.
                - profit_loss_percentage: The percentage profit or loss relative to total deposited.
                - current_total_value: The current total value (balance + portfolio).
                - total_deposited: The total amount deposited.
                - total_withdrawn: The total amount withdrawn.
                - net_invested: The net amount invested (deposited - withdrawn).
        """
        total_deposited = sum(
            t['amount'] for t in self._transactions if t['type'] == 'deposit'
        )
        total_withdrawn = sum(
            t['amount'] for t in self._transactions if t['type'] == 'withdrawal'
        )
        
        net_invested = total_deposited - total_withdrawn
        current_total_value = self._balance + self.calculate_portfolio_value()
        profit_loss = current_total_value - net_invested
        
        if net_invested != 0:
            profit_loss_percentage = (profit_loss / net_invested) * 100
        else:
            profit_loss_percentage = 0.0
        
        return {
            'profit_loss': profit_loss,
            'profit_loss_percentage': profit_loss_percentage,
            'current_total_value': current_total_value,
            'total_deposited': total_deposited,
            'total_withdrawn': total_withdrawn,
            'net_invested': net_invested
        }


if __name__ == '__main__':
    # Simple demonstration of the account management system
    print("=== Trading Simulation Account Demo ===\n")
    
    # Create an account with initial deposit
    account = Account(10000.00)
    print(f"Account created with initial deposit: ${account.get_balance():.2f}")
    
    # Deposit more funds
    account.deposit(5000.00)
    print(f"After depositing $5000: ${account.get_balance():.2f}")
    
    # Buy some shares
    print("\n--- Buying Shares ---")
    account.buy_shares('AAPL', 10)
    print(f"Bought 10 AAPL shares @ ${get_share_price('AAPL'):.2f} each")
    print(f"Balance after purchase: ${account.get_balance():.2f}")
    
    account.buy_shares('TSLA', 5)
    print(f"Bought 5 TSLA shares @ ${get_share_price('TSLA'):.2f} each")
    print(f"Balance after purchase: ${account.get_balance():.2f}")
    
    account.buy_shares('GOOGL', 2)
    print(f"Bought 2 GOOGL shares @ ${get_share_price('GOOGL'):.2f} each")
    print(f"Balance after purchase: ${account.get_balance():.2f}")
    
    # Display holdings
    print("\n--- Current Holdings ---")
    holdings = account.get_holdings()
    for symbol, quantity in holdings.items():
        price = get_share_price(symbol)
        print(f"  {symbol}: {quantity} shares @ ${price:.2f} = ${price * quantity:.2f}")
    
    print(f"\nPortfolio Value: ${account.calculate_portfolio_value():.2f}")
    print(f"Cash Balance: ${account.get_balance():.2f}")
    print(f"Total Value: ${account.get_balance() + account.calculate_portfolio_value():.2f}")
    
    # Sell some shares
    print("\n--- Selling Shares ---")
    account.sell_shares('AAPL', 5)
    print(f"Sold 5 AAPL shares @ ${get_share_price('AAPL'):.2f} each")
    print(f"Balance after sale: ${account.get_balance():.2f}")
    
    # Withdraw funds
    account.withdraw(1000.00)
    print(f"\nWithdrew $1000. New balance: ${account.get_balance():.2f}")
    
    # Profit/Loss Report
    print("\n--- Profit/Loss Report ---")
    pl_report = account.get_profit_loss()
    print(f"Total Deposited: ${pl_report['total_deposited']:.2f}")
    print(f"Total Withdrawn: ${pl_report['total_withdrawn']:.2f}")
    print(f"Net Invested: ${pl_report['net_invested']:.2f}")
    print(f"Current Total Value: ${pl_report['current_total_value']:.2f}")
    print(f"Profit/Loss: ${pl_report['profit_loss']:.2f} ({pl_report['profit_loss_percentage']:.2f}%)")
    
    # List all transactions
    print("\n--- Transaction History ---")
    transactions = account.get_transactions()
    for i, txn in enumerate(transactions, 1):
        print(f"  {i}. [{txn['timestamp']}] {txn['type'].upper()}", end="")
        if 'amount' in txn:
            print(f" - Amount: ${txn['amount']:.2f}", end="")
        if 'symbol' in txn:
            print(f" - {txn['symbol']}", end="")
        if 'quantity' in txn:
            print(f" x {txn['quantity']}", end="")
        if 'price' in txn:
            print(f" @ ${txn['price']:.2f}", end="")
        print()
    
    # Demonstrate error handling
    print("\n--- Error Handling Demo ---")
    
    try:
        account.withdraw(999999.00)
    except InsufficientFundsError as e:
        print(f"InsufficientFundsError caught: {e}")
    
    try:
        account.sell_shares('TSLA', 100)
    except InsufficientSharesError as e:
        print(f"InsufficientSharesError caught: {e}")
    
    try:
        account.buy_shares('GOOGL', 1000)
    except InsufficientFundsError as e:
        print(f"InsufficientFundsError caught: {e}")
    
    try:
        account.deposit(-500)
    except ValueError as e:
        print(f"ValueError caught: {e}")
    
    try:
        bad_account = Account(-100)
    except ValueError as e:
        print(f"ValueError caught: {e}")