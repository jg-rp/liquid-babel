"""Test cases for rendering translatable messages."""
# pylint: disable=missing-class-docstring,missing-function-docstring,too-many-public-methods

import asyncio
import re
import unittest

from gettext import NullTranslations
from typing import List

from liquid import Environment
from liquid import Markup

from liquid_babel.filters import register_translation_filters
from liquid_babel.tags.translate import TranslateTag

PGETTEXT_AVAILABLE = hasattr(NullTranslations, "pgettext")


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
        return Markup("").join(parts)


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

    def test_translate_tag_gettext(self) -> None:
        """Test that we can do gettext with the translate tag."""
        source = """
            {%- translate you: 'World', there: false -%}
                Hello, {{ you }}!
            {%- endtranslate -%}
        """
        template = self.env.from_string(source)

        # Default, null translation
        result = template.render()
        self.assertEqual(result, "Hello, World!")

        # Mock translation
        result = template.render(translations=MOCK_TRANSLATIONS)
        self.assertEqual(result, "HELLO, World!")

        async def coro() -> str:
            return await template.render_async(translations=MOCK_TRANSLATIONS)

        result = asyncio.run(coro())
        self.assertEqual(result, "HELLO, World!")

    def test_translate_tag_ngettext(self) -> None:
        """Test that we can do ngettext with the translate tag."""
        source = """
            {%- translate, you: 'World', count: 2 -%}
                Hello, {{ you }}!
            {%- plural -%}
                Hello, {{ you }}s!
            {%- endtranslate -%}
        """
        template = self.env.from_string(source)

        # Default, null translation
        result = template.render()
        self.assertEqual(result, "Hello, Worlds!")

        # Mock translation
        result = template.render(translations=MOCK_TRANSLATIONS)
        self.assertEqual(result, "HELLO, WorldS!")

    def test_translate_tag_with_filtered_argument(self) -> None:
        """Test that we can use argument-less filters with the translate tag."""
        source = """
            {%- translate you: 'World', count: collection | size -%}
                Hello, {{ you }}!
            {%- plural -%}
                Hello, {{ you }}s!
            {%- endtranslate -%}
        """
        template = self.env.from_string(source)

        # Default, null translation
        result = template.render(collection=[1, 2])
        self.assertEqual(result, "Hello, Worlds!")

        # Mock translation
        result = template.render(collection=[1, 2], translations=MOCK_TRANSLATIONS)
        self.assertEqual(result, "HELLO, WorldS!")

    @unittest.skipUnless(PGETTEXT_AVAILABLE, "pgettext was new in python 3.8")
    def test_translate_tag_pgettext(self) -> None:
        """Test that we can do pgettext with the translate tag."""
        source = """
            {%- translate context: 'greeting', you: 'World' -%}
                Hello, {{ you }}!
            {%- endtranslate -%}
        """
        template = self.env.from_string(source)

        # Default, null translation
        result = template.render()
        self.assertEqual(result, "Hello, World!")

        # Mock translation
        result = template.render(translations=MOCK_TRANSLATIONS)
        self.assertEqual(result, "greeting::HELLO, World!")

    @unittest.skipUnless(PGETTEXT_AVAILABLE, "pgettext was new in python 3.8")
    def test_translate_tag_npgettext(self) -> None:
        """Test that we can do npgettext with the translate tag."""
        source = """
            {%- translate context: 'greeting', you: 'World', count: 2 -%}
                Hello, {{ you }}!
            {%- plural -%}
                Hello, {{ you }}s!
            {%- endtranslate -%}
        """
        template = self.env.from_string(source)

        # Default, null translation
        result = template.render()
        self.assertEqual(result, "Hello, Worlds!")

        # Mock translation
        result = template.render(translations=MOCK_TRANSLATIONS)
        self.assertEqual(result, "greeting::HELLO, WorldS!")


class AutoEscapeMessagesTestCase(unittest.TestCase):
    def setUp(self) -> None:
        super().setUp()
        self.env = Environment(autoescape=True)
        register_translation_filters(self.env, autoescape_message=True)
        self.env.add_tag(TranslateTag)

    def test_t_filter_auto_escape(self) -> None:
        """Test that the t filter can escape messages."""
        source = "{{ s | t }}"
        template = self.env.from_string(source)

        # Default, null translation
        result = template.render(s="<b>Hello, World!</b>")
        self.assertEqual(result, "&lt;b&gt;Hello, World!&lt;/b&gt;")

        # Mock translation
        result = template.render(
            s="<b>Hello, World!</b>", translations=MOCK_TRANSLATIONS
        )
        self.assertEqual(result, "&LT;B&GT;HELLO, WORLD!&LT;/B&GT;")

    def test_ngettext_filter_auto_escape(self) -> None:
        """Test that the ngettext filter can escape messages."""
        source = "{{ s | ngettext: 'Hello, Worlds!', 1 }}"
        template = self.env.from_string(source)

        # Default, null translation
        result = template.render(s="<b>Hello, World!</b>")
        self.assertEqual(result, "&lt;b&gt;Hello, World!&lt;/b&gt;")

        # Mock translation
        result = template.render(
            s="<b>Hello, World!</b>", translations=MOCK_TRANSLATIONS
        )
        self.assertEqual(result, "&LT;B&GT;HELLO, WORLD!&LT;/B&GT;")

    @unittest.skipUnless(PGETTEXT_AVAILABLE, "pgettext was new in python 3.8")
    def test_pgettext_filter_auto_escape(self) -> None:
        """Test that the pgettext filter can escape messages."""
        source = "{{ s | pgettext: 'greeting'}}"
        template = self.env.from_string(source)

        # Default, null translation
        result = template.render(s="<b>Hello, World!</b>")
        self.assertEqual(result, "&lt;b&gt;Hello, World!&lt;/b&gt;")

        # Mock translation
        result = template.render(
            s="<b>Hello, World!</b>", translations=MOCK_TRANSLATIONS
        )
        self.assertEqual(result, "greeting::&LT;B&GT;HELLO, WORLD!&LT;/B&GT;")

    @unittest.skipUnless(PGETTEXT_AVAILABLE, "pgettext was new in python 3.8")
    def test_npgettext_filter_auto_escape(self) -> None:
        """Test that the npgettext filter can escape messages."""
        source = "{{ s | npgettext: 'greeting', 'Hello, Worlds!', 1 }}"
        template = self.env.from_string(source)

        # Default, null translation
        result = template.render(s="<b>Hello, World!</b>")
        self.assertEqual(result, "&lt;b&gt;Hello, World!&lt;/b&gt;")

        # Mock translation
        result = template.render(
            s="<b>Hello, World!</b>", translations=MOCK_TRANSLATIONS
        )
        self.assertEqual(result, "greeting::&LT;B&GT;HELLO, WORLD!&LT;/B&GT;")

    def test_translate_tag_gettext(self) -> None:
        """Test that we can do gettext with the translate tag."""
        source = """
            {%- translate -%}
                Hello, {{ you }}!
            {%- endtranslate -%}
        """
        template = self.env.from_string(source)

        # Default, null translation
        result = template.render(you="<b>World</b>")
        self.assertEqual(result, "Hello, &lt;b&gt;World&lt;/b&gt;!")

        # Mock translation
        result = template.render(you="<b>World</b>", translations=MOCK_TRANSLATIONS)
        self.assertEqual(result, "HELLO, &lt;b&gt;World&lt;/b&gt;!")

    def test_translate_tag_message_trimming(self) -> None:
        """Test that we normalize whitespace in messages by default."""
        source = """
            {%- translate you: 'World', there: false, other: 'foo' -%}
                Hello, {{ you }}!
                {{ other }}
            {%- endtranslate -%}
        """
        template = self.env.from_string(source)

        # Default, null translation
        result = template.render()
        self.assertEqual(result, "Hello, World! foo")

        # Mock translation
        result = template.render(translations=MOCK_TRANSLATIONS)
        self.assertEqual(result, "HELLO, World! foo")

        async def coro() -> str:
            return await template.render_async(translations=MOCK_TRANSLATIONS)

        result = asyncio.run(coro())
        self.assertEqual(result, "HELLO, World! foo")
