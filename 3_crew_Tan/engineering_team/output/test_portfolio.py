import pytest
from unittest.mock import MagicMock, patch
from portfolio import Portfolio


class TestPortfolioInit:
    def test_initial_holdings_empty(self):
        portfolio = Portfolio()
        assert portfolio.holdings == {}

    def test_get_holdings_returns_empty_dict_initially(self):
        portfolio = Portfolio()
        assert portfolio.get_holdings() == {}


class TestPortfolioBuy:
    def test_buy_new_symbol_adds_to_holdings(self):
        portfolio = Portfolio()
        portfolio.buy("AAPL", 10)
        assert portfolio.holdings["AAPL"] == 10

    def test_buy_converts_symbol_to_uppercase(self):
        portfolio = Portfolio()
        portfolio.buy("aapl", 10)
        assert "AAPL" in portfolio.holdings
        assert "aapl" not in portfolio.holdings

    def test_buy_mixed_case_converts_to_uppercase(self):
        portfolio = Portfolio()
        portfolio.buy("aApL", 5)
        assert "AAPL" in portfolio.holdings

    def test_buy_existing_symbol_increases_quantity(self):
        portfolio = Portfolio()
        portfolio.buy("AAPL", 10)
        portfolio.buy("AAPL", 5)
        assert portfolio.holdings["AAPL"] == 15

    def test_buy_multiple_different_symbols(self):
        portfolio = Portfolio()
        portfolio.buy("AAPL", 10)
        portfolio.buy("GOOG", 5)
        assert portfolio.holdings["AAPL"] == 10
        assert portfolio.holdings["GOOG"] == 5

    def test_buy_zero_quantity_raises_value_error(self):
        portfolio = Portfolio()
        with pytest.raises(ValueError):
            portfolio.buy("AAPL", 0)

    def test_buy_negative_quantity_raises_value_error(self):
        portfolio = Portfolio()
        with pytest.raises(ValueError):
            portfolio.buy("AAPL", -5)

    def test_buy_negative_quantity_error_message(self):
        portfolio = Portfolio()
        with pytest.raises(ValueError, match="Quantity must be positive"):
            portfolio.buy("AAPL", -1)

    def test_buy_zero_quantity_error_message(self):
        portfolio = Portfolio()
        with pytest.raises(ValueError, match="Quantity must be positive"):
            portfolio.buy("AAPL", 0)

    def test_buy_single_share(self):
        portfolio = Portfolio()
        portfolio.buy("TSLA", 1)
        assert portfolio.holdings["TSLA"] == 1

    def test_buy_large_quantity(self):
        portfolio = Portfolio()
        portfolio.buy("MSFT", 1000000)
        assert portfolio.holdings["MSFT"] == 1000000

    def test_buy_does_not_affect_other_symbols(self):
        portfolio = Portfolio()
        portfolio.buy("AAPL", 10)
        portfolio.buy("GOOG", 5)
        portfolio.buy("AAPL", 3)
        assert portfolio.holdings["GOOG"] == 5


class TestPortfolioSell:
    def test_sell_reduces_holdings(self):
        portfolio = Portfolio()
        portfolio.buy("AAPL", 10)
        portfolio.sell("AAPL", 3)
        assert portfolio.holdings["AAPL"] == 7

    def test_sell_all_shares_removes_symbol(self):
        portfolio = Portfolio()
        portfolio.buy("AAPL", 10)
        portfolio.sell("AAPL", 10)
        assert "AAPL" not in portfolio.holdings

    def test_sell_more_than_held_raises_value_error(self):
        portfolio = Portfolio()
        portfolio.buy("AAPL", 5)
        with pytest.raises(ValueError):
            portfolio.sell("AAPL", 10)

    def test_sell_symbol_not_held_raises_value_error(self):
        portfolio = Portfolio()
        with pytest.raises(ValueError):
            portfolio.sell("AAPL", 5)

    def test_sell_zero_quantity_raises_value_error(self):
        portfolio = Portfolio()
        portfolio.buy("AAPL", 10)
        with pytest.raises(ValueError):
            portfolio.sell("AAPL", 0)

    def test_sell_negative_quantity_raises_value_error(self):
        portfolio = Portfolio()
        portfolio.buy("AAPL", 10)
        with pytest.raises(ValueError):
            portfolio.sell("AAPL", -3)

    def test_sell_negative_quantity_error_message(self):
        portfolio = Portfolio()
        portfolio.buy("AAPL", 10)
        with pytest.raises(ValueError, match="Quantity must be positive"):
            portfolio.sell("AAPL", -1)

    def test_sell_insufficient_shares_error_message(self):
        portfolio = Portfolio()
        portfolio.buy("AAPL", 5)
        with pytest.raises(ValueError, match="Insufficient shares"):
            portfolio.sell("AAPL", 10)

    def test_sell_converts_symbol_to_uppercase(self):
        portfolio = Portfolio()
        portfolio.buy("AAPL", 10)
        portfolio.sell("aapl", 3)
        assert portfolio.holdings["AAPL"] == 7

    def test_sell_mixed_case_symbol(self):
        portfolio = Portfolio()
        portfolio.buy("GOOG", 10)
        portfolio.sell("gOoG", 5)
        assert portfolio.holdings["GOOG"] == 5

    def test_sell_does_not_affect_other_symbols(self):
        portfolio = Portfolio()
        portfolio.buy("AAPL", 10)
        portfolio.buy("GOOG", 8)
        portfolio.sell("AAPL", 5)
        assert portfolio.holdings["GOOG"] == 8

    def test_sell_insufficient_shares_error_contains_symbol(self):
        portfolio = Portfolio()
        portfolio.buy("TSLA", 3)
        with pytest.raises(ValueError, match="TSLA"):
            portfolio.sell("TSLA", 10)

    def test_sell_insufficient_shares_error_contains_quantities(self):
        portfolio = Portfolio()
        portfolio.buy("TSLA", 3)
        with pytest.raises(ValueError, match="3"):
            portfolio.sell("TSLA", 10)

    def test_sell_single_share(self):
        portfolio = Portfolio()
        portfolio.buy("AAPL", 1)
        portfolio.sell("AAPL", 1)
        assert "AAPL" not in portfolio.holdings


class TestPortfolioGetHoldings:
    def test_get_holdings_returns_copy(self):
        portfolio = Portfolio()
        portfolio.buy("AAPL", 10)
        holdings = portfolio.get_holdings()
        holdings["AAPL"] = 999
        assert portfolio.holdings["AAPL"] == 10

    def test_get_holdings_returns_all_symbols(self):
        portfolio = Portfolio()
        portfolio.buy("AAPL", 10)
        portfolio.buy("GOOG", 5)
        portfolio.buy("TSLA", 3)
        holdings = portfolio.get_holdings()
        assert "AAPL" in holdings
        assert "GOOG" in holdings
        assert "TSLA" in holdings

    def test_get_holdings_returns_correct_quantities(self):
        portfolio = Portfolio()
        portfolio.buy("AAPL", 10)
        portfolio.buy("GOOG", 5)
        holdings = portfolio.get_holdings()
        assert holdings["AAPL"] == 10
        assert holdings["GOOG"] == 5

    def test_get_holdings_reflects_sells(self):
        portfolio = Portfolio()
        portfolio.buy("AAPL", 10)
        portfolio.sell("AAPL", 4)
        holdings = portfolio.get_holdings()
        assert holdings["AAPL"] == 6

    def test_get_holdings_does_not_include_sold_out_symbols(self):
        portfolio = Portfolio()
        portfolio.buy("AAPL", 10)
        portfolio.sell("AAPL", 10)
        holdings = portfolio.get_holdings()
        assert "AAPL" not in holdings

    def test_get_holdings_returns_dict_type(self):
        portfolio = Portfolio()
        holdings = portfolio.get_holdings()
        assert isinstance(holdings, dict)


class TestPortfolioGetQuantity:
    def test_get_quantity_returns_correct_amount(self):
        portfolio = Portfolio()
        portfolio.buy("AAPL", 10)
        assert portfolio.get_quantity("AAPL") == 10

    def test_get_quantity_returns_zero_for_unowned_symbol(self):
        portfolio = Portfolio()
        assert portfolio.get_quantity("AAPL") == 0

    def test_get_quantity_converts_to_uppercase(self):
        portfolio = Portfolio()
        portfolio.buy("AAPL", 10)
        assert portfolio.get_quantity("aapl") == 10

    def test_get_quantity_after_partial_sell(self):
        portfolio = Portfolio()
        portfolio.buy("AAPL", 10)
        portfolio.sell("AAPL", 3)
        assert portfolio.get_quantity("AAPL") == 7

    def test_get_quantity_after_sell_all(self):
        portfolio = Portfolio()
        portfolio.buy("AAPL", 10)
        portfolio.sell("AAPL", 10)
        assert portfolio.get_quantity("AAPL") == 0

    def test_get_quantity_after_multiple_buys(self):
        portfolio = Portfolio()
        portfolio.buy("AAPL", 5)
        portfolio.buy("AAPL", 3)
        portfolio.buy("AAPL", 2)
        assert portfolio.get_quantity("AAPL") == 10


class TestPortfolioHasSufficientShares:
    def test_has_sufficient_shares_true_when_enough(self):
        portfolio = Portfolio()
        portfolio.buy("AAPL", 10)
        assert portfolio.has_sufficient_shares("AAPL", 10) is True

    def test_has_sufficient_shares_true_when_more_than_enough(self):
        portfolio = Portfolio()
        portfolio.buy("AAPL", 10)
        assert portfolio.has_sufficient_shares("AAPL", 5) is True

    def test_has_sufficient_shares_false_when_not_enough(self):
        portfolio = Portfolio()
        portfolio.buy("AAPL", 5)
        assert portfolio.has_sufficient_shares("AAPL", 10) is False

    def test_has_sufficient_shares_false_when_not_owned(self):
        portfolio = Portfolio()
        assert portfolio.has_sufficient_shares("AAPL", 1) is False

    def test_has_sufficient_shares_converts_to_uppercase(self):
        portfolio = Portfolio()
        portfolio.buy("AAPL", 10)
        assert portfolio.has_sufficient_shares("aapl", 5) is True

    def test_has_sufficient_shares_zero_quantity(self):
        portfolio = Portfolio()
        assert portfolio.has_sufficient_shares("AAPL", 0) is True

    def test_has_sufficient_shares_exact_amount(self):
        portfolio = Portfolio()
        portfolio.buy("GOOG", 7)
        assert portfolio.has_sufficient_shares("GOOG", 7) is True

    def test_has_sufficient_shares_one_more_than_held(self):
        portfolio = Portfolio()
        portfolio.buy("GOOG", 7)
        assert portfolio.has_sufficient_shares("GOOG", 8) is False


class TestPortfolioGetTotalValue:
    def test_get_total_value_empty_portfolio(self):
        portfolio = Portfolio()
        get_share_price = MagicMock(return_value=100.0)
        assert portfolio.get_total_value(get_share_price) == 0.0

    def test_get_total_value_single_symbol(self):
        portfolio = Portfolio()
        portfolio.buy("AAPL", 10)
        get_share_price = MagicMock(return_value=150.0)
        assert portfolio.get_total_value(get_share_price) == 1500.0

    def test_get_total_value_multiple_symbols(self):
        portfolio = Portfolio()
        portfolio.buy("AAPL", 10)
        portfolio.buy("GOOG", 5)

        def mock_price(symbol):
            prices = {"AAPL": 150.0, "GOOG": 200.0}
            return prices[symbol]

        total = portfolio.get_total_value(mock_price)
        assert total == 2500.0

    def test_get_total_value_calls_get_share_price_for_each_symbol(self):
        portfolio = Portfolio()
        portfolio.buy("AAPL", 10)
        portfolio.buy("GOOG", 5)
        portfolio.buy("TSLA", 3)
        get_share_price = MagicMock(return_value=100.0)
        portfolio.get_total_value(get_share_price)
        assert get_share_price.call_count == 3

    def test_get_total_value_calls_price_with_correct_symbol(self):
        portfolio = Portfolio()
        portfolio.buy("AAPL", 10)
        get_share_price = MagicMock(return_value=150.0)
        portfolio.get_total_value(get_share_price)
        get_share_price.assert_called_with("AAPL")

    def test_get_total_value_returns_float(self):
        portfolio = Portfolio()
        portfolio.buy("AAPL", 10)
        get_share_price = MagicMock(return_value=100.0)
        result = portfolio.get_total_value(get_share_price)
        assert isinstance(result, float)

    def test_get_total_value_after_sell(self):
        portfolio = Portfolio()
        portfolio.buy("AAPL", 10)
        portfolio.sell("AAPL", 5)
        get_share_price = MagicMock(return_value=150.0)
        assert portfolio.get_total_value(get_share_price) == 750.0


class TestPortfolioRebuildFromTransactions:
    def _make_transaction(self, transaction_type, symbol, quantity):
        transaction = MagicMock()
        transaction.transaction_type = transaction_type
        transaction.symbol = symbol
        transaction.quantity = quantity
        return transaction

    def test_rebuild_clears_existing_holdings(self):
        portfolio = Portfolio()
        portfolio.buy("AAPL", 10)

        mock_buy = MagicMock()
        mock_buy.transaction_type = "BUY_TYPE"
        mock_buy.symbol = "GOOG"
        mock_buy.quantity = 5

        with patch("portfolio.Transaction") as MockTransaction:
            MockTransaction.BUY = "BUY_TYPE"
            MockTransaction.SELL = "SELL_TYPE"
            portfolio.rebuild_from_transactions([mock_buy])

        assert "AAPL" not in portfolio.holdings

    def test_rebuild_from_empty_transactions(self):
        portfolio = Portfolio()
        portfolio.buy("AAPL", 10)

        with patch("portfolio.Transaction") as MockTransaction:
            MockTransaction.BUY = "BUY_TYPE"
            MockTransaction.SELL = "SELL_TYPE"
            portfolio.rebuild_from_transactions([])

        assert portfolio.holdings == {}

    def test_rebuild_processes_buy_transactions(self):
        portfolio = Portfolio()

        mock_buy = MagicMock()
        mock_buy.symbol = "AAPL"
        mock_buy.quantity = 10

        with patch("portfolio.Transaction") as MockTransaction:
            MockTransaction.BUY = "BUY_TYPE"
            MockTransaction.SELL = "SELL_TYPE"
            mock_buy.transaction_type = "BUY_TYPE"
            portfolio.rebuild_from_transactions([mock_buy])

        assert portfolio.holdings.get("AAPL") == 10

    def test_rebuild_processes_sell_transactions(self):
        portfolio = Portfolio()

        mock_buy = MagicMock()
        mock_buy.symbol = "AAPL"
        mock_buy.quantity = 10

        mock_sell = MagicMock()
        mock_sell.symbol = "AAPL"
        mock_sell.quantity = 4

        with patch("portfolio.Transaction") as MockTransaction:
            MockTransaction.BUY = "BUY_TYPE"
            MockTransaction.SELL = "SELL_TYPE"
            mock_buy.transaction_type = "BUY_TYPE"
            mock_sell.transaction_type = "SELL_TYPE"
            portfolio.rebuild_from_transactions([mock_buy, mock_sell])

        assert portfolio.holdings.get("AAPL") == 6

    def test_rebuild_processes_multiple_buy_transactions_same_symbol(self):
        portfolio = Portfolio()

        mock_buy1 = MagicMock()
        mock_buy1.symbol = "AAPL"
        mock_buy1.quantity = 10

        mock_buy2 = MagicMock()
        mock_buy2.symbol = "AAPL"
        mock_buy2.quantity = 5

        with patch("portfolio.Transaction") as MockTransaction:
            MockTransaction.BUY = "BUY_TYPE"
            MockTransaction.SELL = "SELL_TYPE"
            mock_buy1.transaction_type = "BUY_TYPE"
            mock_buy2.transaction_type = "BUY_TYPE"
            portfolio.rebuild_from_transactions([mock_buy1, mock_buy2])

        assert portfolio.holdings.get("AAPL") == 15

    def test_rebuild_processes_multiple_symbols(self):
        portfolio = Portfolio()

        mock_buy1 = MagicMock()
        mock_buy1.symbol = "AAPL"
        mock_buy1.quantity = 10

        mock_buy2 = MagicMock()
        mock_buy2.symbol = "GOOG"
        mock_buy2.quantity = 5

        with patch("portfolio.Transaction") as MockTransaction:
            MockTransaction.BUY = "BUY_TYPE"
            MockTransaction.SELL = "SELL_TYPE"
            mock_buy1.transaction_type = "BUY_TYPE"
            mock_buy2.transaction_type = "BUY_TYPE"
            portfolio.rebuild_from_transactions([mock_buy1, mock_buy2])

        assert portfolio.holdings.get("AAPL") == 10
        assert portfolio.holdings.get("GOOG") == 5

    def test_rebuild_sell_all_shares_removes_symbol(self):
        portfolio = Portfolio()

        mock_buy = MagicMock()
        mock_buy.symbol = "AAPL"
        mock_buy.quantity = 10

        mock_sell = MagicMock()
        mock_sell.symbol = "AAPL"
        mock_sell.quantity = 10

        with patch("portfolio.Transaction") as MockTransaction:
            MockTransaction.BUY = "BUY_TYPE"
            MockTransaction.SELL = "SELL_TYPE"
            mock_buy.transaction_type = "BUY_TYPE"
            mock_sell.transaction_type = "SELL_TYPE"
            portfolio.rebuild_from_transactions([mock_buy, mock_sell])

        assert "AAPL" not in portfolio.holdings

    def test_rebuild_ignores_unknown_transaction_types(self):
        portfolio = Portfolio()

        mock_tx = MagicMock()
        mock_tx.symbol = "AAPL"
        mock_tx.quantity = 10

        with patch("portfolio.Transaction") as MockTransaction:
            MockTransaction.BUY = "BUY_TYPE"
            MockTransaction.SELL = "SELL_TYPE"
            mock_tx.transaction_type = "UNKNOWN_TYPE"
            portfolio.rebuild_from_transactions([mock_tx])

        assert portfolio.holdings == {}

    def test_rebuild_complex_sequence(self):
        portfolio = Portfolio()

        transactions = []

        buy_aapl1 = MagicMock()
        buy_aapl1.symbol = "AAPL"
        buy_aapl1.quantity = 20

        buy_goog = MagicMock()
        buy_goog.symbol = "GOOG"
        buy_goog.quantity = 15

        sell_aapl = MagicMock()
        sell_aapl.symbol = "AAPL"
        sell_aapl.quantity = 5

        buy_aapl2 = MagicMock()
        buy_aapl2.symbol = "AAPL"
        buy_aapl2.quantity = 3

        sell_goog = MagicMock()
        sell_goog.symbol = "GOOG"
        sell_goog.quantity = 15

        with patch("portfolio.Transaction") as MockTransaction:
            MockTransaction.BUY = "BUY_TYPE"
            MockTransaction.SELL = "SELL_TYPE"
            buy_aapl1.transaction_type = "BUY_TYPE"
            buy_goog.transaction_type = "BUY_TYPE"
            sell_aapl.transaction_type = "SELL_TYPE"
            buy_aapl2.transaction_type = "BUY_TYPE"
            sell_goog.transaction_type = "SELL_TYPE"

            portfolio.rebuild_from_transactions(
                [buy_aapl1, buy_goog, sell_aapl, buy_aapl2, sell_goog]
            )

        assert portfolio.holdings.get("AAPL") == 18
        assert "GOOG" not in portfolio.holdings


class TestPortfolioEdgeCases:
    def test_buy_and_sell_sequence(self):
        portfolio = Portfolio()
        portfolio.buy("AAPL", 10)
        portfolio.buy("AAPL", 5)
        portfolio.sell("AAPL", 7)
        assert portfolio.get_quantity("AAPL") == 8

    def test_multiple_symbols_independent(self):
        portfolio = Portfolio()
        portfolio.buy("AAPL", 10)
        portfolio.buy("GOOG", 20)
        portfolio.sell("AAPL", 5)
        assert portfolio.get_quantity("AAPL") == 5
        assert portfolio.get_quantity("GOOG") == 20

    def test_sell_not_held_symbol_error_message(self):
        portfolio = Portfolio()
        with pytest.raises(ValueError, match="Insufficient shares"):
            portfolio.sell("AAPL", 5)

    def test_get_holdings_independent_of_internal_state(self):
        portfolio = Portfolio()
        portfolio.buy("AAPL", 10)
        holdings1 = portfolio.get_holdings()
        portfolio.buy("AAPL", 5)
        holdings2 = portfolio.get_holdings()
        assert holdings1["AAPL"] == 10
        assert holdings2["AAPL"] == 15

    def test_buy_sell_buy_same_symbol(self):
        portfolio = Portfolio()
        portfolio.buy("TSLA", 10)
        portfolio.sell("TSLA", 10)
        assert portfolio.get_quantity("TSLA") == 0
        portfolio.buy("TSLA", 5)
        assert portfolio.get_quantity("TSLA") == 5

    def test_portfolio_with_many_symbols(self):
        portfolio = Portfolio()
        symbols = ["AAPL", "GOOG", "TSLA", "MSFT", "AMZN"]
        for i, symbol in enumerate(symbols):
            portfolio.buy(symbol, (i + 1) * 10)

        holdings = portfolio.get_holdings()
        assert len(holdings) == 5
        for i, symbol in enumerate(symbols):
            assert holdings[symbol] == (i + 1) * 10