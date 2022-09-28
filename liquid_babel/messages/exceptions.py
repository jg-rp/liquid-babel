"""Liquid translation exceptions."""
from liquid.exceptions import Error
from liquid.exceptions import LiquidSyntaxError


class TranslationError(Error):
    """Base exception for translation errors."""


class TranslationSyntaxError(LiquidSyntaxError):
    """Exception raised when a syntax error is found within a translation block."""


class TranslationValueError(TranslationError):
    """Exception raised when translation message interpolation fails with a ValueError."""


class TranslationKeyError(TranslationError):
    """Exception raised when translation message interpolation fails with a KeyError."""
