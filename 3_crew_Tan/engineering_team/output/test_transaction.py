import unittest
from datetime import datetime
from transaction import Transaction


class TestTransactionInit(unittest.TestCase):

    def test_deposit_transaction_valid(self):
        t = Transaction(transaction_type="deposit", amount=100.0)
        self.assertEqual(t.transaction_type, "deposit")
        self.assertEqual(t.amount, 100.0)
        self.assertIsNone(t.symbol)
        self.assertEqual(t.quantity, 0.0)
        self.assertEqual(t.price, 0.0)
        self.assertIsNotNone(t.timestamp)

    def test_withdrawal_transaction_valid(self):
        t = Transaction(transaction_type="withdrawal", amount=50.0)
        self.assertEqual(t.transaction_type, "withdrawal")
        self.assertEqual(t.amount, 50.0)

    def test_buy_transaction_valid(self):
        t = Transaction(transaction_type="buy", symbol="AAPL", quantity=10, price=150.0)
        self.assertEqual(t.transaction_type, "buy")
        self.assertEqual(t.symbol, "AAPL")
        self.assertEqual(t.quantity, 10)
        self.assertEqual(t.price, 150.0)

    def test_sell_transaction_valid(self):
        t = Transaction(transaction_type="sell", symbol="GOOG", quantity=5, price=200.0)
        self.assertEqual(t.transaction_type, "sell")
        self.assertEqual(t.symbol, "GOOG")
        self.assertEqual(t.quantity, 5)
        self.assertEqual(t.price, 200.0)

    def test_invalid_transaction_type_raises_value_error(self):
        with self.assertRaises(ValueError):
            Transaction(transaction_type="transfer", amount=100.0)

    def test_invalid_transaction_type_empty_string(self):
        with self.assertRaises(ValueError):
            Transaction(transaction_type="")

    def test_invalid_transaction_type_none_raises_value_error(self):
        with self.assertRaises(ValueError):
            Transaction(transaction_type=None)

    def test_invalid_transaction_type_random_string(self):
        with self.assertRaises(ValueError):
            Transaction(transaction_type="random_type")

    def test_timestamp_defaults_to_now_when_not_provided(self):
        before = datetime.now()
        t = Transaction(transaction_type="deposit", amount=100.0)
        after = datetime.now()
        self.assertGreaterEqual(t.timestamp, before)
        self.assertLessEqual(t.timestamp, after)

    def test_custom_timestamp_is_stored(self):
        custom_time = datetime(2023, 6, 15, 10, 30, 0)
        t = Transaction(transaction_type="deposit", amount=100.0, timestamp=custom_time)
        self.assertEqual(t.timestamp, custom_time)

    def test_timestamp_none_triggers_default(self):
        t = Transaction(transaction_type="deposit", amount=100.0, timestamp=None)
        self.assertIsInstance(t.timestamp, datetime)

    def test_default_amount_is_zero(self):
        t = Transaction(transaction_type="deposit")
        self.assertEqual(t.amount, 0.0)

    def test_default_quantity_is_zero(self):
        t = Transaction(transaction_type="buy", symbol="AAPL", price=100.0)
        self.assertEqual(t.quantity, 0.0)

    def test_default_price_is_zero(self):
        t = Transaction(transaction_type="buy", symbol="AAPL", quantity=5)
        self.assertEqual(t.price, 0.0)

    def test_default_symbol_is_none(self):
        t = Transaction(transaction_type="deposit", amount=100.0)
        self.assertIsNone(t.symbol)

    def test_symbol_stored_correctly(self):
        t = Transaction(transaction_type="buy", symbol="TSLA", quantity=3, price=700.0)
        self.assertEqual(t.symbol, "TSLA")

    def test_amount_stored_as_float(self):
        t = Transaction(transaction_type="deposit", amount=200)
        self.assertEqual(t.amount, 200)

    def test_quantity_stored_correctly(self):
        t = Transaction(transaction_type="sell", symbol="AMZN", quantity=7, price=3000.0)
        self.assertEqual(t.quantity, 7)

    def test_price_stored_correctly(self):
        t = Transaction(transaction_type="sell", symbol="AMZN", quantity=7, price=3000.0)
        self.assertEqual(t.price, 3000.0)

    def test_all_valid_transaction_types(self):
        valid_types = ["deposit", "withdrawal", "buy", "sell"]
        for t_type in valid_types:
            t = Transaction(transaction_type=t_type)
            self.assertEqual(t.transaction_type, t_type)


class TestTransactionRepr(unittest.TestCase):

    def test_repr_contains_transaction_type(self):
        t = Transaction(transaction_type="deposit", amount=100.0)
        result = repr(t)
        self.assertIn("deposit", result)

    def test_repr_contains_amount(self):
        t = Transaction(transaction_type="deposit", amount=100.0)
        result = repr(t)
        self.assertIn("100.0", result)

    def test_repr_contains_symbol(self):
        t = Transaction(transaction_type="buy", symbol="AAPL", quantity=10, price=150.0)
        result = repr(t)
        self.assertIn("AAPL", result)

    def test_repr_contains_quantity(self):
        t = Transaction(transaction_type="buy", symbol="AAPL", quantity=10, price=150.0)
        result = repr(t)
        self.assertIn("10", result)

    def test_repr_contains_price(self):
        t = Transaction(transaction_type="buy", symbol="AAPL", quantity=10, price=150.0)
        result = repr(t)
        self.assertIn("150.0", result)

    def test_repr_contains_timestamp(self):
        custom_time = datetime(2023, 6, 15, 10, 30, 0)
        t = Transaction(transaction_type="deposit", amount=100.0, timestamp=custom_time)
        result = repr(t)
        self.assertIn(str(custom_time), result)

    def test_repr_starts_with_transaction(self):
        t = Transaction(transaction_type="deposit", amount=100.0)
        result = repr(t)
        self.assertTrue(result.startswith("Transaction("))

    def test_repr_symbol_none_for_deposit(self):
        t = Transaction(transaction_type="deposit", amount=100.0)
        result = repr(t)
        self.assertIn("None", result)

    def test_repr_sell_transaction(self):
        t = Transaction(transaction_type="sell", symbol="GOOG", quantity=5, price=200.0)
        result = repr(t)
        self.assertIn("sell", result)
        self.assertIn("GOOG", result)
        self.assertIn("5", result)
        self.assertIn("200.0", result)


class TestTransactionStr(unittest.TestCase):

    def test_str_deposit_format(self):
        custom_time = datetime(2023, 6, 15, 10, 30, 0)
        t = Transaction(transaction_type="deposit", amount=100.0, timestamp=custom_time)
        result = str(t)
        self.assertIn("Deposit", result)
        self.assertIn("$100.00", result)
        self.assertIn(str(custom_time), result)

    def test_str_withdrawal_format(self):
        custom_time = datetime(2023, 6, 15, 10, 30, 0)
        t = Transaction(transaction_type="withdrawal", amount=50.0, timestamp=custom_time)
        result = str(t)
        self.assertIn("Withdrawal", result)
        self.assertIn("$50.00", result)
        self.assertIn(str(custom_time), result)

    def test_str_buy_format(self):
        custom_time = datetime(2023, 6, 15, 10, 30, 0)
        t = Transaction(transaction_type="buy", symbol="AAPL", quantity=10, price=150.0, timestamp=custom_time)
        result = str(t)
        self.assertIn("Bought", result)
        self.assertIn("10", result)
        self.assertIn("AAPL", result)
        self.assertIn("$150.00", result)
        self.assertIn(str(custom_time), result)

    def test_str_sell_format(self):
        custom_time = datetime(2023, 6, 15, 10, 30, 0)
        t = Transaction(transaction_type="sell", symbol="GOOG", quantity=5, price=200.0, timestamp=custom_time)
        result = str(t)
        self.assertIn("Sold", result)
        self.assertIn("5", result)
        self.assertIn("GOOG", result)
        self.assertIn("$200.00", result)
        self.assertIn(str(custom_time), result)

    def test_str_buy_total_calculation(self):
        custom_time = datetime(2023, 6, 15, 10, 30, 0)
        t = Transaction(transaction_type="buy", symbol="AAPL", quantity=10, price=150.0, timestamp=custom_time)
        result = str(t)
        self.assertIn("$1500.00", result)

    def test_str_sell_total_calculation(self):
        custom_time = datetime(2023, 6, 15, 10, 30, 0)
        t = Transaction(transaction_type="sell", symbol="GOOG", quantity=5, price=200.0, timestamp=custom_time)
        result = str(t)
        self.assertIn("$1000.00", result)

    def test_str_deposit_amount_two_decimal_places(self):
        custom_time = datetime(2023, 6, 15, 10, 30, 0)
        t = Transaction(transaction_type="deposit", amount=99.9, timestamp=custom_time)
        result = str(t)
        self.assertIn("$99.90", result)

    def test_str_withdrawal_amount_two_decimal_places(self):
        custom_time = datetime(2023, 6, 15, 10, 30, 0)
        t = Transaction(transaction_type="withdrawal", amount=10.5, timestamp=custom_time)
        result = str(t)
        self.assertIn("$10.50", result)

    def test_str_buy_contains_shares_label(self):
        custom_time = datetime(2023, 6, 15, 10, 30, 0)
        t = Transaction(transaction_type="buy", symbol="AAPL", quantity=10, price=150.0, timestamp=custom_time)
        result = str(t)
        self.assertIn("share(s)", result)

    def test_str_sell_contains_shares_label(self):
        custom_time = datetime(2023, 6, 15, 10, 30, 0)
        t = Transaction(transaction_type="sell", symbol="TSLA", quantity=3, price=700.0, timestamp=custom_time)
        result = str(t)
        self.assertIn("share(s)", result)

    def test_str_buy_contains_at_keyword(self):
        custom_time = datetime(2023, 6, 15, 10, 30, 0)
        t = Transaction(transaction_type="buy", symbol="AAPL", quantity=10, price=150.0, timestamp=custom_time)
        result = str(t)
        self.assertIn("at", result)

    def test_str_sell_contains_total_label(self):
        custom_time = datetime(2023, 6, 15, 10, 30, 0)
        t = Transaction(transaction_type="sell", symbol="AMZN", quantity=2, price=3000.0, timestamp=custom_time)
        result = str(t)
        self.assertIn("Total", result)

    def test_str_deposit_timestamp_in_brackets(self):
        custom_time = datetime(2023, 6, 15, 10, 30, 0)
        t = Transaction(transaction_type="deposit", amount=100.0, timestamp=custom_time)
        result = str(t)
        self.assertTrue(result.startswith("["))


class TestTransactionTypes(unittest.TestCase):

    def test_transaction_types_class_attribute_exists(self):
        self.assertTrue(hasattr(Transaction, "TRANSACTION_TYPES"))

    def test_transaction_types_contains_deposit(self):
        self.assertIn("deposit", Transaction.TRANSACTION_TYPES)

    def test_transaction_types_contains_withdrawal(self):
        self.assertIn("withdrawal", Transaction.TRANSACTION_TYPES)

    def test_transaction_types_contains_buy(self):
        self.assertIn("buy", Transaction.TRANSACTION_TYPES)

    def test_transaction_types_contains_sell(self):
        self.assertIn("sell", Transaction.TRANSACTION_TYPES)

    def test_transaction_types_is_set(self):
        self.assertIsInstance(Transaction.TRANSACTION_TYPES, set)

    def test_transaction_types_has_four_entries(self):
        self.assertEqual(len(Transaction.TRANSACTION_TYPES), 4)


class TestTransactionEdgeCases(unittest.TestCase):

    def test_zero_amount_deposit(self):
        t = Transaction(transaction_type="deposit", amount=0.0)
        self.assertEqual(t.amount, 0.0)

    def test_large_amount_deposit(self):
        t = Transaction(transaction_type="deposit", amount=1_000_000.0)
        self.assertEqual(t.amount, 1_000_000.0)

    def test_zero_quantity_buy(self):
        t = Transaction(transaction_type="buy", symbol="AAPL", quantity=0, price=150.0)
        self.assertEqual(t.quantity, 0)

    def test_zero_price_buy(self):
        t = Transaction(transaction_type="buy", symbol="AAPL", quantity=10, price=0.0)
        self.assertEqual(t.price, 0.0)

    def test_fractional_quantity_buy(self):
        t = Transaction(transaction_type="buy", symbol="AAPL", quantity=0.5, price=150.0)
        self.assertEqual(t.quantity, 0.5)

    def test_fractional_price_sell(self):
        t = Transaction(transaction_type="sell", symbol="GOOG", quantity=1, price=0.01)
        self.assertEqual(t.price, 0.01)

    def test_str_zero_total_buy(self):
        custom_time = datetime(2023, 6, 15, 10, 30, 0)
        t = Transaction(transaction_type="buy", symbol="AAPL", quantity=0, price=150.0, timestamp=custom_time)
        result = str(t)
        self.assertIn("$0.00", result)

    def test_different_symbols_stored_correctly(self):
        symbols = ["AAPL", "GOOG", "TSLA", "AMZN", "MSFT"]
        for symbol in symbols:
            t = Transaction(transaction_type="buy", symbol=symbol, quantity=1, price=100.0)
            self.assertEqual(t.symbol, symbol)

    def test_transaction_type_case_sensitive(self):
        with self.assertRaises(ValueError):
            Transaction(transaction_type="Deposit")

    def test_transaction_type_case_sensitive_upper(self):
        with self.assertRaises(ValueError):
            Transaction(transaction_type="BUY")

    def test_transaction_type_with_spaces_invalid(self):
        with self.assertRaises(ValueError):
            Transaction(transaction_type=" deposit")

    def test_multiple_transactions_independent(self):
        t1 = Transaction(transaction_type="deposit", amount=100.0)
        t2 = Transaction(transaction_type="withdrawal", amount=50.0)
        self.assertNotEqual(t1.transaction_type, t2.transaction_type)
        self.assertNotEqual(t1.amount, t2.amount)

    def test_buy_transaction_str_does_not_contain_deposit_keywords(self):
        custom_time = datetime(2023, 6, 15, 10, 30, 0)
        t = Transaction(transaction_type="buy", symbol="AAPL", quantity=10, price=150.0, timestamp=custom_time)
        result = str(t)
        self.assertNotIn("Deposit", result)
        self.assertNotIn("Withdrawal", result)

    def test_deposit_str_does_not_contain_bought_sold(self):
        custom_time = datetime(2023, 6, 15, 10, 30, 0)
        t = Transaction(transaction_type="deposit", amount=100.0, timestamp=custom_time)
        result = str(t)
        self.assertNotIn("Bought", result)
        self.assertNotIn("Sold", result)

    def test_value_error_message_contains_invalid_type(self):
        try:
            Transaction(transaction_type="invalid_type")
        except ValueError as e:
            self.assertIn("invalid_type", str(e))

    def test_value_error_message_contains_valid_types_hint(self):
        try:
            Transaction(transaction_type="invalid_type")
        except ValueError as e:
            error_msg = str(e)
            self.assertTrue(
                any(t_type in error_msg for t_type in ["deposit", "withdrawal", "buy", "sell"])
            )


if __name__ == "__main__":
    unittest.main()