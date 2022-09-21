"""Liquid translation exceptions."""
from liquid.exceptions import Error


class TranslationError(Error):
    """Base exception for translation errors."""


class TranslationValueError(TranslationError):
    """Exception raised when translation message interpolation fails with a ValueError."""


class TranslationKeyError(TranslationError):
    """Exception raised when translation message interpolation fails with a KeyError."""
