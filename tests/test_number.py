"""Test cases for the decimal filter."""
# pylint: disable=missing-class-docstring,missing-function-docstring
import unittest

from babel import UnknownLocaleError

from liquid import Environment

from liquid_babel.filters import Number
from liquid_babel.filters import number


# TODO: test string parsing


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
