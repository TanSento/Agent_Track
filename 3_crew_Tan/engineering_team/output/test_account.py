import unittest
from unittest.mock import MagicMock, patch, call
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


class TestAccountInit(unittest.TestCase):

    def setUp(self):
        self.mock_transaction_class = MagicMock()
        self.mock_portfolio_class = MagicMock()
        self.mock_transaction_instance = MagicMock()
        self.mock_portfolio_instance = MagicMock()
        self.mock_transaction_class.return_value = self.mock_transaction_instance
        self.mock_portfolio_class.return_value = self.mock_portfolio_instance

    def test_default_init_zero_balance(self):
        with patch('account.Transaction', self.mock_transaction_class), \
             patch('account.Portfolio', self.mock_portfolio_class):
            from account import Account
            acc = Account()
            self.assertEqual(acc.balance, 0.0)

    def test_default_init_zero_initial_deposit(self):
        with patch('account.Transaction', self.mock_transaction_class), \
             patch('account.Portfolio', self.mock_portfolio_class):
            from account import Account
            acc = Account()
            self.assertEqual(acc.initial_deposit, 0.0)

    def test_default_init_empty_transactions(self):
        with patch('account.Transaction', self.mock_transaction_class), \
             patch('account.Portfolio', self.mock_portfolio_class):
            from account import Account
            acc = Account()
            self.assertEqual(acc.transactions, [])

    def test_default_init_creates_portfolio(self):
        with patch('account.Transaction', self.mock_transaction_class), \
             patch('account.Portfolio', self.mock_portfolio_class):
            from account import Account
            acc = Account()
            self.mock_portfolio_class.assert_called_once()

    def test_init_with_positive_deposit_sets_balance(self):
        with patch('account.Transaction', self.mock_transaction_class), \
             patch('account.Portfolio', self.mock_portfolio_class):
            from account import Account
            acc = Account(initial_deposit=500.0)
            self.assertEqual(acc.balance, 500.0)

    def test_init_with_positive_deposit_sets_initial_deposit(self):
        with patch('account.Transaction', self.mock_transaction_class), \
             patch('account.Portfolio', self.mock_portfolio_class):
            from account import Account
            acc = Account(initial_deposit=500.0)
            self.assertEqual(acc.initial_deposit, 500.0)

    def test_init_with_positive_deposit_creates_transaction(self):
        with patch('account.Transaction', self.mock_transaction_class), \
             patch('account.Portfolio', self.mock_portfolio_class):
            from account import Account
            acc = Account(initial_deposit=500.0)
            self.mock_transaction_class.assert_called_once_with(
                transaction_type="deposit", amount=500.0
            )

    def test_init_with_positive_deposit_appends_transaction(self):
        with patch('account.Transaction', self.mock_transaction_class), \
             patch('account.Portfolio', self.mock_portfolio_class):
            from account import Account
            acc = Account(initial_deposit=500.0)
            self.assertEqual(len(acc.transactions), 1)

    def test_init_with_zero_deposit_does_not_deposit(self):
        with patch('account.Transaction', self.mock_transaction_class), \
             patch('account.Portfolio', self.mock_portfolio_class):
            from account import Account
            acc = Account(initial_deposit=0.0)
            self.assertEqual(acc.balance, 0.0)
            self.assertEqual(acc.initial_deposit, 0.0)
            self.mock_transaction_class.assert_not_called()

    def test_init_with_negative_deposit_does_not_deposit(self):
        with patch('account.Transaction', self.mock_transaction_class), \
             patch('account.Portfolio', self.mock_portfolio_class):
            from account import Account
            acc = Account(initial_deposit=-100.0)
            self.assertEqual(acc.balance, 0.0)
            self.assertEqual(acc.initial_deposit, 0.0)
            self.mock_transaction_class.assert_not_called()

    def test_portfolio_assigned(self):
        with patch('account.Transaction', self.mock_transaction_class), \
             patch('account.Portfolio', self.mock_portfolio_class):
            from account import Account
            acc = Account()
            self.assertEqual(acc.portfolio, self.mock_portfolio_instance)


class TestAccountDeposit(unittest.TestCase):

    def setUp(self):
        self.mock_transaction_class = MagicMock()
        self.mock_portfolio_class = MagicMock()
        self.mock_transaction_instance = MagicMock()
        self.mock_portfolio_instance = MagicMock()
        self.mock_transaction_class.return_value = self.mock_transaction_instance
        self.mock_portfolio_class.return_value = self.mock_portfolio_instance

    def _make_account(self, initial_deposit=0.0):
        with patch('account.Transaction', self.mock_transaction_class), \
             patch('account.Portfolio', self.mock_portfolio_class):
            from account import Account
            acc = Account(initial_deposit=initial_deposit)
            self.mock_transaction_class.reset_mock()
            return acc

    def test_deposit_increases_balance(self):
        with patch('account.Transaction', self.mock_transaction_class), \
             patch('account.Portfolio', self.mock_portfolio_class):
            from account import Account
            acc = Account()
            acc.deposit(200.0)
            self.assertEqual(acc.balance, 200.0)

    def test_deposit_multiple_times_accumulates_balance(self):
        with patch('account.Transaction', self.mock_transaction_class), \
             patch('account.Portfolio', self.mock_portfolio_class):
            from account import Account
            acc = Account()
            acc.deposit(100.0)
            acc.deposit(50.0)
            self.assertEqual(acc.balance, 150.0)

    def test_deposit_creates_transaction(self):
        with patch('account.Transaction', self.mock_transaction_class), \
             patch('account.Portfolio', self.mock_portfolio_class):
            from account import Account
            acc = Account()
            acc.deposit(100.0)
            self.mock_transaction_class.assert_called_with(
                transaction_type="deposit", amount=100.0
            )

    def test_deposit_appends_transaction_to_list(self):
        with patch('account.Transaction', self.mock_transaction_class), \
             patch('account.Portfolio', self.mock_portfolio_class):
            from account import Account
            acc = Account()
            initial_count = len(acc.transactions)
            acc.deposit(100.0)
            self.assertEqual(len(acc.transactions), initial_count + 1)

    def test_deposit_zero_raises_value_error(self):
        with patch('account.Transaction', self.mock_transaction_class), \
             patch('account.Portfolio', self.mock_portfolio_class):
            from account import Account
            acc = Account()
            with self.assertRaises(ValueError) as ctx:
                acc.deposit(0.0)
            self.assertIn("positive", str(ctx.exception))

    def test_deposit_negative_raises_value_error(self):
        with patch('account.Transaction', self.mock_transaction_class), \
             patch('account.Portfolio', self.mock_portfolio_class):
            from account import Account
            acc = Account()
            with self.assertRaises(ValueError):
                acc.deposit(-50.0)

    def test_deposit_zero_does_not_change_balance(self):
        with patch('account.Transaction', self.mock_transaction_class), \
             patch('account.Portfolio', self.mock_portfolio_class):
            from account import Account
            acc = Account()
            try:
                acc.deposit(0.0)
            except ValueError:
                pass
            self.assertEqual(acc.balance, 0.0)

    def test_deposit_negative_does_not_change_balance(self):
        with patch('account.Transaction', self.mock_transaction_class), \
             patch('account.Portfolio', self.mock_portfolio_class):
            from account import Account
            acc = Account()
            try:
                acc.deposit(-10.0)
            except ValueError:
                pass
            self.assertEqual(acc.balance, 0.0)

    def test_deposit_small_amount(self):
        with patch('account.Transaction', self.mock_transaction_class), \
             patch('account.Portfolio', self.mock_portfolio_class):
            from account import Account
            acc = Account()
            acc.deposit(0.01)
            self.assertAlmostEqual(acc.balance, 0.01)

    def test_deposit_large_amount(self):
        with patch('account.Transaction', self.mock_transaction_class), \
             patch('account.Portfolio', self.mock_portfolio_class):
            from account import Account
            acc = Account()
            acc.deposit(1_000_000.0)
            self.assertEqual(acc.balance, 1_000_000.0)


class TestAccountWithdraw(unittest.TestCase):

    def setUp(self):
        self.mock_transaction_class = MagicMock()
        self.mock_portfolio_class = MagicMock()
        self.mock_transaction_instance = MagicMock()
        self.mock_portfolio_instance = MagicMock()
        self.mock_transaction_class.return_value = self.mock_transaction_instance
        self.mock_portfolio_class.return_value = self.mock_portfolio_instance

    def test_withdraw_decreases_balance(self):
        with patch('account.Transaction', self.mock_transaction_class), \
             patch('account.Portfolio', self.mock_portfolio_class):
            from account import Account
            acc = Account()
            acc.balance = 500.0
            acc.withdraw(200.0)
            self.assertEqual(acc.balance, 300.0)

    def test_withdraw_entire_balance(self):
        with patch('account.Transaction', self.mock_transaction_class), \
             patch('account.Portfolio', self.mock_portfolio_class):
            from account import Account
            acc = Account()
            acc.balance = 500.0
            acc.withdraw(500.0)
            self.assertEqual(acc.balance, 0.0)

    def test_withdraw_creates_transaction(self):
        with patch('account.Transaction', self.mock_transaction_class), \
             patch('account.Portfolio', self.mock_portfolio_class):
            from account import Account
            acc = Account()
            acc.balance = 500.0
            acc.withdraw(100.0)
            self.mock_transaction_class.assert_called_with(
                transaction_type="withdrawal", amount=100.0
            )

    def test_withdraw_appends_transaction(self):
        with patch('account.Transaction', self.mock_transaction_class), \
             patch('account.Portfolio', self.mock_portfolio_class):
            from account import Account
            acc = Account()
            acc.balance = 500.0
            initial_count = len(acc.transactions)
            acc.withdraw(100.0)
            self.assertEqual(len(acc.transactions), initial_count + 1)

    def test_withdraw_more_than_balance_raises_value_error(self):
        with patch('account.Transaction', self.mock_transaction_class), \
             patch('account.Portfolio', self.mock_portfolio_class):
            from account import Account
            acc = Account()
            acc.balance = 100.0
            with self.assertRaises(ValueError) as ctx:
                acc.withdraw(150.0)
            self.assertIn("Insufficient funds", str(ctx.exception))

    def test_withdraw_more_than_balance_does_not_change_balance(self):
        with patch('account.Transaction', self.mock_transaction_class), \
             patch('account.Portfolio', self.mock_portfolio_class):
            from account import Account
            acc = Account()
            acc.balance = 100.0
            try:
                acc.withdraw(150.0)
            except ValueError:
                pass
            self.assertEqual(acc.balance, 100.0)

    def test_withdraw_zero_raises_value_error(self):
        with patch('account.Transaction', self.mock_transaction_class), \
             patch('account.Portfolio', self.mock_portfolio_class):
            from account import Account
            acc = Account()
            acc.balance = 100.0
            with self.assertRaises(ValueError) as ctx:
                acc.withdraw(0.0)
            self.assertIn("positive", str(ctx.exception))

    def test_withdraw_negative_raises_value_error(self):
        with patch('account.Transaction', self.mock_transaction_class), \
             patch('account.Portfolio', self.mock_portfolio_class):
            from account import Account
            acc = Account()
            acc.balance = 100.0
            with self.assertRaises(ValueError):
                acc.withdraw(-10.0)

    def test_withdraw_zero_does_not_change_balance(self):
        with patch('account.Transaction', self.mock_transaction_class), \
             patch('account.Portfolio', self.mock_portfolio_class):
            from account import Account
            acc = Account()
            acc.balance = 100.0
            try:
                acc.withdraw(0.0)
            except ValueError:
                pass
            self.assertEqual(acc.balance, 100.0)

    def test_withdraw_negative_does_not_change_balance(self):
        with patch('account.Transaction', self.mock_transaction_class), \
             patch('account.Portfolio', self.mock_portfolio_class):
            from account import Account
            acc = Account()
            acc.balance = 100.0
            try:
                acc.withdraw(-10.0)
            except ValueError:
                pass
            self.assertEqual(acc.balance, 100.0)

    def test_withdraw_from_zero_balance_raises_value_error(self):
        with patch('account.Transaction', self.mock_transaction_class), \
             patch('account.Portfolio', self.mock_portfolio_class):
            from account import Account
            acc = Account()
            with self.assertRaises(ValueError):
                acc.withdraw(10.0)


class TestAccountBuyShares(unittest.TestCase):

    def setUp(self):
        self.mock_transaction_class = MagicMock()
        self.mock_portfolio_class = MagicMock()
        self.mock_transaction_instance = MagicMock()
        self.mock_portfolio_instance = MagicMock()
        self.mock_transaction_class.return_value = self.mock_transaction_instance
        self.mock_portfolio_class.return_value = self.mock_portfolio_instance

    def _make_account_with_balance(self, balance):
        with patch('account.Transaction', self.mock_transaction_class), \
             patch('account.Portfolio', self.mock_portfolio_class):
            from account import Account
            acc = Account()
            acc.balance = balance
            self.mock_transaction_class.reset_mock()
            return acc

    def test_buy_shares_reduces_balance(self):
        with patch('account.Transaction', self.mock_transaction_class), \
             patch('account.Portfolio', self.mock_portfolio_class):
            from account import Account
            acc = Account()
            acc.balance = 1000.0
            get_price = MagicMock(return_value=10.0)
            acc.buy_shares("AAPL", 5, get_price)
            self.assertEqual(acc.balance, 950.0)

    def test_buy_shares_calls_get_share_price(self):
        with patch('account.Transaction', self.mock_transaction_class), \
             patch('account.Portfolio', self.mock_portfolio_class):
            from account import Account
            acc = Account()
            acc.balance = 1000.0
            get_price = MagicMock(return_value=10.0)
            acc.buy_shares("AAPL", 5, get_price)
            get_price.assert_called_once_with("AAPL")

    def test_buy_shares_calls_portfolio_add_shares(self):
        with patch('account.Transaction', self.mock_transaction_class), \
             patch('account.Portfolio', self.mock_portfolio_class):
            from account import Account
            acc = Account()
            acc.balance = 1000.0
            get_price = MagicMock(return_value=10.0)
            acc.buy_shares("AAPL", 5, get_price)
            self.mock_portfolio_instance.add_shares.assert_called_once_with("AAPL", 5)

    def test_buy_shares_creates_buy_transaction(self):
        with patch('account.Transaction', self.mock_transaction_class), \
             patch('account.Portfolio', self.mock_portfolio_class):
            from account import Account
            acc = Account()
            acc.balance = 1000.0
            get_price = MagicMock(return_value=10.0)
            acc.buy_shares("AAPL", 5, get_price)
            self.mock_transaction_class.assert_called_with(
                transaction_type="buy",
                symbol="AAPL",
                quantity=5,
                price=10.0,
                amount=50.0
            )

    def test_buy_shares_appends_transaction(self):
        with patch('account.Transaction', self.mock_transaction_class), \
             patch('account.Portfolio', self.mock_portfolio_class):
            from account import Account
            acc = Account()
            acc.balance = 1000.0
            initial_count = len(acc.transactions)
            get_price = MagicMock(return_value=10.0)
            acc.buy_shares("AAPL", 5, get_price)
            self.assertEqual(len(acc.transactions), initial_count + 1)

    def test_buy_shares_insufficient_funds_raises_value_error(self):
        with patch('account.Transaction', self.mock_transaction_class), \
             patch('account.Portfolio', self.mock_portfolio_class):
            from account import Account
            acc = Account()
            acc.balance = 10.0
            get_price = MagicMock(return_value=10.0)
            with self.assertRaises(ValueError) as ctx:
                acc.buy_shares("AAPL", 5, get_price)
            self.assertIn("Insufficient funds", str(ctx.exception))

    def test_buy_shares_insufficient_funds_does_not_change_balance(self):
        with patch('account.Transaction', self.mock_transaction_class), \
             patch('account.Portfolio', self.mock_portfolio_class):
            from account import Account
            acc = Account()
            acc.balance = 10.0
            get_price = MagicMock(return_value=10.0)
            try:
                acc.buy_shares("AAPL", 5, get_price)
            except ValueError:
                pass
            self.assertEqual(acc.balance, 10.0)

    def test_buy_shares_insufficient_funds_does_not_add_shares(self):
        with patch('account.Transaction', self.mock_transaction_class), \
             patch('account.Portfolio', self.mock_portfolio_class):
            from account import Account
            acc = Account()
            acc.balance = 10.0
            get_price = MagicMock(return_value=10.0)
            try:
                acc.buy_shares("AAPL", 5, get_price)
            except ValueError:
                pass
            self.mock_portfolio_instance.add_shares.assert_not_called()

    def test_buy_shares_zero_quantity_raises_value_error(self):
        with patch('account.Transaction', self.mock_transaction_class), \
             patch('account.Portfolio', self.mock_portfolio_class):
            from account import Account
            acc = Account()
            acc.balance = 1000.0
            get_price = MagicMock(return_value=10.0)
            with self.assertRaises(ValueError) as ctx:
                acc.buy_shares("AAPL", 0, get_price)
            self.assertIn("positive", str(ctx.exception))

    def test_buy_shares_negative_quantity_raises_value_error(self):
        with patch('account.Transaction', self.mock_transaction_class), \
             patch('account.Portfolio', self.mock_portfolio_class):
            from account import Account
            acc = Account()
            acc.balance = 1000.0
            get_price = MagicMock(return_value=10.0)
            with self.assertRaises(ValueError):
                acc.buy_shares("AAPL", -3, get_price)

    def test_buy_shares_exact_balance(self):
        with patch('account.Transaction', self.mock_transaction_class), \
             patch('account.Portfolio', self.mock_portfolio_class):
            from account import Account
            acc = Account()
            acc.balance = 50.0
            get_price = MagicMock(return_value=10.0)
            acc.buy_shares("AAPL", 5, get_price)
            self.assertEqual(acc.balance, 0.0)

    def test_buy_shares_different_symbol(self):
        with patch('account.Transaction', self.mock_transaction_class), \
             patch('account.Portfolio', self.mock_portfolio_class):
            from account import Account
            acc = Account()
            acc.balance = 1000.0
            get_price = MagicMock(return_value=20.0)
            acc.buy_shares("GOOG", 3, get_price)
            get_price.assert_called_once_with("GOOG")
            self.mock_portfolio_instance.add_shares.assert_called_once_with("GOOG", 3)
            self.assertEqual(acc.balance, 940.0)


class TestAccountSellShares(unittest.TestCase):

    def setUp(self):
        self.mock_transaction_class = MagicMock()
        self.mock_portfolio_class = MagicMock()
        self.mock_transaction_instance = MagicMock()
        self.mock_portfolio_instance = MagicMock()
        self.mock_transaction_class.return_value = self.mock_transaction_instance
        self.mock_portfolio_class.return_value = self.mock_portfolio_instance

    def test_sell_shares_increases_balance(self):
        with patch('account.Transaction', self.mock_transaction_class), \
             patch('account.Portfolio', self.mock_portfolio_class):
            from account import Account
            self.mock_portfolio_instance.has_shares.return_value = True
            acc = Account()
            acc.balance = 100.0
            get_price = MagicMock(return_value=10.0)
            acc.sell_shares("AAPL", 5, get_price)
            self.assertEqual(acc.balance, 150.0)

    def test_sell_shares_calls_get_share_price(self):
        with patch('account.Transaction', self.mock_transaction_class), \
             patch('account.Portfolio', self.mock_portfolio_class):
            from account import Account
            self.mock_portfolio_instance.has_shares.return_value = True
            acc = Account()
            acc.balance = 100.0
            get_price = MagicMock(return_value=10.0)
            acc.sell_shares("AAPL", 5, get_price)
            get_price.assert_called_once_with("AAPL")

    def test_sell_shares_calls_portfolio_remove_shares(self):
        with patch('account.Transaction', self.mock_transaction_class), \
             patch('account.Portfolio', self.mock_portfolio_class):
            from account import Account
            self.mock_portfolio_instance.has_shares.return_value = True
            acc = Account()
            acc.balance = 100.0
            get_price = MagicMock(return_value=10.0)
            acc.sell_shares("AAPL", 5, get_price)
            self.mock_portfolio_instance.remove_shares.assert_called_once_with("AAPL", 5)

    def test_sell_shares_calls_portfolio_has_shares(self):
        with patch('account.Transaction', self.mock_transaction_class), \
             patch('account.Portfolio', self.mock_portfolio_class):
            from account import Account
            self.mock_portfolio_instance.has_shares.return_value = True
            acc = Account()
            acc.balance = 100.0
            get_price = MagicMock(return_value=10.0)
            acc.sell_shares("AAPL", 5, get_price)
            self.mock_portfolio_instance.has_shares.assert_called_once_with("AAPL", 5)

    def test_sell_shares_creates_sell_transaction(self):
        with patch('account.Transaction', self.mock_transaction_class), \
             patch('account.Portfolio', self.mock_portfolio_class):
            from account import Account
            self.mock_portfolio_instance.has_shares.return_value = True
            acc = Account()
            acc.balance = 100.0
            get_price = MagicMock(return_value=10.0)
            acc.sell_shares("AAPL", 5, get_price)
            self.mock_transaction_class.assert_called_with(
                transaction_type="sell",
                symbol="AAPL",
                quantity=5,
                price=10.0,
                amount=50.0
            )

    def test_sell_shares_appends_transaction(self):
        with patch('account.Transaction', self.mock_transaction_class), \
             patch('account.Portfolio', self.mock_portfolio_class):
            from account import Account
            self.mock_portfolio_instance.has_shares.return_value = True
            acc = Account()
            initial_count = len(acc.transactions)
            acc.balance = 100.0
            get_price = MagicMock(return_value=10.0)
            acc.sell_shares("AAPL", 5, get_price)
            self.assertEqual(len(acc.transactions), initial_count + 1)

    def test_sell_shares_insufficient_shares_raises_value_error(self):
        with patch('account.Transaction', self.mock_transaction_class), \
             patch('account.Portfolio', self.mock_portfolio_class):
            from account import Account
            self.mock_portfolio_instance.has_shares.return_value = False
            acc = Account()
            acc.balance = 100.0
            get_price = MagicMock(return_value=10.0)
            with self.assertRaises(ValueError) as ctx:
                acc.sell_shares("AAPL", 5, get_price)
            self.assertIn("Insufficient shares", str(ctx.exception))

    def test_sell_shares_insufficient_shares_does_not_change_balance(self):
        with patch('account.Transaction', self.mock_transaction_class), \
             patch('account.Portfolio', self.mock_portfolio_class):
            from account import Account
            self.mock_portfolio_instance.has_shares.return_value = False
            acc = Account()
            acc.balance = 100.0
            get_price = MagicMock(return_value=10.0)
            try:
                acc.sell_shares("AAPL", 5, get_price)
            except ValueError:
                pass
            self.assertEqual(acc.balance, 100.0)

    def test_sell_shares_insufficient_shares_does_not_remove_shares(self):
        with patch('account.Transaction', self.mock_transaction_class), \
             patch('account.Portfolio', self.mock_portfolio_class):
            from account import Account
            self.mock_portfolio_instance.has_shares.return_value = False
            acc = Account()
            acc.balance = 100.0
            get_price = MagicMock(return_value=10.0)
            try:
                acc.sell_shares("AAPL", 5, get_price)
            except ValueError:
                pass
            self.mock_portfolio_instance.remove_shares.assert_not_called()

    def test_sell_shares_zero_quantity_raises_value_error(self):
        with patch('account.Transaction', self.mock_transaction_class), \
             patch('account.Portfolio', self.mock_portfolio_class):
            from account import Account
            acc = Account()
            get_price = MagicMock(return_value=10.0)
            with self.assertRaises(ValueError) as ctx:
                acc.sell_shares("AAPL", 0, get_price)
            self.assertIn("positive", str(ctx.exception))

    def test_sell_shares_negative_quantity_raises_value_error(self):
        with patch('account.Transaction', self.mock_transaction_class), \
             patch('account.Portfolio', self.mock_portfolio_class):
            from account import Account
            acc = Account()
            get_price = MagicMock(return_value=10.0)
            with self.assertRaises(ValueError):
                acc.sell_shares("AAPL", -2, get_price)

    def test_sell_shares_zero_quantity_does_not_call_has_shares(self):
        with patch('account.Transaction', self.mock_transaction_class), \
             patch('account.Portfolio', self.mock_portfolio_class):
            from account import Account
            acc = Account()
            get_price = MagicMock(return_value=10.0)
            try:
                acc.sell_shares("AAPL", 0, get_price)
            except ValueError:
                pass
            self.mock_portfolio_instance.has_shares.assert_not_called()


class TestAccountGetHoldings(unittest.TestCase):

    def setUp(self):
        self.mock_transaction_class = MagicMock()
        self.mock_portfolio_class = MagicMock()
        self.mock_transaction_instance = MagicMock()
        self.mock_portfolio_instance = MagicMock()
        self.mock_transaction_class.return_value = self.mock_transaction_instance
        self.mock_portfolio_class.return_value = self.mock_portfolio_instance

    def test_get_holdings_delegates_to_portfolio(self):
        with patch('account.Transaction', self.mock_transaction_class), \
             patch('account.Portfolio', self.mock_portfolio_class):
            from account import Account
            expected_holdings = {"AAPL": 10, "GOOG": 5}
            self.mock_portfolio_instance.get_holdings.return_value = expected_holdings
            acc = Account()
            result = acc.get_holdings()
            self.mock_portfolio_instance.get_holdings.assert_called_once()
            self.assertEqual(result, expected_holdings)

    def test_get_holdings_returns_empty_dict_when_no_shares(self):
        with patch('account.Transaction', self.mock_transaction_class), \
             patch('account.Portfolio', self.mock_portfolio_class):
            from account import Account
            self.mock_portfolio_instance.get_holdings.return_value = {}
            acc = Account()
            result = acc.get_holdings()
            self.assertEqual(result, {})


class TestAccountGetPortfolioValue(unittest.TestCase):

    def setUp(self):
        self.mock_transaction_class = MagicMock()
        self.mock_portfolio_class = MagicMock()
        self.mock_transaction_instance = MagicMock()
        self.mock_portfolio_instance = MagicMock()
        self.mock_transaction_class.return_value = self.mock_transaction_instance
        self.mock_portfolio_class.return_value = self.mock_portfolio_instance

    def test_get_portfolio_value_delegates_to_portfolio(self):
        with patch('account.Transaction', self.mock_transaction_class), \
             patch('account.Portfolio', self.mock_portfolio_class):
            from account import Account
            self.mock_portfolio_instance.get_total_value.return_value = 500.0
            get_price = MagicMock(return_value=10.0)
            acc = Account()
            result = acc.get_portfolio_value(get_price)
            self.mock_portfolio_instance.get_total_value.assert_called_once_with(get_price)
            self.assertEqual(result, 500.0)

    def test_get_portfolio_value_returns_correct_value(self):
        with patch('account.Transaction', self.mock_transaction_class), \
             patch('account.Portfolio', self.mock_portfolio_class):
            from account import Account
            self.mock_portfolio_instance.get_total_value.return_value = 1200.0
            get_price = MagicMock(return_value=20.0)
            acc = Account()
            result = acc.get_portfolio_value(get_price)
            self.assertEqual(result, 1200.0)


class TestAccountGetTotalValue(unittest.TestCase):

    def setUp(self):
        self.mock_transaction_class = MagicMock()
        self.mock_portfolio_class = MagicMock()
        self.mock_transaction_instance = MagicMock()
        self.mock_portfolio_instance = MagicMock()
        self.mock_transaction_class.return_value = self.mock_transaction_instance
        self.mock_portfolio_class.return_value = self.mock_portfolio_instance

    def test_get_total_value_combines_balance_and_portfolio(self):
        with patch('account.Transaction', self.mock_transaction_class), \
             patch('account.Portfolio', self.mock_portfolio_class):
            from account import Account
            self.mock_portfolio_instance.get_total_value.return_value = 300.0
            acc = Account()
            acc.balance = 200.0
            get_price = MagicMock(return_value=10.0)
            result = acc.get_total_value(get_price)
            self.assertEqual(result, 500.0)

    def test_get_total_value_with_zero_portfolio_value(self):
        with patch('account.Transaction', self.mock_transaction_class), \
             patch('account.Portfolio', self.mock_portfolio_class):
            from account import Account
            self.mock_portfolio_instance.get_total_value.return_value = 0.0
            acc = Account()
            acc.balance = 400.0
            get_price = MagicMock(return_value=10.0)
            result = acc.get_total_value(get_price)
            self.assertEqual(result, 400.0)

    def test_get_total_value_with_zero_balance(self):
        with patch('account.Transaction', self.mock_transaction_class), \
             patch('account.Portfolio', self.mock_portfolio_class):
            from account import Account
            self.mock_portfolio_instance.get_total_value.return_value = 750.0
            acc = Account()
            acc.balance = 0.0
            get_price = MagicMock(return_value=10.0)
            result = acc.get_total_value(get_price)
            self.assertEqual(result, 750.0)

    def test_get_total_value_passes_get_share_price_to_portfolio(self):
        with patch('account.Transaction', self.mock_transaction_class), \
             patch('account.Portfolio', self.mock_portfolio_class):
            from account import Account
            self.mock_portfolio_instance.get_total_value.return_value = 0.0
            get_price = MagicMock(return_value=10.0)
            acc = Account()
            acc.get_total_value(get_price)
            self.mock_portfolio_instance.get_total_value.assert_called_once_with(get_price)


class TestAccountGetProfitLoss(unittest.TestCase):

    def setUp(self):
        self.mock_transaction_class = MagicMock()
        self.mock_portfolio_class = MagicMock()
        self.mock_transaction_instance = MagicMock()
        self.mock_portfolio_instance = MagicMock()
        self.mock_transaction_class.return_value = self.mock_transaction_instance
        self.mock_portfolio_class.return_value = self.mock_portfolio_instance

    def test_get_profit_loss_positive(self):
        with patch('account.Transaction', self.mock_transaction_class), \
             patch('account.Portfolio', self.mock_portfolio_class):
            from account import Account
            self.mock_portfolio_instance.get_total_value.return_value = 200.0
            acc = Account()
            acc.balance = 800.0
            acc.initial_deposit = 500.0
            get_price = MagicMock(return_value=10.0)
            result = acc.get_profit_loss(get_price)
            self.assertEqual(result, 500.0)

    def test_get_profit_loss_negative(self):
        with patch('account.Transaction', self.mock_transaction_class), \
             patch('account.Portfolio', self.mock_portfolio_class):
            from account import Account
            self.mock_portfolio_instance.get_total_value.return_value = 0.0
            acc = Account()
            acc.balance = 200.0
            acc.initial_deposit = 500.0
            get_price = MagicMock(return_value=10.0)
            result = acc.get_profit_loss(get_price)
            self.assertEqual(result, -300.0)

    def test_get_profit_loss_zero(self):
        with patch('account.Transaction', self.mock_transaction_class), \
             patch('account.Portfolio', self.mock_portfolio_class):
            from account import Account
            self.mock_portfolio_instance.get_total_value.return_value = 0.0
            acc = Account()
            acc.balance = 500.0
            acc.initial_deposit = 500.0
            get_price = MagicMock(return_value=10.0)
            result = acc.get_profit_loss(get_price)
            self.assertEqual(result, 0.0)

    def test_get_profit_loss_uses_initial_deposit(self):
        with patch('account.Transaction', self.mock_transaction_class), \
             patch('account.Portfolio', self.mock_portfolio_class):
            from account import Account
            self.mock_portfolio_instance.get_total_value.return_value = 100.0
            acc = Account()
            acc.balance = 900.0
            acc.initial_deposit = 1000.0
            get_price = MagicMock(return_value=10.0)
            result = acc.get_profit_loss(get_price)
            self.assertEqual(result, 0.0)

    def test_get_profit_loss_with_no_initial_deposit(self):
        with patch('account.Transaction', self.mock_transaction_class), \
             patch('account.Portfolio', self.mock_portfolio_class):
            from account import Account
            self.mock_portfolio_instance.get_total_value.return_value = 0.0
            acc = Account()
            acc.balance = 0.0
            acc.initial_deposit = 0.0
            get_price = MagicMock(return_value=10.0)
            result = acc.get_profit_loss(get_price)
            self.assertEqual(result, 0.0)


class TestAccountGetTransactions(unittest.TestCase):

    def setUp(self):
        self.mock_transaction_class = MagicMock()
        self.mock_portfolio_class = MagicMock()
        self.mock_transaction_instance = MagicMock()
        self.mock_portfolio_instance = MagicMock()
        self.mock_transaction_class.return_value = self.mock_transaction_instance
        self.mock_portfolio_class.return_value = self.mock_portfolio_instance

    def test_get_transactions_returns_list(self):
        with patch('account.Transaction', self.mock_transaction_class), \
             patch('account.Portfolio', self.mock_portfolio_class):
            from account import Account
            acc = Account()
            result = acc.get_transactions()
            self.assertIsInstance(result, list)

    def test_get_transactions_returns_empty_when_no_transactions(self):
        with patch('account.Transaction', self.mock_transaction_class), \
             patch('account.Portfolio', self.mock_portfolio_class):
            from account import Account
            acc = Account()
            result = acc.get_transactions()
            self.assertEqual(result, [])

    def test_get_transactions_returns_copy(self):
        with patch('account.Transaction', self.mock_transaction_class), \
             patch('account.Portfolio', self.mock_portfolio_class):
            from account import Account
            acc = Account()
            acc.deposit(100.0)
            result = acc.get_transactions()
            result.append("extra")
            self.assertNotEqual(len(acc.get_transactions()), len(result))

    def test_get_transactions_returns_all_transactions(self):
        with patch('account.Transaction', self.mock_transaction_class), \
             patch('account.Portfolio', self.mock_portfolio_class):
            from account import Account
            acc = Account()
            acc.deposit(100.0)
            acc.deposit(200.0)
            acc.withdraw(50.0)
            result = acc.get_transactions()
            self.assertEqual(len(result), 3)

    def test_get_transactions_contains_transaction_objects(self):
        with patch('account.Transaction', self.mock_transaction_class), \
             patch('account.Portfolio', self.mock_portfolio_class):
            from account import Account
            acc = Account()
            acc.deposit(100.0)
            result = acc.get_transactions()
            self.assertIn(self.mock_transaction_instance, result)


class TestAccountIntegrationLikeBehavior(unittest.TestCase):

    def setUp(self):
        self.mock_transaction_class = MagicMock()
        self.mock_portfolio_class = MagicMock()
        self.mock_portfolio_instance = MagicMock()
        self.mock_portfolio_class.return_value = self.mock_portfolio_instance

    def test_deposit_then_withdraw_correct_balance(self):
        with patch('account.Transaction', self.mock_transaction_class), \
             patch('account.Portfolio', self.mock_portfolio_class):
            from account import Account
            acc = Account()
            acc.deposit(500.0)
            acc.withdraw(200.0)
            self.assertEqual(acc.balance, 300.0)

    def test_multiple_deposits_and_withdrawals(self):
        with patch('account.Transaction', self.mock_transaction_class), \
             patch('account.Portfolio', self.mock_portfolio_class):
            from account import Account
            acc = Account()
            acc.deposit(1000.0)
            acc.deposit(500.0)
            acc.withdraw(300.0)
            acc.withdraw(200.0)
            self.assertEqual(acc.balance, 1000.0)

    def test_buy_then_sell_restores_balance(self):
        with patch('account.Transaction', self.mock_transaction_class), \
             patch('account.Portfolio', self.mock_portfolio_class):
            from account import Account
            self.mock_portfolio_instance.has_shares.return_value = True
            acc = Account()
            acc.balance = 1000.0
            get_price = MagicMock(return_value=10.0)
            acc.buy_shares("AAPL", 5, get_price)
            acc.sell_shares("AAPL", 5, get_price)
            self.assertEqual(acc.balance, 1000.0)

    def test_transaction_count_after_multiple_operations(self):
        with patch('account.Transaction', self.mock_transaction_class), \
             patch('account.Portfolio', self.mock_portfolio_class):
            from account import Account
            self.mock_portfolio_instance.has_shares.return_value = True
            acc = Account()
            acc.deposit(1000.0)
            acc.withdraw(100.0)
            get_price = MagicMock(return_value=10.0)
            acc.buy_shares("AAPL", 5, get_price)
            acc.sell_shares("AAPL", 5, get_price)
            self.assertEqual(len(acc.transactions), 4)

    def test_initial_deposit_not_changed_after_subsequent_deposits(self):
        with patch('account.Transaction', self.mock_transaction_class), \
             patch('account.Portfolio', self.mock_portfolio_class):
            from account import Account
            acc = Account(initial_deposit=500.0)
            acc.deposit(200.0)
            self.assertEqual(acc.initial_deposit, 500.0)

    def test_buy_shares_does_not_call_portfolio_has_shares(self):
        with patch('account.Transaction', self.mock_transaction_class), \
             patch('account.Portfolio', self.mock_portfolio_class):
            from account import Account
            acc = Account()
            acc.balance = 1000.0
            get_price = MagicMock(return_value=10.0)
            acc.buy_shares("AAPL", 5, get_price)
            self.mock_portfolio_instance.has_shares.assert_not_called()

    def test_sell_shares_does_not_call_portfolio_add_shares(self):
        with patch('account.Transaction', self.mock_transaction_class), \
             patch('account.Portfolio', self.mock_portfolio_class):
            from account import Account
            self.mock_portfolio_instance.has_shares.return_value = True
            acc = Account()
            acc.balance = 100.0
            get_price = MagicMock(return_value=10.0)
            acc.sell_shares("AAPL", 5, get_price)
            self.mock_portfolio_instance.add_shares.assert_not_called()


if __name__ == "__main__":
    unittest.main()