import unittest
from unittest.mock import MagicMock, patch
from portfolio_valuation import PortfolioValuation


class TestPortfolioValuation(unittest.TestCase):

    def setUp(self):
        self.mock_account = MagicMock()
        self.mock_portfolio = MagicMock()
        self.mock_share_price_service = MagicMock()

        self.valuation = PortfolioValuation(
            account=self.mock_account,
            portfolio=self.mock_portfolio,
            share_price_service=self.mock_share_price_service
        )

    # Tests for __init__
    def test_init_sets_account(self):
        self.assertEqual(self.valuation.account, self.mock_account)

    def test_init_sets_portfolio(self):
        self.assertEqual(self.valuation.portfolio, self.mock_portfolio)

    def test_init_sets_share_price_service(self):
        self.assertEqual(self.valuation.share_price_service, self.mock_share_price_service)

    # Tests for calculate_portfolio_value
    def test_calculate_portfolio_value_empty_holdings(self):
        self.mock_portfolio.get_holdings.return_value = {}
        result = self.valuation.calculate_portfolio_value()
        self.assertEqual(result, 0.0)

    def test_calculate_portfolio_value_single_holding(self):
        self.mock_portfolio.get_holdings.return_value = {"AAPL": 10}
        self.mock_share_price_service.get_share_price.return_value = 150.0
        result = self.valuation.calculate_portfolio_value()
        self.assertEqual(result, 1500.0)

    def test_calculate_portfolio_value_multiple_holdings(self):
        self.mock_portfolio.get_holdings.return_value = {"AAPL": 10, "GOOG": 5}
        self.mock_share_price_service.get_share_price.side_effect = lambda symbol: {
            "AAPL": 150.0,
            "GOOG": 200.0
        }[symbol]
        result = self.valuation.calculate_portfolio_value()
        self.assertEqual(result, 10 * 150.0 + 5 * 200.0)

    def test_calculate_portfolio_value_skips_zero_quantity(self):
        self.mock_portfolio.get_holdings.return_value = {"AAPL": 0, "GOOG": 5}
        self.mock_share_price_service.get_share_price.side_effect = lambda symbol: {
            "AAPL": 150.0,
            "GOOG": 200.0
        }[symbol]
        result = self.valuation.calculate_portfolio_value()
        self.assertEqual(result, 5 * 200.0)
        calls = [call[0][0] for call in self.mock_share_price_service.get_share_price.call_args_list]
        self.assertNotIn("AAPL", calls)

    def test_calculate_portfolio_value_does_not_call_price_service_for_zero_quantity(self):
        self.mock_portfolio.get_holdings.return_value = {"AAPL": 0}
        result = self.valuation.calculate_portfolio_value()
        self.assertEqual(result, 0.0)
        self.mock_share_price_service.get_share_price.assert_not_called()

    def test_calculate_portfolio_value_calls_get_holdings(self):
        self.mock_portfolio.get_holdings.return_value = {}
        self.valuation.calculate_portfolio_value()
        self.mock_portfolio.get_holdings.assert_called_once()

    def test_calculate_portfolio_value_calls_price_service_for_each_symbol(self):
        self.mock_portfolio.get_holdings.return_value = {"AAPL": 10, "MSFT": 3}
        self.mock_share_price_service.get_share_price.return_value = 100.0
        self.valuation.calculate_portfolio_value()
        self.assertEqual(self.mock_share_price_service.get_share_price.call_count, 2)

    def test_calculate_portfolio_value_with_fractional_prices(self):
        self.mock_portfolio.get_holdings.return_value = {"TSLA": 3}
        self.mock_share_price_service.get_share_price.return_value = 123.45
        result = self.valuation.calculate_portfolio_value()
        self.assertAlmostEqual(result, 3 * 123.45)

    def test_calculate_portfolio_value_with_large_quantities(self):
        self.mock_portfolio.get_holdings.return_value = {"AAPL": 1000000}
        self.mock_share_price_service.get_share_price.return_value = 200.0
        result = self.valuation.calculate_portfolio_value()
        self.assertEqual(result, 1000000 * 200.0)

    def test_calculate_portfolio_value_returns_float(self):
        self.mock_portfolio.get_holdings.return_value = {}
        result = self.valuation.calculate_portfolio_value()
        self.assertIsInstance(result, float)

    def test_calculate_portfolio_value_all_zero_quantities(self):
        self.mock_portfolio.get_holdings.return_value = {"AAPL": 0, "GOOG": 0, "MSFT": 0}
        result = self.valuation.calculate_portfolio_value()
        self.assertEqual(result, 0.0)
        self.mock_share_price_service.get_share_price.assert_not_called()

    def test_calculate_portfolio_value_mixed_zero_and_nonzero_quantities(self):
        self.mock_portfolio.get_holdings.return_value = {"AAPL": 0, "GOOG": 2, "MSFT": 0, "TSLA": 4}
        self.mock_share_price_service.get_share_price.side_effect = lambda symbol: {
            "GOOG": 100.0,
            "TSLA": 50.0
        }[symbol]
        result = self.valuation.calculate_portfolio_value()
        self.assertEqual(result, 2 * 100.0 + 4 * 50.0)

    # Tests for calculate_total_value
    def test_calculate_total_value_with_zero_portfolio_value(self):
        self.mock_portfolio.get_holdings.return_value = {}
        self.mock_account.get_balance.return_value = 1000.0
        result = self.valuation.calculate_total_value()
        self.assertEqual(result, 1000.0)

    def test_calculate_total_value_with_zero_cash_balance(self):
        self.mock_portfolio.get_holdings.return_value = {"AAPL": 5}
        self.mock_share_price_service.get_share_price.return_value = 100.0
        self.mock_account.get_balance.return_value = 0.0
        result = self.valuation.calculate_total_value()
        self.assertEqual(result, 500.0)

    def test_calculate_total_value_combines_portfolio_and_cash(self):
        self.mock_portfolio.get_holdings.return_value = {"AAPL": 10}
        self.mock_share_price_service.get_share_price.return_value = 100.0
        self.mock_account.get_balance.return_value = 500.0
        result = self.valuation.calculate_total_value()
        self.assertEqual(result, 1000.0 + 500.0)

    def test_calculate_total_value_calls_get_balance(self):
        self.mock_portfolio.get_holdings.return_value = {}
        self.mock_account.get_balance.return_value = 0.0
        self.valuation.calculate_total_value()
        self.mock_account.get_balance.assert_called_once()

    def test_calculate_total_value_calls_calculate_portfolio_value(self):
        self.mock_portfolio.get_holdings.return_value = {"GOOG": 2}
        self.mock_share_price_service.get_share_price.return_value = 300.0
        self.mock_account.get_balance.return_value = 200.0
        result = self.valuation.calculate_total_value()
        self.assertEqual(result, 2 * 300.0 + 200.0)

    def test_calculate_total_value_returns_float(self):
        self.mock_portfolio.get_holdings.return_value = {}
        self.mock_account.get_balance.return_value = 0.0
        result = self.valuation.calculate_total_value()
        self.assertIsInstance(result, float)

    def test_calculate_total_value_with_multiple_holdings_and_cash(self):
        self.mock_portfolio.get_holdings.return_value = {"AAPL": 5, "MSFT": 3}
        self.mock_share_price_service.get_share_price.side_effect = lambda symbol: {
            "AAPL": 200.0,
            "MSFT": 100.0
        }[symbol]
        self.mock_account.get_balance.return_value = 750.0
        result = self.valuation.calculate_total_value()
        self.assertEqual(result, 5 * 200.0 + 3 * 100.0 + 750.0)

    def test_calculate_total_value_with_fractional_values(self):
        self.mock_portfolio.get_holdings.return_value = {"TSLA": 7}
        self.mock_share_price_service.get_share_price.return_value = 33.33
        self.mock_account.get_balance.return_value = 66.67
        result = self.valuation.calculate_total_value()
        self.assertAlmostEqual(result, 7 * 33.33 + 66.67)

    # Tests for calculate_profit_or_loss
    def test_calculate_profit_or_loss_with_profit(self):
        self.mock_portfolio.get_holdings.return_value = {"AAPL": 10}
        self.mock_share_price_service.get_share_price.return_value = 200.0
        self.mock_account.get_balance.return_value = 500.0
        self.mock_account.get_initial_deposit.return_value = 1000.0
        result = self.valuation.calculate_profit_or_loss()
        # total_value = 2000 + 500 = 2500, profit = 2500 - 1000 = 1500
        self.assertEqual(result, 1500.0)

    def test_calculate_profit_or_loss_with_loss(self):
        self.mock_portfolio.get_holdings.return_value = {"AAPL": 5}
        self.mock_share_price_service.get_share_price.return_value = 50.0
        self.mock_account.get_balance.return_value = 100.0
        self.mock_account.get_initial_deposit.return_value = 1000.0
        result = self.valuation.calculate_profit_or_loss()
        # total_value = 250 + 100 = 350, loss = 350 - 1000 = -650
        self.assertEqual(result, -650.0)

    def test_calculate_profit_or_loss_breakeven(self):
        self.mock_portfolio.get_holdings.return_value = {"AAPL": 10}
        self.mock_share_price_service.get_share_price.return_value = 100.0
        self.mock_account.get_balance.return_value = 0.0
        self.mock_account.get_initial_deposit.return_value = 1000.0
        result = self.valuation.calculate_profit_or_loss()
        self.assertEqual(result, 0.0)

    def test_calculate_profit_or_loss_calls_get_initial_deposit(self):
        self.mock_portfolio.get_holdings.return_value = {}
        self.mock_account.get_balance.return_value = 0.0
        self.mock_account.get_initial_deposit.return_value = 500.0
        self.valuation.calculate_profit_or_loss()
        self.mock_account.get_initial_deposit.assert_called_once()

    def test_calculate_profit_or_loss_zero_initial_deposit_and_zero_total(self):
        self.mock_portfolio.get_holdings.return_value = {}
        self.mock_account.get_balance.return_value = 0.0
        self.mock_account.get_initial_deposit.return_value = 0.0
        result = self.valuation.calculate_profit_or_loss()
        self.assertEqual(result, 0.0)

    def test_calculate_profit_or_loss_returns_float(self):
        self.mock_portfolio.get_holdings.return_value = {}
        self.mock_account.get_balance.return_value = 0.0
        self.mock_account.get_initial_deposit.return_value = 0.0
        result = self.valuation.calculate_profit_or_loss()
        self.assertIsInstance(result, float)

    def test_calculate_profit_or_loss_large_profit(self):
        self.mock_portfolio.get_holdings.return_value = {"AAPL": 1000}
        self.mock_share_price_service.get_share_price.return_value = 500.0
        self.mock_account.get_balance.return_value = 10000.0
        self.mock_account.get_initial_deposit.return_value = 5000.0
        result = self.valuation.calculate_profit_or_loss()
        # total_value = 500000 + 10000 = 510000, profit = 510000 - 5000 = 505000
        self.assertEqual(result, 505000.0)

    def test_calculate_profit_or_loss_with_multiple_symbols(self):
        self.mock_portfolio.get_holdings.return_value = {"AAPL": 5, "GOOG": 2}
        self.mock_share_price_service.get_share_price.side_effect = lambda symbol: {
            "AAPL": 100.0,
            "GOOG": 200.0
        }[symbol]
        self.mock_account.get_balance.return_value = 300.0
        self.mock_account.get_initial_deposit.return_value = 1200.0
        result = self.valuation.calculate_profit_or_loss()
        # portfolio_value = 500 + 400 = 900, total = 900 + 300 = 1200, pnl = 1200 - 1200 = 0
        self.assertEqual(result, 0.0)

    def test_calculate_profit_or_loss_only_cash(self):
        self.mock_portfolio.get_holdings.return_value = {}
        self.mock_account.get_balance.return_value = 1500.0
        self.mock_account.get_initial_deposit.return_value = 1000.0
        result = self.valuation.calculate_profit_or_loss()
        self.assertEqual(result, 500.0)

    # Integration-style tests using the class methods together
    def test_full_scenario_buy_and_price_increase(self):
        # Simulate: deposit 1000, spend 500 on 5 AAPL at 100, price rises to 150
        self.mock_portfolio.get_holdings.return_value = {"AAPL": 5}
        self.mock_share_price_service.get_share_price.return_value = 150.0
        self.mock_account.get_balance.return_value = 500.0
        self.mock_account.get_initial_deposit.return_value = 1000.0

        portfolio_value = self.valuation.calculate_portfolio_value()
        total_value = self.valuation.calculate_total_value()
        pnl = self.valuation.calculate_profit_or_loss()

        self.assertEqual(portfolio_value, 750.0)
        self.assertEqual(total_value, 1250.0)
        self.assertEqual(pnl, 250.0)

    def test_full_scenario_buy_and_price_decrease(self):
        # Simulate: deposit 1000, spend 600 on 3 GOOG at 200, price falls to 150
        self.mock_portfolio.get_holdings.return_value = {"GOOG": 3}
        self.mock_share_price_service.get_share_price.return_value = 150.0
        self.mock_account.get_balance.return_value = 400.0
        self.mock_account.get_initial_deposit.return_value = 1000.0

        portfolio_value = self.valuation.calculate_portfolio_value()
        total_value = self.valuation.calculate_total_value()
        pnl = self.valuation.calculate_profit_or_loss()

        self.assertEqual(portfolio_value, 450.0)
        self.assertEqual(total_value, 850.0)
        self.assertEqual(pnl, -150.0)

    def test_full_scenario_no_holdings_no_change(self):
        # No shares bought, just cash sitting
        self.mock_portfolio.get_holdings.return_value = {}
        self.mock_account.get_balance.return_value = 1000.0
        self.mock_account.get_initial_deposit.return_value = 1000.0

        portfolio_value = self.valuation.calculate_portfolio_value()
        total_value = self.valuation.calculate_total_value()
        pnl = self.valuation.calculate_profit_or_loss()

        self.assertEqual(portfolio_value, 0.0)
        self.assertEqual(total_value, 1000.0)
        self.assertEqual(pnl, 0.0)

    def test_price_service_called_with_correct_symbols(self):
        self.mock_portfolio.get_holdings.return_value = {"AAPL": 3, "TSLA": 2}
        self.mock_share_price_service.get_share_price.return_value = 100.0
        self.valuation.calculate_portfolio_value()
        called_symbols = {call[0][0] for call in self.mock_share_price_service.get_share_price.call_args_list}
        self.assertIn("AAPL", called_symbols)
        self.assertIn("TSLA", called_symbols)

    def test_calculate_total_value_with_negative_balance(self):
        # Edge case: account might allow negative balance in some scenarios
        self.mock_portfolio.get_holdings.return_value = {"AAPL": 5}
        self.mock_share_price_service.get_share_price.return_value = 100.0
        self.mock_account.get_balance.return_value = -50.0
        result = self.valuation.calculate_total_value()
        self.assertEqual(result, 500.0 - 50.0)

    def test_calculate_profit_or_loss_with_high_initial_deposit(self):
        self.mock_portfolio.get_holdings.return_value = {"AAPL": 1}
        self.mock_share_price_service.get_share_price.return_value = 100.0
        self.mock_account.get_balance.return_value = 0.0
        self.mock_account.get_initial_deposit.return_value = 1000000.0
        result = self.valuation.calculate_profit_or_loss()
        self.assertEqual(result, 100.0 - 1000000.0)


if __name__ == "__main__":
    unittest.main()