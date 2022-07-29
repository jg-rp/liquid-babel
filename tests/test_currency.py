"""Test cases for the currency filter."""
# pylint: disable=missing-class-docstring,missing-function-docstring
import unittest

from typing import Dict
from typing import NamedTuple

from babel import UnknownLocaleError

from liquid import Environment

from liquid_babel.filters import Currency
from liquid_babel.filters import currency


class Case(NamedTuple):
    description: str
    template: str
    expect: str
    globals: Dict[str, object]


class CurrencyFilterTestCase(unittest.TestCase):
    def test_default_currency_code_and_locale(self) -> None:
        """Test that the default currency code is USD and locale is en_US."""
        env = Environment()
        env.add_filter("currency", currency)
        template = env.from_string("{{ 1.99 | currency }}")
        result = template.render()
        self.assertEqual(result, "$1.99")

    def test_set_currency_code_default(self) -> None:
        """Test that we can set the default currency code."""
        env = Environment()
        env.add_filter("currency", Currency(default_currency_code="GBP"))
        template = env.from_string("{{ 1.99 | currency }}")
        result = template.render()
        self.assertEqual(result, "£1.99")

    def test_currency_code_from_context(self) -> None:
        """Test that we can get a currency code from context."""
        env = Environment()
        env.add_filter("currency", currency)
        template = env.from_string("{{ 1.99 | currency }}")
        result = template.render(currency_code="GBP")
        self.assertEqual(result, "£1.99")

    def test_unknown_currency_code(self) -> None:
        """Test that an unknown currency code is treated is prepended."""
        env = Environment()
        env.add_filter("currency", currency)
        template = env.from_string("{{ 1.99 | currency }}")
        result = template.render(currency_code="nosuchthing")
        self.assertEqual(result, "nosuchthing1.99")

    def test_set_locale_default(self) -> None:
        """Test that we can set the default locale."""
        env = Environment()
        env.add_filter("currency", Currency(default_locale="de"))
        template = env.from_string("{{ 1.99 | currency }}")
        result = template.render()
        self.assertEqual(result, "1,99\xa0$")

    def test_locale_from_context(self) -> None:
        """Test that we can get a locale from context."""
        env = Environment()
        env.add_filter("currency", currency)
        template = env.from_string("{{ 1.99 | currency }}")
        result = template.render(locale="de")
        self.assertEqual(result, "1,99\xa0$")

    def test_unknown_locale(self) -> None:
        """Test that an unknown locale raises an exception early."""
        env = Environment()
        with self.assertRaises(UnknownLocaleError):
            env.add_filter("currency", Currency(default_locale="nosuchthing"))

    def test_unknown_locale_from_context(self) -> None:
        """Test that an unknown locale falls back to default."""
        env = Environment()
        env.add_filter("currency", currency)
        template = env.from_string("{{ 1.99 | currency }}")
        result = template.render(locale="nosuchthing")
        self.assertEqual(result, "$1.99")

    def test_set_format_default(self) -> None:
        """Test that we can set the default currency format."""
        env = Environment()
        env.add_filter("currency", Currency(default_format="¤¤ #,##0.00"))
        template = env.from_string("{{ 1.99 | currency }}")
        result = template.render()
        self.assertEqual(result, "USD 1.99")

    def test_format_from_context(self) -> None:
        """Test that we can get a currency format from context."""
        env = Environment()
        env.add_filter("currency", currency)
        template = env.from_string("{{ 1.99 | currency }}")
        result = template.render(currency_format="¤¤ #,##0.00")
        self.assertEqual(result, "USD 1.99")

    def test_garbage_format(self) -> None:
        """Test that we don't fall over when given a garbage currency format."""
        env = Environment()
        env.add_filter("currency", currency)
        template = env.from_string("{{ 1.99 | currency }}")
        result = template.render(currency_format="bad format")
        self.assertEqual(result, "bad format1.99")

    def test_valid_string_left_value(self) -> None:
        """Test that we parse strings as decimals."""
        env = Environment()
        env.add_filter("currency", currency)
        template = env.from_string("{{ '1.99' | currency }}")
        result = template.render()
        self.assertEqual(result, "$1.99")

    def test_invalid_string_left_value(self) -> None:
        """Test that invalid decimals default to zero"""
        env = Environment()
        env.add_filter("currency", currency)
        template = env.from_string("{{ 'not a number' | currency }}")
        result = template.render()
        self.assertEqual(result, "$0.00")

    def test_arbitrary_object_left_value(self) -> None:
        """Test that arbitrary objects default to zero."""
        env = Environment()
        env.add_filter("currency", currency)
        template = env.from_string("{{ obj | currency }}")
        result = template.render(obj=object())
        self.assertEqual(result, "$0.00")

    def test_group_separator_default(self) -> None:
        """Test that the group separator argument defaults to True."""
        env = Environment()
        env.add_filter("currency", currency)
        template = env.from_string("{{ 811375 | currency }}")
        result = template.render()
        self.assertEqual(result, "$811,375.00")

    def test_group_separator_argument(self) -> None:
        """Test that we can control group separators with a filter keyword argument."""
        env = Environment()
        env.add_filter("currency", currency)
        template = env.from_string("{{ 811375 | currency: group_separator: false }}")
        result = template.render()
        self.assertEqual(result, "$811375.00")
