import pytest
from unittest.mock import MagicMock, patch, call
from trading_service import TradingService


@pytest.fixture
def mock_account():
    account = MagicMock()
    account.balance = 10000.0
    return account


@pytest.fixture
def mock_portfolio():
    portfolio = MagicMock()
    return portfolio


@pytest.fixture
def mock_share_price_service():
    service = MagicMock()
    return service


@pytest.fixture
def trading_service(mock_account, mock_portfolio, mock_share_price_service):
    return TradingService(mock_account, mock_portfolio, mock_share_price_service)


class TestTradingServiceInit:
    def test_trading_service_stores_account(self, trading_service, mock_account):
        assert trading_service.account is mock_account

    def test_trading_service_stores_portfolio(self, trading_service, mock_portfolio):
        assert trading_service.portfolio is mock_portfolio

    def test_trading_service_stores_share_price_service(self, trading_service, mock_share_price_service):
        assert trading_service.share_price_service is mock_share_price_service


class TestBuyShares:
    def test_buy_shares_returns_transaction(self, trading_service, mock_account, mock_share_price_service):
        mock_share_price_service.get_price.return_value = 100.0
        mock_account.balance = 10000.0

        transaction = trading_service.buy_shares("AAPL", 10)

        assert transaction is not None

    def test_buy_shares_transaction_type_is_buy(self, trading_service, mock_account, mock_share_price_service):
        mock_share_price_service.get_price.return_value = 100.0
        mock_account.balance = 10000.0

        transaction = trading_service.buy_shares("AAPL", 10)

        assert transaction.transaction_type == "BUY"

    def test_buy_shares_transaction_has_correct_symbol(self, trading_service, mock_account, mock_share_price_service):
        mock_share_price_service.get_price.return_value = 100.0
        mock_account.balance = 10000.0

        transaction = trading_service.buy_shares("AAPL", 10)

        assert transaction.symbol == "AAPL"

    def test_buy_shares_transaction_has_correct_quantity(self, trading_service, mock_account, mock_share_price_service):
        mock_share_price_service.get_price.return_value = 100.0
        mock_account.balance = 10000.0

        transaction = trading_service.buy_shares("AAPL", 10)

        assert transaction.quantity == 10

    def test_buy_shares_transaction_has_correct_price(self, trading_service, mock_account, mock_share_price_service):
        mock_share_price_service.get_price.return_value = 100.0
        mock_account.balance = 10000.0

        transaction = trading_service.buy_shares("AAPL", 10)

        assert transaction.price == 100.0

    def test_buy_shares_calls_get_price_with_symbol(self, trading_service, mock_account, mock_share_price_service):
        mock_share_price_service.get_price.return_value = 50.0
        mock_account.balance = 5000.0

        trading_service.buy_shares("TSLA", 10)

        mock_share_price_service.get_price.assert_called_once_with("TSLA")

    def test_buy_shares_calls_account_withdraw_with_total_cost(self, trading_service, mock_account, mock_share_price_service):
        mock_share_price_service.get_price.return_value = 100.0
        mock_account.balance = 10000.0

        trading_service.buy_shares("AAPL", 10)

        mock_account.withdraw.assert_called_once_with(1000.0)

    def test_buy_shares_calls_portfolio_add_shares(self, trading_service, mock_account, mock_portfolio, mock_share_price_service):
        mock_share_price_service.get_price.return_value = 100.0
        mock_account.balance = 10000.0

        trading_service.buy_shares("AAPL", 10)

        mock_portfolio.add_shares.assert_called_once_with("AAPL", 10, 100.0)

    def test_buy_shares_adds_transaction_to_account(self, trading_service, mock_account, mock_share_price_service):
        mock_share_price_service.get_price.return_value = 100.0
        mock_account.balance = 10000.0

        transaction = trading_service.buy_shares("AAPL", 10)

        mock_account.add_transaction.assert_called_once_with(transaction)

    def test_buy_shares_raises_value_error_for_zero_quantity(self, trading_service):
        with pytest.raises(ValueError) as exc_info:
            trading_service.buy_shares("AAPL", 0)

        assert "Quantity must be positive" in str(exc_info.value)

    def test_buy_shares_raises_value_error_for_negative_quantity(self, trading_service):
        with pytest.raises(ValueError) as exc_info:
            trading_service.buy_shares("AAPL", -5)

        assert "Quantity must be positive" in str(exc_info.value)

    def test_buy_shares_raises_value_error_for_insufficient_funds(self, trading_service, mock_account, mock_share_price_service):
        mock_share_price_service.get_price.return_value = 100.0
        mock_account.balance = 500.0

        with pytest.raises(ValueError) as exc_info:
            trading_service.buy_shares("AAPL", 10)

        assert "Insufficient funds" in str(exc_info.value)

    def test_buy_shares_insufficient_funds_message_contains_needed_amount(self, trading_service, mock_account, mock_share_price_service):
        mock_share_price_service.get_price.return_value = 100.0
        mock_account.balance = 500.0

        with pytest.raises(ValueError) as exc_info:
            trading_service.buy_shares("AAPL", 10)

        assert "1000.00" in str(exc_info.value)

    def test_buy_shares_insufficient_funds_message_contains_available_amount(self, trading_service, mock_account, mock_share_price_service):
        mock_share_price_service.get_price.return_value = 100.0
        mock_account.balance = 500.0

        with pytest.raises(ValueError) as exc_info:
            trading_service.buy_shares("AAPL", 10)

        assert "500.00" in str(exc_info.value)

    def test_buy_shares_does_not_withdraw_when_insufficient_funds(self, trading_service, mock_account, mock_share_price_service):
        mock_share_price_service.get_price.return_value = 100.0
        mock_account.balance = 500.0

        with pytest.raises(ValueError):
            trading_service.buy_shares("AAPL", 10)

        mock_account.withdraw.assert_not_called()

    def test_buy_shares_does_not_add_shares_when_insufficient_funds(self, trading_service, mock_account, mock_portfolio, mock_share_price_service):
        mock_share_price_service.get_price.return_value = 100.0
        mock_account.balance = 500.0

        with pytest.raises(ValueError):
            trading_service.buy_shares("AAPL", 10)

        mock_portfolio.add_shares.assert_not_called()

    def test_buy_shares_exact_balance_succeeds(self, trading_service, mock_account, mock_share_price_service):
        mock_share_price_service.get_price.return_value = 100.0
        mock_account.balance = 1000.0

        transaction = trading_service.buy_shares("AAPL", 10)

        assert transaction is not None
        mock_account.withdraw.assert_called_once_with(1000.0)

    def test_buy_shares_does_not_add_transaction_when_insufficient_funds(self, trading_service, mock_account, mock_share_price_service):
        mock_share_price_service.get_price.return_value = 100.0
        mock_account.balance = 500.0

        with pytest.raises(ValueError):
            trading_service.buy_shares("AAPL", 10)

        mock_account.add_transaction.assert_not_called()

    def test_buy_shares_single_share(self, trading_service, mock_account, mock_share_price_service):
        mock_share_price_service.get_price.return_value = 200.0
        mock_account.balance = 500.0

        transaction = trading_service.buy_shares("GOOG", 1)

        mock_account.withdraw.assert_called_once_with(200.0)
        mock_portfolio.add_shares if hasattr(mock_account, 'portfolio') else None
        assert transaction.quantity == 1

    def test_buy_shares_with_fractional_price(self, trading_service, mock_account, mock_share_price_service):
        mock_share_price_service.get_price.return_value = 10.50
        mock_account.balance = 1000.0

        transaction = trading_service.buy_shares("XYZ", 5)

        mock_account.withdraw.assert_called_once_with(52.5)
        assert transaction.price == 10.50


class TestSellShares:
    def test_sell_shares_returns_transaction(self, trading_service, mock_portfolio, mock_share_price_service):
        mock_portfolio.get_quantity.return_value = 20
        mock_share_price_service.get_price.return_value = 100.0

        transaction = trading_service.sell_shares("AAPL", 10)

        assert transaction is not None

    def test_sell_shares_transaction_type_is_sell(self, trading_service, mock_portfolio, mock_share_price_service):
        mock_portfolio.get_quantity.return_value = 20
        mock_share_price_service.get_price.return_value = 100.0

        transaction = trading_service.sell_shares("AAPL", 10)

        assert transaction.transaction_type == "SELL"

    def test_sell_shares_transaction_has_correct_symbol(self, trading_service, mock_portfolio, mock_share_price_service):
        mock_portfolio.get_quantity.return_value = 20
        mock_share_price_service.get_price.return_value = 100.0

        transaction = trading_service.sell_shares("AAPL", 10)

        assert transaction.symbol == "AAPL"

    def test_sell_shares_transaction_has_correct_quantity(self, trading_service, mock_portfolio, mock_share_price_service):
        mock_portfolio.get_quantity.return_value = 20
        mock_share_price_service.get_price.return_value = 100.0

        transaction = trading_service.sell_shares("AAPL", 10)

        assert transaction.quantity == 10

    def test_sell_shares_transaction_has_correct_price(self, trading_service, mock_portfolio, mock_share_price_service):
        mock_portfolio.get_quantity.return_value = 20
        mock_share_price_service.get_price.return_value = 150.0

        transaction = trading_service.sell_shares("AAPL", 10)

        assert transaction.price == 150.0

    def test_sell_shares_calls_get_quantity_with_symbol(self, trading_service, mock_portfolio, mock_share_price_service):
        mock_portfolio.get_quantity.return_value = 20
        mock_share_price_service.get_price.return_value = 100.0

        trading_service.sell_shares("TSLA", 5)

        mock_portfolio.get_quantity.assert_called_once_with("TSLA")

    def test_sell_shares_calls_get_price_with_symbol(self, trading_service, mock_portfolio, mock_share_price_service):
        mock_portfolio.get_quantity.return_value = 20
        mock_share_price_service.get_price.return_value = 100.0

        trading_service.sell_shares("TSLA", 5)

        mock_share_price_service.get_price.assert_called_once_with("TSLA")

    def test_sell_shares_calls_portfolio_remove_shares(self, trading_service, mock_portfolio, mock_share_price_service):
        mock_portfolio.get_quantity.return_value = 20
        mock_share_price_service.get_price.return_value = 100.0

        trading_service.sell_shares("AAPL", 10)

        mock_portfolio.remove_shares.assert_called_once_with("AAPL", 10)

    def test_sell_shares_calls_account_deposit_with_total_proceeds(self, trading_service, mock_account, mock_portfolio, mock_share_price_service):
        mock_portfolio.get_quantity.return_value = 20
        mock_share_price_service.get_price.return_value = 100.0

        trading_service.sell_shares("AAPL", 10)

        mock_account.deposit.assert_called_once_with(1000.0)

    def test_sell_shares_adds_transaction_to_account(self, trading_service, mock_account, mock_portfolio, mock_share_price_service):
        mock_portfolio.get_quantity.return_value = 20
        mock_share_price_service.get_price.return_value = 100.0

        transaction = trading_service.sell_shares("AAPL", 10)

        mock_account.add_transaction.assert_called_once_with(transaction)

    def test_sell_shares_raises_value_error_for_zero_quantity(self, trading_service):
        with pytest.raises(ValueError) as exc_info:
            trading_service.sell_shares("AAPL", 0)

        assert "Quantity must be positive" in str(exc_info.value)

    def test_sell_shares_raises_value_error_for_negative_quantity(self, trading_service):
        with pytest.raises(ValueError) as exc_info:
            trading_service.sell_shares("AAPL", -5)

        assert "Quantity must be positive" in str(exc_info.value)

    def test_sell_shares_raises_value_error_for_insufficient_shares(self, trading_service, mock_portfolio):
        mock_portfolio.get_quantity.return_value = 5

        with pytest.raises(ValueError) as exc_info:
            trading_service.sell_shares("AAPL", 10)

        assert "Insufficient shares" in str(exc_info.value)

    def test_sell_shares_insufficient_shares_message_contains_needed_amount(self, trading_service, mock_portfolio):
        mock_portfolio.get_quantity.return_value = 5

        with pytest.raises(ValueError) as exc_info:
            trading_service.sell_shares("AAPL", 10)

        assert "10" in str(exc_info.value)

    def test_sell_shares_insufficient_shares_message_contains_available_amount(self, trading_service, mock_portfolio):
        mock_portfolio.get_quantity.return_value = 5

        with pytest.raises(ValueError) as exc_info:
            trading_service.sell_shares("AAPL", 10)

        assert "5" in str(exc_info.value)

    def test_sell_shares_does_not_remove_shares_when_insufficient(self, trading_service, mock_portfolio):
        mock_portfolio.get_quantity.return_value = 5

        with pytest.raises(ValueError):
            trading_service.sell_shares("AAPL", 10)

        mock_portfolio.remove_shares.assert_not_called()

    def test_sell_shares_does_not_deposit_when_insufficient_shares(self, trading_service, mock_account, mock_portfolio):
        mock_portfolio.get_quantity.return_value = 5

        with pytest.raises(ValueError):
            trading_service.sell_shares("AAPL", 10)

        mock_account.deposit.assert_not_called()

    def test_sell_shares_does_not_add_transaction_when_insufficient_shares(self, trading_service, mock_account, mock_portfolio):
        mock_portfolio.get_quantity.return_value = 5

        with pytest.raises(ValueError):
            trading_service.sell_shares("AAPL", 10)

        mock_account.add_transaction.assert_not_called()

    def test_sell_shares_exact_quantity_succeeds(self, trading_service, mock_account, mock_portfolio, mock_share_price_service):
        mock_portfolio.get_quantity.return_value = 10
        mock_share_price_service.get_price.return_value = 100.0

        transaction = trading_service.sell_shares("AAPL", 10)

        assert transaction is not None
        mock_portfolio.remove_shares.assert_called_once_with("AAPL", 10)

    def test_sell_shares_zero_holdings_raises_error(self, trading_service, mock_portfolio):
        mock_portfolio.get_quantity.return_value = 0

        with pytest.raises(ValueError) as exc_info:
            trading_service.sell_shares("AAPL", 1)

        assert "Insufficient shares" in str(exc_info.value)

    def test_sell_shares_deposits_correct_proceeds_with_fractional_price(self, trading_service, mock_account, mock_portfolio, mock_share_price_service):
        mock_portfolio.get_quantity.return_value = 20
        mock_share_price_service.get_price.return_value = 15.75

        trading_service.sell_shares("XYZ", 4)

        mock_account.deposit.assert_called_once_with(63.0)

    def test_sell_shares_single_share(self, trading_service, mock_account, mock_portfolio, mock_share_price_service):
        mock_portfolio.get_quantity.return_value = 5
        mock_share_price_service.get_price.return_value = 200.0

        transaction = trading_service.sell_shares("GOOG", 1)

        mock_account.deposit.assert_called_once_with(200.0)
        assert transaction.quantity == 1


class TestBuyAndSellIntegration:
    def test_buy_then_sell_calls_correct_methods_in_order(self, trading_service, mock_account, mock_portfolio, mock_share_price_service):
        mock_share_price_service.get_price.return_value = 100.0
        mock_account.balance = 10000.0
        mock_portfolio.get_quantity.return_value = 10

        trading_service.buy_shares("AAPL", 10)
        trading_service.sell_shares("AAPL", 5)

        assert mock_account.withdraw.call_count == 1
        assert mock_account.deposit.call_count == 1

    def test_multiple_buy_transactions_added_to_account(self, trading_service, mock_account, mock_share_price_service):
        mock_share_price_service.get_price.return_value = 50.0
        mock_account.balance = 10000.0

        t1 = trading_service.buy_shares("AAPL", 5)
        t2 = trading_service.buy_shares("TSLA", 3)

        assert mock_account.add_transaction.call_count == 2

    def test_multiple_sell_transactions_added_to_account(self, trading_service, mock_account, mock_portfolio, mock_share_price_service):
        mock_share_price_service.get_price.return_value = 50.0
        mock_portfolio.get_quantity.return_value = 100

        t1 = trading_service.sell_shares("AAPL", 5)
        t2 = trading_service.sell_shares("TSLA", 3)

        assert mock_account.add_transaction.call_count == 2

    def test_buy_negative_quantity_does_not_call_get_price(self, trading_service, mock_share_price_service):
        with pytest.raises(ValueError):
            trading_service.buy_shares("AAPL", -1)

        mock_share_price_service.get_price.assert_not_called()

    def test_sell_negative_quantity_does_not_call_get_quantity(self, trading_service, mock_portfolio):
        with pytest.raises(ValueError):
            trading_service.sell_shares("AAPL", -1)

        mock_portfolio.get_quantity.assert_not_called()

    def test_sell_zero_quantity_does_not_call_get_quantity(self, trading_service, mock_portfolio):
        with pytest.raises(ValueError):
            trading_service.sell_shares("AAPL", 0)

        mock_portfolio.get_quantity.assert_not_called()

    def test_buy_zero_quantity_does_not_call_get_price(self, trading_service, mock_share_price_service):
        with pytest.raises(ValueError):
            trading_service.buy_shares("AAPL", 0)

        mock_share_price_service.get_price.assert_not_called()

    def test_transaction_objects_are_different_for_buy_and_sell(self, trading_service, mock_account, mock_portfolio, mock_share_price_service):
        mock_share_price_service.get_price.return_value = 100.0
        mock_account.balance = 10000.0
        mock_portfolio.get_quantity.return_value = 20

        buy_transaction = trading_service.buy_shares("AAPL", 5)
        sell_transaction = trading_service.sell_shares("AAPL", 5)

        assert buy_transaction is not sell_transaction
        assert buy_transaction.transaction_type == "BUY"
        assert sell_transaction.transaction_type == "SELL"