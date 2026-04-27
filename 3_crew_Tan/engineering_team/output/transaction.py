from datetime import datetime


class Transaction:
    """
    Represents a single account event such as a deposit, withdrawal,
    share purchase, or share sale.
    """

    TRANSACTION_TYPES = {"deposit", "withdrawal", "buy", "sell"}

    def __init__(self, transaction_type: str, amount: float = 0.0,
                 symbol: str = None, quantity: float = 0.0,
                 price: float = 0.0, timestamp: datetime = None):
        """
        Initialize a Transaction instance.

        :param transaction_type: Type of transaction ('deposit', 'withdrawal', 'buy', 'sell')
        :param amount: The monetary amount involved in the transaction (for deposits/withdrawals)
        :param symbol: The stock ticker symbol (applicable for 'buy' and 'sell' transactions)
        :param quantity: The number of shares involved (applicable for 'buy' and 'sell' transactions)
        :param price: The price per share at time of transaction
        :param timestamp: The datetime when the transaction occurred; defaults to now if not provided
        """
        if transaction_type not in self.TRANSACTION_TYPES:
            raise ValueError(
                f"Invalid transaction type '{transaction_type}'. "
                f"Must be one of: {self.TRANSACTION_TYPES}"
            )

        self.transaction_type = transaction_type
        self.amount = amount
        self.symbol = symbol
        self.quantity = quantity
        self.price = price
        self.timestamp = timestamp if timestamp is not None else datetime.now()

    def __repr__(self):
        return (
            f"Transaction("
            f"type={self.transaction_type!r}, "
            f"amount={self.amount}, "
            f"symbol={self.symbol!r}, "
            f"quantity={self.quantity}, "
            f"price={self.price}, "
            f"timestamp={self.timestamp!r})"
        )

    def __str__(self):
        if self.transaction_type in ("deposit", "withdrawal"):
            return (
                f"[{self.timestamp}] {self.transaction_type.capitalize()}: "
                f"${self.amount:.2f}"
            )
        else:
            action = "Bought" if self.transaction_type == "buy" else "Sold"
            return (
                f"[{self.timestamp}] {action} {self.quantity} share(s) of "
                f"{self.symbol} at ${self.price:.2f} each "
                f"(Total: ${self.quantity * self.price:.2f})"
            )