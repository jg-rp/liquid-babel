"""Test cases for the unit filter."""
# pylint: disable=missing-class-docstring,missing-function-docstring
import unittest

from babel import UnknownLocaleError

from liquid import Environment
from liquid.exceptions import FilterArgumentError

from liquid_babel.filters import Unit
from liquid_babel.filters import unit


class UnitFilterTestCase(unittest.TestCase):
    def test_defaults(self) -> None:
        """Test the default locale and length."""
        env = Environment()
        env.add_filter("unit", unit)
        template = env.from_string("{{ 12 | unit: 'length-meter' }}")
        result = template.render()
        self.assertEqual(result, "12 meters")

    def test_set_default_local(self) -> None:
        """Test that we can set the default locale."""
        env = Environment()
        env.add_filter("unit", Unit(default_locale="de"))
        template = env.from_string("{{ 12 | unit: 'length-meter' }}")
        result = template.render()
        self.assertEqual(result, "12 Meter")

    def test_get_the_default_local_from_context(self) -> None:
        """Test that we can get the default locale from context."""
        env = Environment()
        env.add_filter("unit", unit)
        template = env.from_string("{{ 12 | unit: 'length-meter' }}")
        result = template.render(locale="de")
        self.assertEqual(result, "12 Meter")

    def test_set_the_default_length(self) -> None:
        """Test that we can set the default unit length."""
        env = Environment()
        env.add_filter("unit", Unit(default_length="short"))
        template = env.from_string("{{ 12 | unit: 'length-meter' }}")
        result = template.render()
        self.assertEqual(result, "12 m")

    def test_length_argument(self) -> None:
        """Test that the length argument takes priority over the default."""
        env = Environment()
        env.add_filter("unit", Unit(default_length="short"))
        template = env.from_string("{{ 12 | unit: 'length-meter', length: 'narrow' }}")
        result = template.render()
        self.assertEqual(result, "12m")

    def test_get_length_from_context(self) -> None:
        """Test that we can get the length from context."""
        env = Environment()
        env.add_filter("unit", unit)
        template = env.from_string("{{ 12 | unit: 'length-meter' }}")
        result = template.render(unit_length="narrow")
        self.assertEqual(result, "12m")

    def test_parse_string(self) -> None:
        """Test that we can parse strings using the input locale."""
        env = Environment()
        env.add_filter("unit", unit)
        template = env.from_string("{{ '1.200' | unit: 'length-meter' }}")
        result = template.render(input_locale="de")
        self.assertEqual(result, "1,200 meters")

    def test_set_decimal_format(self) -> None:
        """Test that we can set the default decimal format."""
        env = Environment()
        env.add_filter("unit", Unit(default_format="#,##0.00"))
        template = env.from_string("{{ '1200' | unit: 'length-meter' }}")
        result = template.render()
        self.assertEqual(result, "1,200.00 meters")

    def test_format_argument(self) -> None:
        """Test that the format argument takes priority over the default."""
        env = Environment()
        env.add_filter("unit", unit)
        template = env.from_string(
            "{{ '1200' | unit: 'length-meter', format: '#,##0.00' }}"
        )
        result = template.render()
        self.assertEqual(result, "1,200.00 meters")

    def test_get_format_from_context(self) -> None:
        """Test that the we can get the decimal format from context."""
        env = Environment()
        env.add_filter("unit", unit)
        template = env.from_string("{{ '1200' | unit: 'length-meter' }}")
        result = template.render(unit_format="#,##0.00")
        self.assertEqual(result, "1,200.00 meters")

    def test_unknown_locale(self) -> None:
        """Test that an unknown locale raises an exception early."""
        env = Environment()
        with self.assertRaises(UnknownLocaleError):
            env.add_filter("unit", Unit(default_locale="nosuchthing"))

    def test_unknown_locale_from_context(self) -> None:
        """Test that an unknown locale falls back to default."""
        env = Environment()
        env.add_filter("unit", unit)
        template = env.from_string("{{ '1.99' | unit: 'length-meter' }}")
        result = template.render(locale="nosuchthing")
        self.assertEqual(result, "1.99 meters")

    def test_invalid_string_left_value(self) -> None:
        """Test that invalid decimals default to zero"""
        env = Environment()
        env.add_filter("unit", unit)
        template = env.from_string("{{ 'not a number' | unit: 'length-meter' }}")
        result = template.render()
        self.assertEqual(result, "0 meters")

    def test_compound_unit(self) -> None:
        """Test that we can format compound units."""
        env = Environment()
        env.add_filter("unit", unit)
        template = env.from_string(
            "{{ 150 | unit: 'kilowatt', denominator_unit: 'year'  }}"
        )
        result = template.render(locale="fi")
        self.assertEqual(result, "150 kilowattia / vuosi")

    def test_compound_unit_with_denominator(self) -> None:
        """Test that we can format compound units with a denominator value."""
        env = Environment()
        env.add_filter("unit", unit)
        template = env.from_string(
            "{{ 32.5 | unit: 'ton', denominator: 15, denominator_unit: 'hour' }}"
        )
        result = template.render(locale="en")
        self.assertEqual(result, "32.5 tons per 15 hours")

    def test_unknown_unit(self) -> None:
        """Test that we handle unknown units."""
        env = Environment()
        env.add_filter("unit", unit)
        template = env.from_string("{{ 5 | unit: 'apples' }}")

        with self.assertRaises(FilterArgumentError):
            template.render()
