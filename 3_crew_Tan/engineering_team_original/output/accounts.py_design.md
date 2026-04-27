```markdown
# accounts.py Module Design

## Overview

The `accounts.py` module provides functionality for managing trading simulation accounts. It includes features for creating accounts, depositing and withdrawing funds, recording trades, calculating portfolio value, and reporting profit or loss. The system enforces rules to prevent unauthorized financial actions.

## Classes and Methods

### Class: Account

This class represents a user's account in the trading simulation platform. It maintains the user's balance, transactions, and portfolio holdings.

#### Constructor
- `__init__(self, initial_deposit: float) -> None`
  - Initializes a new account with a specified initial deposit.
  - Raises an error if the initial deposit is negative.

#### Account Management Methods
- `deposit(self, amount: float) -> None`
  - Adds the specified amount to the user's balance.
  - Raises an error if the deposit amount is negative.

- `withdraw(self, amount: float) -> None`
  - Deducts the specified amount from the user's balance.
  - Raises an error if the amount exceeds the current balance.

- `get_balance(self) -> float`
  - Returns the current balance in the account.

#### Trading Methods
- `buy_shares(self, symbol: str, quantity: int) -> None`
  - Records the purchase of the specified quantity of shares at the current price.
  - Raises an error if the total purchase price exceeds the available balance.

- `sell_shares(self, symbol: str, quantity: int) -> None`
  - Records the sale of the specified quantity of shares at the current price.
  - Raises an error if the user tries to sell more shares than they own.

#### Portfolio and Profit Calculation Methods
- `calculate_portfolio_value(self) -> float`
  - Returns the total value of the portfolio based on current share prices.

- `calculate_profit_loss(self) -> float`
  - Calculates and returns the profit or loss since the initial deposit.

#### Reporting Methods
- `get_holdings(self) -> dict`
  - Returns a dictionary of shares owned by the user and their quantities.

- `get_transactions(self) -> list`
  - Returns a list of all transactions (buys, sells, deposits, withdrawals) made by the user.

- `get_profit_loss(self) -> dict`
  - Returns a report of the profit or loss value and percentage since the initial deposit.

### Helper Functions

- `get_share_price(symbol: str) -> float`
  - Test implementation providing fixed share prices for AAPL, TSLA, GOOGL.
  - Should be used for simulating getting the current market price of a given share symbol.

## Error Handling

The module should define a custom exception class `InsufficientFundsError` to be raised when attempts are made to withdraw more funds than available or make purchases that cannot be covered by the account balance.

The module should also define a custom exception class `InsufficientSharesError` to be raised when attempts are made to sell more shares than held. 

```