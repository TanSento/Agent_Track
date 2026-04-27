import pytest
from unittest.mock import MagicMock, patch
from share_price_service import SharePriceService, get_share_price


class TestGetSharePriceFunction:
    """Tests for the standalone get_share_price function."""

    def test_get_share_price_aapl(self):
        price = get_share_price("AAPL")
        assert price == 150.00

    def test_get_share_price_tsla(self):
        price = get_share_price("TSLA")
        assert price == 700.00

    def test_get_share_price_googl(self):
        price = get_share_price("GOOGL")
        assert price == 2800.00

    def test_get_share_price_unknown_symbol_raises_value_error(self):
        with pytest.raises(ValueError) as exc_info:
            get_share_price("UNKNOWN")
        assert "Unknown symbol: UNKNOWN" in str(exc_info.value)

    def test_get_share_price_empty_string_raises_value_error(self):
        with pytest.raises(ValueError) as exc_info:
            get_share_price("")
        assert "Unknown symbol:" in str(exc_info.value)

    def test_get_share_price_lowercase_raises_value_error(self):
        with pytest.raises(ValueError):
            get_share_price("aapl")

    def test_get_share_price_returns_float_aapl(self):
        price = get_share_price("AAPL")
        assert isinstance(price, float)

    def test_get_share_price_returns_float_tsla(self):
        price = get_share_price("TSLA")
        assert isinstance(price, float)

    def test_get_share_price_returns_float_googl(self):
        price = get_share_price("GOOGL")
        assert isinstance(price, float)

    def test_get_share_price_msft_raises_value_error(self):
        with pytest.raises(ValueError) as exc_info:
            get_share_price("MSFT")
        assert "Unknown symbol: MSFT" in str(exc_info.value)

    def test_get_share_price_none_raises_value_error(self):
        with pytest.raises((ValueError, TypeError, KeyError)):
            get_share_price(None)


class TestSharePriceServiceInit:
    """Tests for SharePriceService initialization."""

    def test_init_with_no_args_uses_default_price_function(self):
        service = SharePriceService()
        assert service._get_share_price is get_share_price

    def test_init_with_none_uses_default_price_function(self):
        service = SharePriceService(price_function=None)
        assert service._get_share_price is get_share_price

    def test_init_with_custom_price_function(self):
        custom_fn = MagicMock(return_value=123.45)
        service = SharePriceService(price_function=custom_fn)
        assert service._get_share_price is custom_fn

    def test_init_stores_custom_function_correctly(self):
        def my_price_fn(symbol):
            return 999.99

        service = SharePriceService(price_function=my_price_fn)
        assert service._get_share_price is my_price_fn

    def test_init_default_is_callable(self):
        service = SharePriceService()
        assert callable(service._get_share_price)

    def test_init_custom_function_is_stored_as_callable(self):
        custom_fn = lambda s: 50.0
        service = SharePriceService(price_function=custom_fn)
        assert callable(service._get_share_price)


class TestSharePriceServiceGetPriceWithDefaultFunction:
    """Tests for SharePriceService.get_price using the default price function."""

    def setup_method(self):
        self.service = SharePriceService()

    def test_get_price_aapl_returns_correct_price(self):
        price = self.service.get_price("AAPL")
        assert price == 150.00

    def test_get_price_tsla_returns_correct_price(self):
        price = self.service.get_price("TSLA")
        assert price == 700.00

    def test_get_price_googl_returns_correct_price(self):
        price = self.service.get_price("GOOGL")
        assert price == 2800.00

    def test_get_price_aapl_returns_float(self):
        price = self.service.get_price("AAPL")
        assert isinstance(price, float)

    def test_get_price_tsla_returns_float(self):
        price = self.service.get_price("TSLA")
        assert isinstance(price, float)

    def test_get_price_googl_returns_float(self):
        price = self.service.get_price("GOOGL")
        assert isinstance(price, float)

    def test_get_price_unknown_symbol_raises_value_error(self):
        with pytest.raises(ValueError):
            self.service.get_price("UNKNOWN")

    def test_get_price_unknown_symbol_error_message(self):
        with pytest.raises(ValueError) as exc_info:
            self.service.get_price("XYZ")
        assert "Unknown symbol: XYZ" in str(exc_info.value)

    def test_get_price_empty_string_raises_value_error(self):
        with pytest.raises(ValueError):
            self.service.get_price("")

    def test_get_price_lowercase_aapl_raises_value_error(self):
        with pytest.raises(ValueError):
            self.service.get_price("aapl")

    def test_get_price_msft_raises_value_error(self):
        with pytest.raises(ValueError) as exc_info:
            self.service.get_price("MSFT")
        assert "MSFT" in str(exc_info.value)

    def test_get_price_amzn_raises_value_error(self):
        with pytest.raises(ValueError):
            self.service.get_price("AMZN")


class TestSharePriceServiceGetPriceWithCustomFunction:
    """Tests for SharePriceService.get_price using a custom/mocked price function."""

    def test_get_price_calls_custom_function_with_symbol(self):
        mock_fn = MagicMock(return_value=250.00)
        service = SharePriceService(price_function=mock_fn)
        service.get_price("AAPL")
        mock_fn.assert_called_once_with("AAPL")

    def test_get_price_returns_value_from_custom_function(self):
        mock_fn = MagicMock(return_value=333.33)
        service = SharePriceService(price_function=mock_fn)
        price = service.get_price("AAPL")
        assert price == 333.33

    def test_get_price_passes_symbol_correctly_to_custom_function(self):
        mock_fn = MagicMock(return_value=100.0)
        service = SharePriceService(price_function=mock_fn)
        service.get_price("TSLA")
        mock_fn.assert_called_once_with("TSLA")

    def test_get_price_propagates_exception_from_custom_function(self):
        mock_fn = MagicMock(side_effect=ValueError("Custom error"))
        service = SharePriceService(price_function=mock_fn)
        with pytest.raises(ValueError) as exc_info:
            service.get_price("AAPL")
        assert "Custom error" in str(exc_info.value)

    def test_get_price_propagates_runtime_error_from_custom_function(self):
        mock_fn = MagicMock(side_effect=RuntimeError("Network error"))
        service = SharePriceService(price_function=mock_fn)
        with pytest.raises(RuntimeError):
            service.get_price("AAPL")

    def test_get_price_with_custom_function_returning_integer(self):
        mock_fn = MagicMock(return_value=500)
        service = SharePriceService(price_function=mock_fn)
        price = service.get_price("AAPL")
        assert price == 500

    def test_get_price_with_custom_function_called_multiple_times(self):
        mock_fn = MagicMock(side_effect=[100.0, 200.0, 300.0])
        service = SharePriceService(price_function=mock_fn)
        assert service.get_price("AAPL") == 100.0
        assert service.get_price("TSLA") == 200.0
        assert service.get_price("GOOGL") == 300.0
        assert mock_fn.call_count == 3

    def test_get_price_with_custom_function_for_custom_symbol(self):
        custom_prices = {"MSFT": 300.00, "AMZN": 3500.00}

        def custom_fn(symbol):
            if symbol not in custom_prices:
                raise ValueError(f"Unknown symbol: {symbol}")
            return custom_prices[symbol]

        service = SharePriceService(price_function=custom_fn)
        assert service.get_price("MSFT") == 300.00
        assert service.get_price("AMZN") == 3500.00

    def test_get_price_with_lambda_price_function(self):
        service = SharePriceService(price_function=lambda s: 42.0)
        price = service.get_price("ANY")
        assert price == 42.0

    def test_get_price_delegates_to_internal_price_function(self):
        mock_fn = MagicMock(return_value=99.99)
        service = SharePriceService(price_function=mock_fn)
        result = service.get_price("GOOGL")
        assert result == mock_fn.return_value

    def test_get_price_does_not_modify_returned_value(self):
        expected_price = 12345.6789
        mock_fn = MagicMock(return_value=expected_price)
        service = SharePriceService(price_function=mock_fn)
        result = service.get_price("AAPL")
        assert result == expected_price

    def test_get_price_with_zero_price(self):
        mock_fn = MagicMock(return_value=0.0)
        service = SharePriceService(price_function=mock_fn)
        price = service.get_price("AAPL")
        assert price == 0.0

    def test_get_price_with_very_large_price(self):
        large_price = 999999999.99
        mock_fn = MagicMock(return_value=large_price)
        service = SharePriceService(price_function=mock_fn)
        price = service.get_price("AAPL")
        assert price == large_price


class TestSharePriceServiceIntegration:
    """Integration-style tests for SharePriceService."""

    def test_default_service_acts_as_single_source_of_truth_for_aapl(self):
        service = SharePriceService()
        assert service.get_price("AAPL") == 150.00

    def test_default_service_acts_as_single_source_of_truth_for_tsla(self):
        service = SharePriceService()
        assert service.get_price("TSLA") == 700.00

    def test_default_service_acts_as_single_source_of_truth_for_googl(self):
        service = SharePriceService()
        assert service.get_price("GOOGL") == 2800.00

    def test_two_services_with_default_return_same_price(self):
        service1 = SharePriceService()
        service2 = SharePriceService()
        assert service1.get_price("AAPL") == service2.get_price("AAPL")

    def test_service_with_custom_function_overrides_default_prices(self):
        custom_fn = lambda s: 999.0
        service = SharePriceService(price_function=custom_fn)
        assert service.get_price("AAPL") == 999.0

    def test_multiple_calls_to_get_price_return_consistent_values(self):
        service = SharePriceService()
        price1 = service.get_price("AAPL")
        price2 = service.get_price("AAPL")
        assert price1 == price2

    def test_service_correctly_wraps_get_share_price_function(self):
        with patch("share_price_service.get_share_price") as mock_get_share_price:
            mock_get_share_price.return_value = 123.45
            service = SharePriceService()
            price = service.get_price("AAPL")
            mock_get_share_price.assert_called_once_with("AAPL")
            assert price == 123.45

    def test_service_raises_value_error_for_unknown_symbol_via_default(self):
        service = SharePriceService()
        with pytest.raises(ValueError):
            service.get_price("NOTASTOCK")

    def test_service_all_three_known_symbols(self):
        service = SharePriceService()
        expected = {"AAPL": 150.00, "TSLA": 700.00, "GOOGL": 2800.00}
        for symbol, expected_price in expected.items():
            assert service.get_price(symbol) == expected_price