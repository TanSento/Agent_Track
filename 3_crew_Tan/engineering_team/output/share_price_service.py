def get_share_price(symbol):
    """Test implementation that returns fixed prices for known symbols."""
    fixed_prices = {
        "AAPL": 150.00,
        "TSLA": 700.00,
        "GOOGL": 2800.00,
    }
    if symbol not in fixed_prices:
        raise ValueError(f"Unknown symbol: {symbol}")
    return fixed_prices[symbol]


class SharePriceService:
    """Provides share price lookup functionality.
    
    Wraps a get_share_price(symbol) function and acts as the single
    source of truth for current share prices in the system.
    """

    def __init__(self, price_function=None):
        """Initialize the SharePriceService.
        
        Args:
            price_function: A callable that takes a symbol string and returns
                            the current price. Defaults to the test implementation
                            with fixed prices for AAPL, TSLA, and GOOGL.
        """
        if price_function is None:
            self._get_share_price = get_share_price
        else:
            self._get_share_price = price_function

    def get_price(self, symbol):
        """Get the current price for a given share symbol.
        
        Args:
            symbol: The stock ticker symbol (e.g., 'AAPL', 'TSLA', 'GOOGL').
        
        Returns:
            The current price of the share as a float.
        
        Raises:
            ValueError: If the symbol is not recognized by the price function.
        """
        return self._get_share_price(symbol)