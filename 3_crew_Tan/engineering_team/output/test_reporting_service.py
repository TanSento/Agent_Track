import unittest
from unittest.mock import MagicMock, patch
from reporting_service import ReportingService


class TestReportingServiceHoldingsReport(unittest.TestCase):

    def setUp(self):
        self.account = MagicMock()
        self.portfolio = MagicMock()
        self.portfolio_valuation = MagicMock()
        self.service = ReportingService(self.account, self.portfolio, self.portfolio_valuation)

    def test_holdings_report_with_no_shares(self):
        self.portfolio.get_holdings.return_value = {}
        self.account.get_balance.return_value = 1000.00
        self.portfolio_valuation.total_value.return_value = 0.00

        result = self.service.holdings_report()

        self.assertIn("=== Current Holdings ===", result)
        self.assertIn("No shares currently held.", result)
        self.assertIn("Cash Balance: $1000.00", result)
        self.assertIn("Portfolio Market Value: $0.00", result)

    def test_holdings_report_with_single_holding(self):
        self.portfolio.get_holdings.return_value = {"AAPL": 10}
        self.account.get_balance.return_value = 500.00
        self.portfolio_valuation.total_value.return_value = 1500.00

        result = self.service.holdings_report()

        self.assertIn("=== Current Holdings ===", result)
        self.assertIn("AAPL: 10 shares", result)
        self.assertIn("Cash Balance: $500.00", result)
        self.assertIn("Portfolio Market Value: $1500.00", result)

    def test_holdings_report_with_multiple_holdings(self):
        self.portfolio.get_holdings.return_value = {"AAPL": 10, "GOOG": 5, "TSLA": 3}
        self.account.get_balance.return_value = 250.75
        self.portfolio_valuation.total_value.return_value = 3000.00

        result = self.service.holdings_report()

        self.assertIn("AAPL: 10 shares", result)
        self.assertIn("GOOG: 5 shares", result)
        self.assertIn("TSLA: 3 shares", result)
        self.assertIn("Cash Balance: $250.75", result)
        self.assertIn("Portfolio Market Value: $3000.00", result)

    def test_holdings_report_cash_balance_zero(self):
        self.portfolio.get_holdings.return_value = {}
        self.account.get_balance.return_value = 0.00
        self.portfolio_valuation.total_value.return_value = 0.00

        result = self.service.holdings_report()

        self.assertIn("Cash Balance: $0.00", result)

    def test_holdings_report_header_is_first_line(self):
        self.portfolio.get_holdings.return_value = {}
        self.account.get_balance.return_value = 100.00
        self.portfolio_valuation.total_value.return_value = 0.00

        result = self.service.holdings_report()
        lines = result.split("\n")

        self.assertEqual(lines[0], "=== Current Holdings ===")

    def test_holdings_report_calls_get_holdings(self):
        self.portfolio.get_holdings.return_value = {}
        self.account.get_balance.return_value = 100.00
        self.portfolio_valuation.total_value.return_value = 0.00

        self.service.holdings_report()

        self.portfolio.get_holdings.assert_called_once()

    def test_holdings_report_calls_get_balance(self):
        self.portfolio.get_holdings.return_value = {}
        self.account.get_balance.return_value = 100.00
        self.portfolio_valuation.total_value.return_value = 0.00

        self.service.holdings_report()

        self.account.get_balance.assert_called_once()

    def test_holdings_report_calls_total_value(self):
        self.portfolio.get_holdings.return_value = {}
        self.account.get_balance.return_value = 100.00
        self.portfolio_valuation.total_value.return_value = 0.00

        self.service.holdings_report()

        self.portfolio_valuation.total_value.assert_called_once()

    def test_holdings_report_large_balance_formatting(self):
        self.portfolio.get_holdings.return_value = {}
        self.account.get_balance.return_value = 1000000.99
        self.portfolio_valuation.total_value.return_value = 9999999.01

        result = self.service.holdings_report()

        self.assertIn("Cash Balance: $1000000.99", result)
        self.assertIn("Portfolio Market Value: $9999999.01", result)

    def test_holdings_report_returns_string(self):
        self.portfolio.get_holdings.return_value = {}
        self.account.get_balance.return_value = 0.00
        self.portfolio_valuation.total_value.return_value = 0.00

        result = self.service.holdings_report()

        self.assertIsInstance(result, str)


class TestReportingServiceProfitLossReport(unittest.TestCase):

    def setUp(self):
        self.account = MagicMock()
        self.portfolio = MagicMock()
        self.portfolio_valuation = MagicMock()
        self.service = ReportingService(self.account, self.portfolio, self.portfolio_valuation)

    def test_profit_loss_report_shows_profit(self):
        self.portfolio_valuation.profit_or_loss.return_value = 500.00
        self.portfolio_valuation.total_value.return_value = 1500.00
        self.account.get_balance.return_value = 1000.00

        result = self.service.profit_loss_report()

        self.assertIn("=== Profit / Loss Report ===", result)
        self.assertIn("Profit: $500.00", result)
        self.assertNotIn("Loss", result)

    def test_profit_loss_report_shows_loss(self):
        self.portfolio_valuation.profit_or_loss.return_value = -300.00
        self.portfolio_valuation.total_value.return_value = 700.00
        self.account.get_balance.return_value = 800.00

        result = self.service.profit_loss_report()

        self.assertIn("=== Profit / Loss Report ===", result)
        self.assertIn("Loss: $300.00", result)
        self.assertNotIn("Profit", result)

    def test_profit_loss_report_zero_profit_loss(self):
        self.portfolio_valuation.profit_or_loss.return_value = 0.00
        self.portfolio_valuation.total_value.return_value = 1000.00
        self.account.get_balance.return_value = 1000.00

        result = self.service.profit_loss_report()

        self.assertIn("Profit: $0.00", result)

    def test_profit_loss_report_contains_cash_balance(self):
        self.portfolio_valuation.profit_or_loss.return_value = 100.00
        self.portfolio_valuation.total_value.return_value = 1100.00
        self.account.get_balance.return_value = 250.50

        result = self.service.profit_loss_report()

        self.assertIn("Cash Balance: $250.50", result)

    def test_profit_loss_report_contains_portfolio_market_value(self):
        self.portfolio_valuation.profit_or_loss.return_value = 100.00
        self.portfolio_valuation.total_value.return_value = 2345.67
        self.account.get_balance.return_value = 500.00

        result = self.service.profit_loss_report()

        self.assertIn("Portfolio Market Value: $2345.67", result)

    def test_profit_loss_report_header_is_first_line(self):
        self.portfolio_valuation.profit_or_loss.return_value = 0.00
        self.portfolio_valuation.total_value.return_value = 0.00
        self.account.get_balance.return_value = 0.00

        result = self.service.profit_loss_report()
        lines = result.split("\n")

        self.assertEqual(lines[0], "=== Profit / Loss Report ===")

    def test_profit_loss_report_calls_profit_or_loss(self):
        self.portfolio_valuation.profit_or_loss.return_value = 0.00
        self.portfolio_valuation.total_value.return_value = 0.00
        self.account.get_balance.return_value = 0.00

        self.service.profit_loss_report()

        self.portfolio_valuation.profit_or_loss.assert_called_once()

    def test_profit_loss_report_calls_total_value(self):
        self.portfolio_valuation.profit_or_loss.return_value = 0.00
        self.portfolio_valuation.total_value.return_value = 0.00
        self.account.get_balance.return_value = 0.00

        self.service.profit_loss_report()

        self.portfolio_valuation.total_value.assert_called_once()

    def test_profit_loss_report_calls_get_balance(self):
        self.portfolio_valuation.profit_or_loss.return_value = 0.00
        self.portfolio_valuation.total_value.return_value = 0.00
        self.account.get_balance.return_value = 0.00

        self.service.profit_loss_report()

        self.account.get_balance.assert_called_once()

    def test_profit_loss_report_returns_string(self):
        self.portfolio_valuation.profit_or_loss.return_value = 0.00
        self.portfolio_valuation.total_value.return_value = 0.00
        self.account.get_balance.return_value = 0.00

        result = self.service.profit_loss_report()

        self.assertIsInstance(result, str)

    def test_profit_loss_report_large_profit(self):
        self.portfolio_valuation.profit_or_loss.return_value = 99999.99
        self.portfolio_valuation.total_value.return_value = 199999.99
        self.account.get_balance.return_value = 50000.00

        result = self.service.profit_loss_report()

        self.assertIn("Profit: $99999.99", result)

    def test_profit_loss_report_large_loss(self):
        self.portfolio_valuation.profit_or_loss.return_value = -99999.99
        self.portfolio_valuation.total_value.return_value = 1.00
        self.account.get_balance.return_value = 0.01

        result = self.service.profit_loss_report()

        self.assertIn("Loss: $99999.99", result)


class TestReportingServiceTransactionHistoryReport(unittest.TestCase):

    def setUp(self):
        self.account = MagicMock()
        self.portfolio = MagicMock()
        self.portfolio_valuation = MagicMock()
        self.service = ReportingService(self.account, self.portfolio, self.portfolio_valuation)

    def test_transaction_history_report_no_transactions(self):
        self.account.get_transactions.return_value = []

        result = self.service.transaction_history_report()

        self.assertIn("=== Transaction History ===", result)
        self.assertIn("No transactions recorded.", result)

    def test_transaction_history_report_single_transaction(self):
        txn = MagicMock()
        txn.__str__ = MagicMock(return_value="BUY AAPL 10 @ $150.00")
        self.account.get_transactions.return_value = [txn]

        result = self.service.transaction_history_report()

        self.assertIn("=== Transaction History ===", result)
        self.assertIn("BUY AAPL 10 @ $150.00", result)

    def test_transaction_history_report_multiple_transactions(self):
        txn1 = MagicMock()
        txn1.__str__ = MagicMock(return_value="DEPOSIT $1000.00")
        txn2 = MagicMock()
        txn2.__str__ = MagicMock(return_value="BUY AAPL 5 @ $150.00")
        txn3 = MagicMock()
        txn3.__str__ = MagicMock(return_value="SELL AAPL 2 @ $160.00")
        self.account.get_transactions.return_value = [txn1, txn2, txn3]

        result = self.service.transaction_history_report()

        self.assertIn("DEPOSIT $1000.00", result)
        self.assertIn("BUY AAPL 5 @ $150.00", result)
        self.assertIn("SELL AAPL 2 @ $160.00", result)

    def test_transaction_history_report_header_is_first_line(self):
        self.account.get_transactions.return_value = []

        result = self.service.transaction_history_report()
        lines = result.split("\n")

        self.assertEqual(lines[0], "=== Transaction History ===")

    def test_transaction_history_report_calls_get_transactions(self):
        self.account.get_transactions.return_value = []

        self.service.transaction_history_report()

        self.account.get_transactions.assert_called_once()

    def test_transaction_history_report_returns_string(self):
        self.account.get_transactions.return_value = []

        result = self.service.transaction_history_report()

        self.assertIsInstance(result, str)

    def test_transaction_history_report_transactions_in_order(self):
        txn1 = MagicMock()
        txn1.__str__ = MagicMock(return_value="First Transaction")
        txn2 = MagicMock()
        txn2.__str__ = MagicMock(return_value="Second Transaction")
        txn3 = MagicMock()
        txn3.__str__ = MagicMock(return_value="Third Transaction")
        self.account.get_transactions.return_value = [txn1, txn2, txn3]

        result = self.service.transaction_history_report()
        lines = result.split("\n")

        first_idx = lines.index("First Transaction")
        second_idx = lines.index("Second Transaction")
        third_idx = lines.index("Third Transaction")

        self.assertLess(first_idx, second_idx)
        self.assertLess(second_idx, third_idx)

    def test_transaction_history_report_no_transactions_absent_str_msg(self):
        txn = MagicMock()
        txn.__str__ = MagicMock(return_value="Some Transaction")
        self.account.get_transactions.return_value = [txn]

        result = self.service.transaction_history_report()

        self.assertNotIn("No transactions recorded.", result)


class TestReportingServiceFullReport(unittest.TestCase):

    def setUp(self):
        self.account = MagicMock()
        self.portfolio = MagicMock()
        self.portfolio_valuation = MagicMock()
        self.service = ReportingService(self.account, self.portfolio, self.portfolio_valuation)

    def _setup_defaults(self):
        self.portfolio.get_holdings.return_value = {"AAPL": 5}
        self.account.get_balance.return_value = 500.00
        self.portfolio_valuation.total_value.return_value = 750.00
        self.portfolio_valuation.profit_or_loss.return_value = 250.00
        self.account.get_transactions.return_value = []

    def test_full_report_contains_holdings_section(self):
        self._setup_defaults()

        result = self.service.full_report()

        self.assertIn("=== Current Holdings ===", result)

    def test_full_report_contains_profit_loss_section(self):
        self._setup_defaults()

        result = self.service.full_report()

        self.assertIn("=== Profit / Loss Report ===", result)

    def test_full_report_contains_transaction_history_section(self):
        self._setup_defaults()

        result = self.service.full_report()

        self.assertIn("=== Transaction History ===", result)

    def test_full_report_sections_separated_by_double_newline(self):
        self._setup_defaults()

        result = self.service.full_report()

        self.assertIn("\n\n", result)

    def test_full_report_holdings_before_profit_loss(self):
        self._setup_defaults()

        result = self.service.full_report()

        holdings_idx = result.index("=== Current Holdings ===")
        pl_idx = result.index("=== Profit / Loss Report ===")

        self.assertLess(holdings_idx, pl_idx)

    def test_full_report_profit_loss_before_transactions(self):
        self._setup_defaults()

        result = self.service.full_report()

        pl_idx = result.index("=== Profit / Loss Report ===")
        txn_idx = result.index("=== Transaction History ===")

        self.assertLess(pl_idx, txn_idx)

    def test_full_report_returns_string(self):
        self._setup_defaults()

        result = self.service.full_report()

        self.assertIsInstance(result, str)

    def test_full_report_calls_holdings_report(self):
        self._setup_defaults()
        self.service.holdings_report = MagicMock(return_value="=== Current Holdings ===\nTest")
        self.service.profit_loss_report = MagicMock(return_value="=== Profit / Loss Report ===\nTest")
        self.service.transaction_history_report = MagicMock(return_value="=== Transaction History ===\nTest")

        self.service.full_report()

        self.service.holdings_report.assert_called_once()

    def test_full_report_calls_profit_loss_report(self):
        self._setup_defaults()
        self.service.holdings_report = MagicMock(return_value="=== Current Holdings ===\nTest")
        self.service.profit_loss_report = MagicMock(return_value="=== Profit / Loss Report ===\nTest")
        self.service.transaction_history_report = MagicMock(return_value="=== Transaction History ===\nTest")

        self.service.full_report()

        self.service.profit_loss_report.assert_called_once()

    def test_full_report_calls_transaction_history_report(self):
        self._setup_defaults()
        self.service.holdings_report = MagicMock(return_value="=== Current Holdings ===\nTest")
        self.service.profit_loss_report = MagicMock(return_value="=== Profit / Loss Report ===\nTest")
        self.service.transaction_history_report = MagicMock(return_value="=== Transaction History ===\nTest")

        self.service.full_report()

        self.service.transaction_history_report.assert_called_once()

    def test_full_report_all_sections_present_with_transactions(self):
        self.portfolio.get_holdings.return_value = {"GOOG": 2}
        self.account.get_balance.return_value = 200.00
        self.portfolio_valuation.total_value.return_value = 600.00
        self.portfolio_valuation.profit_or_loss.return_value = -100.00
        txn = MagicMock()
        txn.__str__ = MagicMock(return_value="BUY GOOG 2 @ $300.00")
        self.account.get_transactions.return_value = [txn]

        result = self.service.full_report()

        self.assertIn("=== Current Holdings ===", result)
        self.assertIn("GOOG: 2 shares", result)
        self.assertIn("=== Profit / Loss Report ===", result)
        self.assertIn("Loss: $100.00", result)
        self.assertIn("=== Transaction History ===", result)
        self.assertIn("BUY GOOG 2 @ $300.00", result)

    def test_full_report_three_sections_joined_by_double_newline(self):
        self._setup_defaults()
        self.service.holdings_report = MagicMock(return_value="SECTION_A")
        self.service.profit_loss_report = MagicMock(return_value="SECTION_B")
        self.service.transaction_history_report = MagicMock(return_value="SECTION_C")

        result = self.service.full_report()

        self.assertEqual(result, "SECTION_A\n\nSECTION_B\n\nSECTION_C")


class TestReportingServiceInit(unittest.TestCase):

    def test_init_stores_account(self):
        account = MagicMock()
        portfolio = MagicMock()
        portfolio_valuation = MagicMock()

        service = ReportingService(account, portfolio, portfolio_valuation)

        self.assertEqual(service.account, account)

    def test_init_stores_portfolio(self):
        account = MagicMock()
        portfolio = MagicMock()
        portfolio_valuation = MagicMock()

        service = ReportingService(account, portfolio, portfolio_valuation)

        self.assertEqual(service.portfolio, portfolio)

    def test_init_stores_portfolio_valuation(self):
        account = MagicMock()
        portfolio = MagicMock()
        portfolio_valuation = MagicMock()

        service = ReportingService(account, portfolio, portfolio_valuation)

        self.assertEqual(service.portfolio_valuation, portfolio_valuation)


if __name__ == "__main__":
    unittest.main()