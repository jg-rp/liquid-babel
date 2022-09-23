"""Test message translation edge cases."""
# pylint: disable=missing-class-docstring,missing-function-docstring,too-many-public-methods
import unittest

from liquid import Environment
from liquid import StrictUndefined

from liquid.exceptions import UndefinedError

from liquid_babel.filters.translate import register_translation_filters
from liquid_babel.tags.translate import TranslateTag


class MessagesEdgeTestCase(unittest.TestCase):
    def setUp(self) -> None:
        super().setUp()
        self.env = Environment()
        register_translation_filters(self.env)
        self.env.add_tag(TranslateTag)

    def test_missing_translation_variable(self) -> None:
        """Test that missing translation variables are `Undefined`."""
        source = "{{ 'Hello, %(you)s!' | gettext }}"
        template = self.env.from_string(source)
        self.assertEqual(template.render(), "Hello, !")

        self.env.undefined = StrictUndefined
        with self.assertRaises(UndefinedError):
            template.render()

    def test_bool_translation_variable(self) -> None:
        """Test that we handle boolean translation variables."""
        source = "{{ 'Hello, %(you)s!' | gettext }}"
        template = self.env.from_string(source)
        self.assertEqual(template.render(you=True), "Hello, true!")

    def test_none_translation_variable(self) -> None:
        """Test that we handle None translation variables."""
        source = "{{ 'Hello, %(you)s!' | gettext }}"
        template = self.env.from_string(source)
        self.assertEqual(template.render(you=None), "Hello, !")

    def test_list_translation_variable(self) -> None:
        """Test that we handle list translation variables."""
        source = "{{ 'Hello, %(you)s!' | gettext }}"
        template = self.env.from_string(source)
        self.assertEqual(template.render(you=[1, 2, 3]), "Hello, 123!")

        self.env.autoescape = True
        self.assertEqual(template.render(you=[1, 2, 3]), "Hello, 123!")

    def test_range_translation_variable(self) -> None:
        """Test that we handle range translation variables."""
        source = "{% assign you = (1..3) %}{{ 'Hello, %(you)s!' | gettext }}"
        template = self.env.from_string(source)
        self.assertEqual(template.render(), "Hello, 1..3!")

        self.env.autoescape = True
        self.assertEqual(template.render(), "Hello, 1..3!")

    def test_message_not_a_string(self) -> None:
        """Test that we handle messages that are not strings."""
        source = "{{ true | gettext }}"
        template = self.env.from_string(source)
        self.assertEqual(template.render(), "true")

    def test_count_not_int(self) -> None:
        """Test that the t filter handles counts that are not ints."""
        source = "{{ 'Hello, World!' | t: plural: 'Hello, Worlds!', count:'foo' }}"
        template = self.env.from_string(source)
        self.assertEqual(template.render(), "Hello, World!")
