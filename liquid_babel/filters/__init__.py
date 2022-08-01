# flake8: noqa
# pylint: disable=useless-import-alias,missing-module-docstring
from .currency import Currency as Currency
from .date_and_time import DateTime as DateTime
from .number import Number as Number

# For convenience. Use defaults.
currency = Currency()
number = Number()

# For convenience. Something akin to Shopify's money filters.
money = currency
money_with_currency = Currency(default_format="¤#,##0.00 ¤¤")
money_without_currency = Currency(default_format="#,##0.00")
money_without_trailing_zeros = Currency(
    default_format="¤#,###",
    currency_digits=False,
)

__all__ = [
    "Currency",
    "DateTime",
    "Number",
    "currency",
    "number",
    "money",
    "money_with_currency",
    "money_without_currency",
    "money_without_trailing_zeros",
]
