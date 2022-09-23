"""Test cases for rendering translatable messages."""
# pylint: disable=missing-class-docstring,missing-function-docstring,too-many-public-methods
import re
import unittest

from typing import List

from liquid import Environment

from liquid_babel.filters.translate import PGETTEXT_AVAILABLE
from liquid_babel.filters.translate import register_translation_filters

from liquid_babel.tags.translate import TranslateTag


class MockTranslations:
    """A mock translations class that returns all messages in upper case."""

    RE_VARS = re.compile(r"%\(\w+\)s")

    def gettext(self, message: str) -> str:
        return self._upper(message)

    def ngettext(self, singular: str, plural: str, n: int) -> str:
        if n > 1:
            return self._upper(plural)
        return self._upper(singular)

    def pgettext(self, message_context: str, message: str) -> str:
        return message_context + "::" + self._upper(message)

    def npgettext(
        self, message_context: str, singular: str, plural: str, n: int
    ) -> str:
        if n > 1:
            return message_context + "::" + self._upper(plural)
        return message_context + "::" + self._upper(singular)

    def _upper(self, message: str) -> str:
        start = 0
        parts: List[str] = []
        for match in self.RE_VARS.finditer(message):
            parts.append(message[start : match.start()].upper())
            parts.append(match.group())
            start = match.end()

        parts.append(message[start:].upper())
        return "".join(parts)


MOCK_TRANSLATIONS = MockTranslations()


class TranslateMessagesTestCase(unittest.TestCase):
    def setUp(self) -> None:
        super().setUp()
        self.env = Environment()
        register_translation_filters(self.env)
        self.env.add_tag(TranslateTag)

    def test_gettext_filter(self) -> None:
        """Test that we can translate messages with the gettext filter."""
        source = "{{ 'Hello, World!' | gettext }}"
        template = self.env.from_string(source)

        # Default, null translation
        result = template.render()
        self.assertEqual(result, "Hello, World!")

        # Mock translation
        result = template.render(translations=MOCK_TRANSLATIONS)
        self.assertEqual(result, "HELLO, WORLD!")

    def test_gettext_from_context(self) -> None:
        """Test that we can translate messages from context with the gettext filter."""
        source = "{{ foo | gettext }}"
        template = self.env.from_string(source)

        # Default, null translation
        result = template.render(foo="Hello, World!")
        self.assertEqual(result, "Hello, World!")

        # Mock translation
        result = template.render(
            translations=MOCK_TRANSLATIONS,
            foo="Hello, World!",
        )
        self.assertEqual(result, "HELLO, WORLD!")

    def test_gettext_filter_with_variables(self) -> None:
        """Test that we can translate messages with the gettext filter."""
        source = "{{ 'Hello, %(you)s!' | gettext: you: 'World' }}"
        template = self.env.from_string(source)

        # Default, null translation
        result = template.render()
        self.assertEqual(result, "Hello, World!")

        # Mock translation
        result = template.render(translations=MOCK_TRANSLATIONS)
        self.assertEqual(result, "HELLO, World!")

    def test_ngettext_filter(self) -> None:
        """Test that we can translate messages with the ngettext filter."""
        source = "{{ 'Hello, World!' | ngettext: 'Hello, Worlds!', 2 }}"
        template = self.env.from_string(source)

        # Default, null translation
        result = template.render()
        self.assertEqual(result, "Hello, Worlds!")

        # Mock translation
        result = template.render(translations=MOCK_TRANSLATIONS)
        self.assertEqual(result, "HELLO, WORLDS!")

    @unittest.skipUnless(PGETTEXT_AVAILABLE, "pgettext was new in python 3.8")
    def test_pgettext_filter(self) -> None:
        """Test that we can translate messages with the pgettext filter."""
        source = "{{ 'Hello, World!' | pgettext: 'greeting' }}"
        template = self.env.from_string(source)

        # Default, null translation
        result = template.render()
        self.assertEqual(result, "Hello, World!")

        # Mock translation
        result = template.render(translations=MOCK_TRANSLATIONS)
        self.assertEqual(result, "greeting::HELLO, WORLD!")

    @unittest.skipUnless(PGETTEXT_AVAILABLE, "pgettext was new in python 3.8")
    def test_npgettext_filter(self) -> None:
        """Test that we can translate messages with the npgettext filter."""
        source = "{{ 'Hello, World!' | npgettext: 'greeting', 'Hello, Worlds!', 2 }}"
        template = self.env.from_string(source)

        # Default, null translation
        result = template.render()
        self.assertEqual(result, "Hello, Worlds!")

        # Mock translation
        result = template.render(translations=MOCK_TRANSLATIONS)
        self.assertEqual(result, "greeting::HELLO, WORLDS!")

    def test_t_filter_gettext(self) -> None:
        """Test that we can do gettext with the t filter."""
        source = "{{ 'Hello, World!' | t }}"
        template = self.env.from_string(source)

        # Default, null translation
        result = template.render()
        self.assertEqual(result, "Hello, World!")

        # Mock translation
        result = template.render(translations=MOCK_TRANSLATIONS)
        self.assertEqual(result, "HELLO, WORLD!")

    def test_t_filter_ngettext(self) -> None:
        """Test that we can do ngettext with the t filter."""
        source = "{{ 'Hello, World!' | t: plural: 'Hello, Worlds!', count: 2 }}"
        template = self.env.from_string(source)

        # Default, null translation
        result = template.render()
        self.assertEqual(result, "Hello, Worlds!")

        # Mock translation
        result = template.render(translations=MOCK_TRANSLATIONS)
        self.assertEqual(result, "HELLO, WORLDS!")

    @unittest.skipUnless(PGETTEXT_AVAILABLE, "pgettext was new in python 3.8")
    def test_t_filter_pgettext(self) -> None:
        """Test that we can do pgettext with the t filter."""
        source = "{{ 'Hello, %(you)s!' | t: 'greeting', you: 'World' }}"
        template = self.env.from_string(source)

        # Default, null translation
        result = template.render()
        self.assertEqual(result, "Hello, World!")

        # Mock translation
        result = template.render(translations=MOCK_TRANSLATIONS)
        self.assertEqual(result, "greeting::HELLO, World!")

    @unittest.skipUnless(PGETTEXT_AVAILABLE, "pgettext was new in python 3.8")
    def test_t_filter_npgettext(self) -> None:
        """Test that we can do npgettext with the t filter."""
        source = """
            {{-
                'Hello, %(you)s!' | t:
                    'greeting',
                    plural: 'Hello, %(you)ss!',
                    count: 2,
                    you: 'World'
            -}}
        """
        template = self.env.from_string(source)

        # Default, null translation
        result = template.render()
        self.assertEqual(result, "Hello, Worlds!")

        # Mock translation
        result = template.render(translations=MOCK_TRANSLATIONS)
        self.assertEqual(result, "greeting::HELLO, WorldS!")


# TODO: test turn off filter message interpolation
# TODO: test plural is converted to a string
# TODO: test ngettext count can be a string
# TODO: test autoescape
