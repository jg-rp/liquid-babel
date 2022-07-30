"""Test cases for the decimal filter."""
# pylint: disable=missing-class-docstring,missing-function-docstring
import unittest

from babel import UnknownLocaleError

from liquid import Environment

from liquid_babel.filters import Number
from liquid_babel.filters import number


class NumberFilterTestCase(unittest.TestCase):
    def test_defaults(self) -> None:
        """Test that the default locale and format use en_US."""
        env = Environment()
        env.add_filter("decimal", number)
        template = env.from_string("{{ '374881.01' | decimal }}")
        result = template.render()
        self.assertEqual(result, "374,881.01")

    def test_set_default_locale(self) -> None:
        """Test that we can set the default locale."""
        env = Environment()
        env.add_filter("decimal", Number(default_locale="de"))
        template = env.from_string("{{ '374881.01' | decimal }}")
        result = template.render()
        self.assertEqual(result, "374.881,01")

    def test_get_default_locale_from_context(self) -> None:
        """Test that we can get a default locale from context."""
        env = Environment()
        env.add_filter("decimal", number)
        template = env.from_string("{{ '374881.01' | decimal }}")
        result = template.render(locale="de")
        self.assertEqual(result, "374.881,01")

    def test_default_decimal_quantization(self) -> None:
        """Test that decimal quantization defaults to False."""
        env = Environment()
        env.add_filter("decimal", number)
        template = env.from_string("{{ '2.2346' | decimal }}")
        result = template.render()
        self.assertEqual(result, "2.2346")

    def test_set_default_decimal_quantization(self) -> None:
        """Test that we can set the default decimal quantization."""
        env = Environment()
        env.add_filter("decimal", Number(default_decimal_quantization=True))
        template = env.from_string("{{ '2.2346' | decimal }}")
        result = template.render()
        self.assertEqual(result, "2.235")

    def test_get_decimal_quantization_from_context(self) -> None:
        """Test that we can get decimal quantization from context."""
        env = Environment()
        env.add_filter("decimal", number)
        template = env.from_string("{{ '2.2346' | decimal }}")
        result = template.render(decimal_quantization=True)
        self.assertEqual(result, "2.235")

    def test_parse_string(self) -> None:
        """Test parse a string to a decimal with the default input locale."""
        env = Environment()
        env.add_filter("decimal", number)
        # Parse as en_US
        template = env.from_string("{{ '10,000.00' | decimal }}")
        result = template.render(locale="de")
        # Render as de
        self.assertEqual(result, "10.000")

    def test_parse_string_with_input_locale_from_context(self) -> None:
        """Test parse a string to a decimal with an input locale from context."""
        env = Environment()
        env.add_filter("decimal", number)
        # Parse as de
        template = env.from_string("{{ '10.000,00' | decimal }}")
        result = template.render(locale="en_US", input_locale="de")
        # Render as en_US
        self.assertEqual(result, "10,000")

    def test_set_default_input_locale(self) -> None:
        """Test that we can set the default input locale."""
        env = Environment()
        # Parse as de
        env.add_filter("decimal", Number(default_input_locale="de"))
        template = env.from_string("{{ '10.000,00' | decimal }}")
        result = template.render(locale="en_US")
        # Render as en_US
        self.assertEqual(result, "10,000")

    def test_unknown_locale(self) -> None:
        """Test that an unknown locale raises an exception early."""
        env = Environment()
        with self.assertRaises(UnknownLocaleError):
            env.add_filter("decimal", Number(default_locale="nosuchthing"))

    def test_unknown_locale_from_context(self) -> None:
        """Test that an unknown locale falls back to default."""
        env = Environment()
        env.add_filter("decimal", number)
        template = env.from_string("{{ '1.99' | decimal }}")
        result = template.render(locale="nosuchthing")
        self.assertEqual(result, "1.99")

    def test_invalid_string_left_value(self) -> None:
        """Test that invalid decimals default to zero"""
        env = Environment()
        env.add_filter("decimal", number)
        template = env.from_string("{{ 'not a number' | decimal }}")
        result = template.render()
        self.assertEqual(result, "0")

    def test_arbitrary_object_left_value(self) -> None:
        """Test that arbitrary objects default to zero."""
        env = Environment()
        env.add_filter("decimal", number)
        template = env.from_string("{{ obj | decimal }}")
        result = template.render(obj=object())
        self.assertEqual(result, "0")

    def test_float_left_value(self) -> None:
        """Test that float left values are parsed."""
        env = Environment()
        env.add_filter("decimal", number)
        template = env.from_string("{{ 1.5 | decimal }}")
        result = template.render()
        self.assertEqual(result, "1.5")
