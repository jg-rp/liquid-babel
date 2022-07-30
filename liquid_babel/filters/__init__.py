# flake8: noqa
# pylint: disable=useless-import-alias,missing-module-docstring
from .currency import Currency as Currency

# For convenience. Use defaults.
currency = Currency()

# For convenience. Something akin to Shopify's money filters.
money = currency
money_with_currency = Currency(default_format="¤#,##0.00 ¤¤")
money_without_currency = Currency(default_format="#,##0.00")
money_without_trailing_zeros = Currency(
    default_format="¤#,###",
    currency_digits=False,
)
