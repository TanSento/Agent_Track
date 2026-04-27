import unittest
from accounts import (
    Account,
    get_share_price,
    InsufficientFundsError,
    InsufficientSharesError
)


class TestGetSharePrice(unittest.TestCase):
    def test_valid_symbol_uppercase(self):
        self.assertEqual(get_share_price('AAPL'), 150.00)
        self.assertEqual(get_share_price('TSLA'), 250.00)
        self.assertEqual(get_share_price('GOOGL'), 2800.00)

    def test_valid_symbol_lowercase(self):
        self.assertEqual(get_share_price('aapl'), 150.00)

    def test_valid_symbol_mixed_case(self):
        self.assertEqual(get_share_price('GoOgL'), 2800.00)

    def test_unknown_symbol(self):
        with self.assertRaises(ValueError) as context:
            get_share_price('MSFT')
        self.assertIn('Unknown symbol', str(context.exception))


class TestAccountInit(unittest.TestCase):
    def test_positive_initial_deposit(self):
        account = Account(1000.00)
        self.assertEqual(account.get_balance(), 1000.00)
        self.assertEqual(account.get_holdings(), {})
        self.assertEqual(len(account.get_transactions()), 1)
        self.assertEqual(account.get_transactions()[0]['type'], 'deposit')
        self.assertEqual(account.get_transactions()[0]['amount'], 1000.00)

    def test_zero_initial_deposit(self):
        account = Account(0.0)
        self.assertEqual(account.get_balance(), 0.0)
        self.assertEqual(account.get_holdings(), {})
        self.assertEqual(len(account.get_transactions()), 0)

    def test_negative_initial_deposit(self):
        with self.assertRaises(ValueError):
            Account(-100.0)


class TestAccountDeposit(unittest.TestCase):
    def setUp(self):
        self.account = Account(500.0)

    def test_deposit_positive_amount(self):
        self.account.deposit(200.0)
        self.assertEqual(self.account.get_balance(), 700.0)
        transactions = self.account.get_transactions()
        self.assertEqual(len(transactions), 2)
        last_txn = transactions[-1]
        self.assertEqual(last_txn['type'], 'deposit')
        self.assertEqual(last_txn['amount'], 200.0)
        self.assertIn('timestamp', last_txn)

    def test_deposit_zero(self):
        self.account.deposit(0.0)
        self.assertEqual(self.account.get_balance(), 500.0)

    def test_deposit_negative_amount(self):
        with self.assertRaises(ValueError) as context:
            self.account.deposit(-50.0)
        self.assertIn('cannot be negative', str(context.exception))


class TestAccountWithdraw(unittest.TestCase):
    def setUp(self):
        self.account = Account(1000.0)

    def test_withdraw_valid_amount(self):
        self.account.withdraw(400.0)
        self.assertEqual(self.account.get_balance(), 600.0)
        self.assertEqual(len(self.account.get_transactions()), 2)

    def test_withdraw_zero(self):
        self.account.withdraw(0.0)
        self.assertEqual(self.account.get_balance(), 1000.0)

    def test_withdraw_negative(self):
        with self.assertRaises(ValueError):
            self.account.withdraw(-100.0)

    def test_withdraw_insufficient_funds(self):
        with self.assertRaises(InsufficientFundsError) as context:
            self.account.withdraw(1500.0)
        self.assertIn('Insufficient funds', str(context.exception))
        self.assertEqual(self.account.get_balance(), 1000.0)  # unchanged

    def test_withdraw_all_funds(self):
        self.account.withdraw(1000.0)
        self.assertEqual(self.account.get_balance(), 0.0)


class TestAccountBuyShares(unittest.TestCase):
    def setUp(self):
        self.account = Account(5000.0)

    def test_buy_valid_shares(self):
        self.account.buy_shares('AAPL', 10)
        balance = 5000.0 - (150.00 * 10)
        self.assertEqual(self.account.get_balance(), balance)
        self.assertEqual(self.account.get_holdings(), {'AAPL': 10})
        txn = self.account.get_transactions()[-1]
        self.assertEqual(txn['type'], 'buy')
        self.assertEqual(txn['symbol'], 'AAPL')
        self.assertEqual(txn['quantity'], 10)
        self.assertEqual(txn['price'], 150.00)
        self.assertEqual(txn['total_cost'], 1500.00)

    def test_buy_multiple_symbols(self):
        self.account.buy_shares('AAPL', 5)
        self.account.buy_shares('TSLA', 2)
        self.assertEqual(self.account.get_holdings(), {'AAPL': 5, 'TSLA': 2})
        expected_balance = 5000.0 - (150*5 + 250*2)
        self.assertEqual(self.account.get_balance(), expected_balance)

    def test_buy_symbol_case_insensitive(self):
        self.account.buy_shares('aapl', 3)
        self.assertEqual(self.account.get_holdings()['AAPL'], 3)

    def test_buy_zero_quantity(self):
        with self.assertRaises(ValueError):
            self.account.buy_shares('AAPL', 0)

    def test_buy_negative_quantity(self):
        with self.assertRaises(ValueError):
            self.account.buy_shares('AAPL', -5)

    def test_buy_insufficient_funds(self):
        with self.assertRaises(InsufficientFundsError):
            self.account.buy_shares('GOOGL', 10)  # would cost 28000


class TestAccountSellShares(unittest.TestCase):
    def setUp(self):
        self.account = Account(5000.0)
        self.account.buy_shares('AAPL', 10)
        self.account.buy_shares('TSLA', 5)

    def test_sell_partial_shares(self):
        self.account.sell_shares('AAPL', 4)
        self.assertEqual(self.account.get_holdings()['AAPL'], 6)
        expected_balance = 5000.0 - (150*10 + 250*5) + (150*4)
        self.assertEqual(self.account.get_balance(), expected_balance)
        txn = self.account.get_transactions()[-1]
        self.assertEqual(txn['type'], 'sell')
        self.assertEqual(txn['symbol'], 'AAPL')
        self.assertEqual(txn['quantity'], 4)
        self.assertEqual(txn['price'], 150.00)
        self.assertEqual(txn['total_proceeds'], 600.00)

    def test_sell_all_shares_of_symbol(self):
        self.account.sell_shares('TSLA', 5)
        self.assertNotIn('TSLA', self.account.get_holdings())

    def test_sell_zero_quantity(self):
        with self.assertRaises(ValueError):
            self.account.sell_shares('AAPL', 0)

    def test_sell_negative_quantity(self):
        with self.assertRaises(ValueError):
            self.account.sell_shares('AAPL', -1)

    def test_sell_insufficient_shares(self):
        with self.assertRaises(InsufficientSharesError):
            self.account.sell_shares('AAPL', 100)

    def test_sell_symbol_not_owned(self):
        with self.assertRaises(InsufficientSharesError):
            self.account.sell_shares('GOOGL', 1)

    def test_sell_case_insensitive_symbol(self):
        self.account.sell_shares('aapl', 2)
        self.assertEqual(self.account.get_holdings()['AAPL'], 8)


class TestPortfolioValue(unittest.TestCase):
    def test_empty_portfolio(self):
        account = Account(1000.0)
        self.assertEqual(account.calculate_portfolio_value(), 0.0)

    def test_portfolio_with_holdings(self):
        account = Account(10000.0)
        account.buy_shares('AAPL', 10)
        account.buy_shares('GOOGL', 2)
        expected_value = 150*10 + 2800*2
        self.assertEqual(account.calculate_portfolio_value(), expected_value)

    def test_after_sell(self):
        account = Account(10000.0)
        account.buy_shares('TSLA', 4)
        account.sell_shares('TSLA', 2)
        expected_value = 250 * 2
        self.assertEqual(account.calculate_portfolio_value(), expected_value)


class TestProfitLoss(unittest.TestCase):
    def test_no_trades_only_deposits(self):
        account = Account(500.0)
        account.deposit(300.0)
        # Only cash, no trades. Current total = balance = 800, net invested = 800, profit/loss = 0
        self.assertEqual(account.calculate_profit_loss(), 0.0)

    def test_withdraw_no_trades(self):
        account = Account(1000.0)
        account.withdraw(200.0)
        # Balance 800, no portfolio, net invested = 1000-200=800, profit=0
        self.assertEqual(account.calculate_profit_loss(), 0.0)

    def test_profit_from_share_appreciation(self):
        # Since prices are fixed, we can't simulate profit. But profit/loss calculation
        # uses current price from get_share_price, same as buy/sell prices. So no intrinsic profit.
        # However, we can test after deposit, buy, sell. But prices are constant => p/l zero.
        account = Account(1000.0)
        account.buy_shares('AAPL', 1)
        self.assertEqual(account.calculate_profit_loss(), 0.0)

    def test_profit_loss_with_transactions(self):
        # Edge: deposit, buy, then deposit more. But no price change.
        account = Account(1000.0)
        account.buy_shares('AAPL', 1)
        account.deposit(500.0)
        # Total deposits = 1500, no withdrawals, net invested = 1500.
        # Balance = 1000 - 150 + 500 = 1350, portfolio value = 150, total = 1500 => P/L 0
        self.assertEqual(account.calculate_profit_loss(), 0.0)


class TestGetProfitLossReport(unittest.TestCase):
    def test_report_structure(self):
        account = Account(1000.0)
        account.deposit(500.0)
        account.withdraw(200.0)
        account.buy_shares('TSLA', 2)
        report = account.get_profit_loss()
        self.assertIsInstance(report, dict)
        self.assertIn('profit_loss', report)
        self.assertIn('profit_loss_percentage', report)
        self.assertIn('current_total_value', report)
        self.assertIn('total_deposited', report)
        self.assertIn('total_withdrawn', report)
        self.assertIn('net_invested', report)
        # net invested = 1000+500-200=1300, current total = balance + portfolio value:
        # balance = 1000+500-200 - 500 = 800, portfolio = 2*250=500 => total 1300, profit=0, percentage 0
        self.assertEqual(report['total_deposited'], 1500.0)
        self.assertEqual(report['total_withdrawn'], 200.0)
        self.assertEqual(report['net_invested'], 1300.0)
        self.assertEqual(report['current_total_value'], 1300.0)
        self.assertEqual(report['profit_loss'], 0.0)
        self.assertEqual(report['profit_loss_percentage'], 0.0)

    def test_report_zero_net_invested(self):
        account = Account(0.0)
        account.deposit(200.0)
        account.withdraw(200.0)
        # net invested 0
        report = account.get_profit_loss()
        self.assertEqual(report['profit_loss_percentage'], 0.0)

    def test_report_with_profit(self):
        # Can't generate real profit because prices fixed, but can test formula.
        pass  # Already tested 0 profit.


class TestHoldingsAndTransactions(unittest.TestCase):
    def test_get_holdings_returns_copy(self):
        account = Account(1000.0)
        account.buy_shares('AAPL', 5)
        holdings = account.get_holdings()
        holdings['FAKE'] = 10  # modify copy
        self.assertNotIn('FAKE', account.get_holdings())

    def test_get_transactions_returns_copy(self):
        account = Account(1000.0)
        transactions = account.get_transactions()
        transactions.append({'type': 'hack'})
        self.assertEqual(len(account.get_transactions()), 1)  # original unchanged

    def test_get_holdings_after_sell_all(self):
        account = Account(1000.0)
        account.buy_shares('GOOGL', 1)
        account.sell_shares('GOOGL', 1)
        self.assertEqual(account.get_holdings(), {})


class TestTransactionHistory(unittest.TestCase):
    def setUp(self):
        self.account = Account(1000.0)

    def test_initial_deposit_transaction(self):
        txn = self.account.get_transactions()[0]
        self.assertEqual(txn['type'], 'deposit')
        self.assertEqual(txn['amount'], 1000.0)
        self.assertIsInstance(txn['timestamp'], str)

    def test_deposit_transaction_recorded(self):
        self.account.deposit(500.0)
        txn = self.account.get_transactions()[-1]
        self.assertEqual(txn['type'], 'deposit')
        self.assertEqual(txn['amount'], 500.0)

    def test_withdraw_transaction_recorded(self):
        self.account.withdraw(200.0)
        txn = self.account.get_transactions()[-1]
        self.assertEqual(txn['type'], 'withdrawal')
        self.assertEqual(txn['amount'], 200.0)

    def test_buy_transaction_recorded(self):
        self.account.buy_shares('TSLA', 2)
        txn = self.account.get_transactions()[-1]
        self.assertEqual(txn['type'], 'buy')
        self.assertEqual(txn['symbol'], 'TSLA')
        self.assertEqual(txn['quantity'], 2)
        self.assertEqual(txn['price'], 250.0)
        self.assertEqual(txn['total_cost'], 500.0)

    def test_sell_transaction_recorded(self):
        self.account.buy_shares('AAPL', 5)
        self.account.sell_shares('AAPL', 2)
        txn = self.account.get_transactions()[-1]
        self.assertEqual(txn['type'], 'sell')
        self.assertEqual(txn['symbol'], 'AAPL')
        self.assertEqual(txn['quantity'], 2)
        self.assertEqual(txn['price'], 150.0)
        self.assertEqual(txn['total_proceeds'], 300.0)


class TestEdgeCases(unittest.TestCase):
    def test_account_with_zero_initial_deposit_buy_fails(self):
        account = Account(0.0)
        with self.assertRaises(InsufficientFundsError):
            account.buy_shares('AAPL', 1)

    def test_deposit_then_zero_balance_withdraw_all(self):
        account = Account(500.0)
        account.withdraw(500.0)
        self.assertEqual(account.get_balance(), 0.0)

    def test_buy_and_sell_same_quantity(self):
        account = Account(10000.0)
        account.buy_shares('GOOGL', 2)
        account.sell_shares('GOOGL', 2)
        self.assertNotIn('GOOGL', account.get_holdings())
        # Balance should be original minus cost plus proceeds: cost=5600, proceeds=5600, balance = original
        self.assertEqual(account.get_balance(), 10000.0)


if __name__ == '__main__':
    unittest.main()