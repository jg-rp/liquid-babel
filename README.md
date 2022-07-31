# Python Liquid Babel

Internationalization and localization for [Liquid](https://github.com/jg-rp/liquid/) templates.

[![PyPI](https://img.shields.io/pypi/v/liquid-babel?style=flat-square)](https://pypi.org/project/liquid-babel/)
[![GitHub Workflow Status](https://img.shields.io/github/workflow/status/jg-rp/liquid-babel/Tests?style=flat-square)](https://github.com/jg-rp/liquid-babel/actions)
[![PyPI - License](https://img.shields.io/pypi/l/liquid-babel?style=flat-square)](https://github.com/jg-rp/liquid-babel/blob/main/LICENSE)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/liquid-babel?style=flat-square)](https://pypi.org/project/liquid-babel/)
![PyPy Version](https://img.shields.io/badge/pypy-3.7%20%7C%203.8-blue?style=flat-square)

## Install

Install Python Liquid Babel using [pipenv](https://pipenv.pypa.io/en/latest/):

```plain
$ pipenv install liquid-babel
```

Or [pip](https://pip.pypa.io/en/stable/getting-started/):

```plain
python -m pip install -U liquid-babel
```

## Currency Filter

Currency (aka money) formatting ([source](https://github.com/jg-rp/liquid-babel/blob/main/liquid-babel/filters/currency.py), [tests](https://github.com/jg-rp/liquid_babel/blob/main/tests/test_currency.py))

**Default options**

Instances of the `Currency` class default to looking for a locale in a render context variable called `locale`, and a currency code in a render context variable called `currency_code`. It uses the locale's standard format and falls back to en_US and USD if those context variables don't exist.

```python
from liquid import Environment
from liquid_babel.filters import Currency

env = Environment()
env.add_filter("currency", Currency())

template = env.from_string("{{ 100457.99 | currency }}")

print(template.render())
print(template.render(currency_code="GBP"))
print(template.render(locale="de", currency_code="CAD"))
```

**Output**

```plain
$100,457.99
£100,457.99
100.457,99 CA$
```

### Money

For convenience, some "money" filters are defined that mimic Shopify's money filter behavior.

```python
from liquid import Environment
from liquid_babel.filters import money
from liquid_babel.filters import money_with_currency
from liquid_babel.filters import money_without_currency
from liquid_babel.filters import money_without_trailing_zeros

env = Environment()
env.add_filter("money", money)
env.add_filter("money_with_currency", money_with_currency)
env.add_filter("money_without_currency", money_without_currency)
env.add_filter("money_without_trailing_zeros", money_without_trailing_zeros)

template = env.from_string("""\
{% assign amount = 10 %}
{{ amount | money }}
{{ amount | money_with_currency }}
{{ amount | money_without_currency }}
{{ amount | money_without_trailing_zeros }}
""")

print(template.render(currency_code="CAD", locale="en_CA"))
```

**Output**

```plain
$10.00
$10.00 CAD
10.00
$10
```

## Number / Decimal Filter

Decimal number formatting. ([source](https://github.com/jg-rp/liquid-babel/blob/main/liquid_babel/filters/number.py), [tests](https://github.com/jg-rp/liquid-babel/blob/main/tests/test_number.py))

Instances of the `Number` class default to looking for a locale in a render context variable called `locale`. It uses the locale's standard format and falls back to en_US if those context variables don't exist.

```python
from liquid import Environment
from liquid_babel.filters import Number

env = Environment()
# Register an instance of the `Number` class as a filter called "decimal".
env.add_filter("decimal", Number())

# Parse a number from a string in the default (en_US) input locale.
template = env.from_string("""\
{{ '10,000.23' | decimal }}
{{ '10,000.23' | decimal: group_separator: false }}
""")
print(template.render(locale="de"))
print(template.render(locale="en_GB"))
```

**Output**

```plain
10.000,23
10000,23

10,000.23
10000.23
```

## Filters on the to-do list

- Date and time formatting
- List formatting
- Pluralization
- Inline translation

## Tags on the to-do list

- Translation block tag
