import math


def is_number(value):
    return not isinstance(value, str) and (type(value) == int or type(value) == float)


def is_nullable(value):
    return value is None or value == '' or (is_number(value) and math.isnan(value))
