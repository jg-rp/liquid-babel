# Python Liquid Babel

Internationalization and localization for [Liquid](https://github.com/jg-rp/liquid/) templates.

## Project Status

This project is in its infancy. Documentation is currently limited to doc comments in source files. I'll update this readme with links to docs and PyPi as and when they become available.

## Currency

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
```

**Output**

```plain
$100,457.99
£100,457.99
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

## Number / Decimal

Decimal number formatting. ([source](https://github.com/jg-rp/liquid-babel/blob/main/liquid-babel/filters/number.py), [tests](https://github.com/jg-rp/liquid_babel/blob/main/tests/test_number.py))

Instances of the `Number` class default to looking for a locale in a render context variable called `locale`. It uses the locale's standard format and falls back to en_US if those context variables don't exist.

```python
from liquid import Environment
from liquid_babel.filters import Number

env = Environment()
env.add_filter("decimal", Number())

# parse a number from a string in the default (en_US) input locale.
template = env.from_string("{{ '10,000.23' | decimal }}")
print(template.render(locale="de"))
print(template.render(locale="en_GB"))
```

**Output**

```plain
10.000,23
10,000.23
```

## Filters on the to-do list

- Date and time formatting
- List formatting
- Pluralization
- Inline translation

## Tags on the to-do list

- Translation block tag
