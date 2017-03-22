import string

MAX_BASE_COUNT = 4
digs = string.digits + string.ascii_letters


def int2base(x, base):
    """ Convert an integer to a string in the given base"""
    if x < 0:
        sign = -1
    elif x == 0:
        return digs[0]
    else:
        sign = 1

    x *= sign
    digits = []

    while x:
        digits.append(digs[x % base])
        x //= base

    if sign < 0:
        digits.append('-')

    digits.reverse()

    return ''.join(digits)


def get_numbers_consisting_of_n_digits_in_base(digits, base):
    start_number = 1
    numbers = []
    while True:
        str_num = int2base(start_number, base)
        if len(str_num) > digits:
            break
        elif len(str_num) == digits:
            numbers.append(start_number)
        start_number += 1

    return numbers


def number_is_basic(number, base):
    """ See if a given number is basic or not"""
    based_number = int2base(number, base)

    for i in range(1, len(based_number)+1):
        prefix = based_number[:i]
        converted_number = int(prefix, base)
        if converted_number % i != 0:
            return False
    return True

# PRE CALCULATE ALL NUMBERS
base_numbers_digits= {}
max_valid_digits_for_base = {}


for base in range(2, MAX_BASE_COUNT+1):
    digits = 1
    while True:
        valid_numbers = get_numbers_consisting_of_n_digits_in_base(digits, base)
        num_valids = len([True for number in valid_numbers if number_is_basic(number, base)])
        base_numbers_digits[(base, digits)] = num_valids

        if num_valids == 0:
            max_valid_digits_for_base[base] = digits
            break
        digits += 1


test_case_count = int(input())
for _ in range(test_case_count):
    base, digits = [int(p) for p in input().split()]
    if digits > max_valid_digits_for_base[base]:
        print(0)
    else:
        print(base_numbers_digits[(base, digits)])
