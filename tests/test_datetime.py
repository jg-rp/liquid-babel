"""Test cases for the datetime filter."""
# pylint: disable=missing-class-docstring,missing-function-docstring
import datetime
import unittest

import pytz

from babel import UnknownLocaleError

from liquid import Environment
from liquid.exceptions import FilterArgumentError

from liquid_babel.filters import DateTime


# pylint: disable=too-many-public-methods
class DateTimeFilterTestCase(unittest.TestCase):
    def test_default_options(self) -> None:
        """Test the default timezone, format and locale."""
        env = Environment()
        env.add_filter("datetime", DateTime())
        template = env.from_string("{{ dt | datetime }}")
        result = template.render(dt=datetime.datetime(2007, 4, 1, 15, 30))
        self.assertEqual(result, "Apr 1, 2007, 3:30:00 PM")

    def test_short_format(self) -> None:
        """Test the built-in short format."""
        env = Environment()
        env.add_filter("datetime", DateTime())

        template = env.from_string("{{ dt | datetime: format: 'short' }}")
        result = template.render(dt=datetime.datetime(2007, 4, 1, 15, 30))
        self.assertEqual(result, "4/1/07, 3:30 PM")

    def test_medium_format(self) -> None:
        """Test the built-in medium format."""
        env = Environment()
        env.add_filter("datetime", DateTime())

        template = env.from_string("{{ dt | datetime: format: 'medium' }}")
        result = template.render(dt=datetime.datetime(2007, 4, 1, 15, 30))
        self.assertEqual(result, "Apr 1, 2007, 3:30:00 PM")

    def test_long_format(self) -> None:
        """Test the built-in long format."""
        env = Environment()
        env.add_filter("datetime", DateTime())

        template = env.from_string("{{ dt | datetime: format: 'long' }}")
        result = template.render(dt=datetime.datetime(2007, 4, 1, 15, 30))
        self.assertEqual(result, "April 1, 2007 at 3:30:00 PM UTC")

    def test_full_format(self) -> None:
        """Test the built-in full format."""
        env = Environment()
        env.add_filter("datetime", DateTime())

        template = env.from_string("{{ dt | datetime: format: 'full' }}")
        result = template.render(dt=datetime.datetime(2007, 4, 1, 15, 30))
        self.assertEqual(
            result, "Sunday, April 1, 2007 at 3:30:00 PM Coordinated Universal Time"
        )

    def test_custom_format(self) -> None:
        """Test we can override the default format with a custom format string."""
        env = Environment()
        env.add_filter("datetime", DateTime())

        template = env.from_string("{{ dt | datetime: format: 'EEEE, d.M.yyyy' }}")
        result = template.render(dt=datetime.datetime(2007, 4, 1, 15, 30))
        self.assertEqual(result, "Sunday, 1.4.2007")

    def test_set_default_format(self) -> None:
        """Test we can set a default format string."""
        env = Environment()
        env.add_filter("datetime", DateTime(default_format="EEEE, d.M.yyyy"))

        template = env.from_string("{{ dt | datetime }}")
        result = template.render(dt=datetime.datetime(2007, 4, 1, 15, 30))
        self.assertEqual(result, "Sunday, 1.4.2007")

    def test_get_format_from_context(self) -> None:
        """Test we can get a format string from the render context."""
        env = Environment()
        env.add_filter("datetime", DateTime())

        template = env.from_string("{{ dt | datetime }}")
        result = template.render(
            dt=datetime.datetime(2007, 4, 1, 15, 30),
            datetime_format="EEEE, d.M.yyyy",
        )
        self.assertEqual(result, "Sunday, 1.4.2007")

    def test_set_default_timezone(self) -> None:
        """Test we can set a default timezone."""
        env = Environment()
        # Choose a static timezone so tests wont fail as we go in and out of daylight
        # saving. Etc/GMT reverses the meaning of '+' and '-' compared to UTC or GMT.
        env.add_filter("datetime", DateTime(default_timezone="Etc/GMT-1"))

        template = env.from_string("{{ dt | datetime }}")
        result = template.render(dt=datetime.datetime(2007, 4, 1, 15, 30))
        self.assertEqual(result, "Apr 1, 2007, 4:30:00 PM")

    def test_get_timezone_from_context(self) -> None:
        """Test we can get a timezone from the render context."""
        env = Environment()
        env.add_filter("datetime", DateTime())

        template = env.from_string("{{ dt | datetime }}")
        result = template.render(
            dt=datetime.datetime(2007, 4, 1, 15, 30),
            timezone="Etc/GMT-1",
        )
        self.assertEqual(result, "Apr 1, 2007, 4:30:00 PM")

    def test_unknown_timezone_falls_back_to_default(self) -> None:
        """Test we handle unknown timezones."""
        env = Environment()
        env.add_filter("datetime", DateTime())

        template = env.from_string("{{ dt | datetime }}")
        result = template.render(
            dt=datetime.datetime(2007, 4, 1, 15, 30),
            timezone="foo",
        )
        self.assertEqual(result, "Apr 1, 2007, 3:30:00 PM")

    def test_unknown_default_timezone(self) -> None:
        """Test that an unknown default timezone fails early."""
        env = Environment()

        with self.assertRaises(pytz.UnknownTimeZoneError) as raised:
            env.add_filter("datetime", DateTime(default_timezone="foo"))
        self.assertEqual(str(raised.exception), "'foo'")

    def test_set_default_locale(self) -> None:
        """Test we can set a default locale."""
        env = Environment()
        env.add_filter("datetime", DateTime(default_locale="en_GB"))

        template = env.from_string("{{ dt | datetime }}")
        result = template.render(dt=datetime.datetime(2007, 4, 1, 15, 30))
        self.assertEqual(result, "1 Apr 2007, 15:30:00")

    def test_get_locale_from_context(self) -> None:
        """Test we can get a locale from the render context."""
        env = Environment()
        env.add_filter("datetime", DateTime())

        template = env.from_string("{{ dt | datetime }}")
        result = template.render(
            dt=datetime.datetime(2007, 4, 1, 15, 30),
            locale="en_GB",
        )
        self.assertEqual(result, "1 Apr 2007, 15:30:00")

    def test_unknown_locale(self) -> None:
        """Test that an unknown locale raises an exception early."""
        env = Environment()
        with self.assertRaises(UnknownLocaleError):
            env.add_filter("datetime", DateTime(default_locale="nosuchthing"))

    def test_unknown_locale_from_context(self) -> None:
        """Test that an unknown locale falls back to default."""
        env = Environment()
        env.add_filter("datetime", DateTime())
        template = env.from_string("{{ dt | datetime }}")
        result = template.render(
            locale="nosuchthing",
            dt=datetime.datetime(2007, 4, 1, 15, 30),
        )
        self.assertEqual(result, "Apr 1, 2007, 3:30:00 PM")

    def test_parse_string(self) -> None:
        """Test that we parse strings to datetime objects."""
        env = Environment()
        env.add_filter("datetime", DateTime())
        template = env.from_string(
            "{{ 'Apr 1, 2007, 3:30:00 PM' | datetime: format: 'short' }}"
        )
        result = template.render()
        self.assertEqual(result, "4/1/07, 3:30 PM")

    def test_parse_string_with_tzinfo(self) -> None:
        """Test that we parse strings to datetime objects."""
        env = Environment()
        env.add_filter("datetime", DateTime())
        template = env.from_string(
            "{{ 'Apr 1, 2007, 3:30:00 PM GMT-1' | datetime: format: 'short' }}"
        )
        result = template.render()
        self.assertEqual(result, "4/1/07, 2:30 PM")

    def test_set_default_input_timezone(self) -> None:
        """Test that we can set the default input timezone."""
        env = Environment()
        env.add_filter("datetime", DateTime(default_input_timezone="Etc/GMT-1"))
        template = env.from_string(
            "{{ 'Apr 1, 2007, 3:30:00 PM' | datetime: format: 'short' }}"
        )
        result = template.render()
        self.assertEqual(result, "4/1/07, 2:30 PM")

    def test_garbage_left_value(self) -> None:
        """Test that we get an exception of the input string is garbage."""
        env = Environment()
        env.add_filter("datetime", DateTime())
        template = env.from_string("{{ 'foobar' | datetime: format: 'short' }}")
        with self.assertRaises(FilterArgumentError):
            template.render()

    def test_now(self) -> None:
        """Test that we use the current datetime with 'now'."""
        env = Environment()
        env.add_filter("datetime", DateTime(default_format="yyyy"))
        template = env.from_string("{{ 'now' | datetime: }}")
        result = template.render()
        self.assertEqual(result, str(datetime.datetime.today().year))

    def test_today(self) -> None:
        """Test that we use the current datetime with 'today'."""
        env = Environment()
        env.add_filter("datetime", DateTime(default_format="yyyy"))
        template = env.from_string("{{ 'today' | datetime: }}")
        result = template.render()
        self.assertEqual(result, str(datetime.datetime.today().year))

    def test_date_input(self) -> None:
        """Test that we handle date objects."""
        env = Environment()
        env.add_filter("datetime", DateTime())
        template = env.from_string("{{ dt | datetime: }}")
        result = template.render(dt=datetime.date(2007, 4, 1))
        self.assertEqual(result, "Apr 1, 2007, 12:00:00 AM")

    def test_integer_input(self) -> None:
        """Test that we handle unix timestamps."""
        env = Environment()
        env.add_filter("datetime", DateTime())
        template = env.from_string("{{ dt | datetime: }}")
        result = template.render(dt=1152098955)
        self.assertEqual(result, "Jul 5, 2006, 11:29:15 AM")

    def test_arbitrary_object_input(self) -> None:
        """Test that we handle unix timestamps."""
        env = Environment()
        env.add_filter("datetime", DateTime())
        template = env.from_string("{{ dt | datetime: }}")
        with self.assertRaises(FilterArgumentError):
            template.render(dt=object())

    def test_filter_argument_priority(self) -> None:
        """Test that the filter argument takes priority over render context."""
        env = Environment()
        env.add_filter("datetime", DateTime())
        template = env.from_string(
            "{{ 'Apr 1, 2007, 3:30:00 PM' | datetime: format: 'short' }}"
        )
        result = template.render(datetime_format="full")
        self.assertEqual(result, "4/1/07, 3:30 PM")
