"""Unit tests for duration.parse_duration (T2 acceptance).

Spec recap:
- units: ms, s, m, h, d, strictly in the order d, h, m, s, ms; may be skipped,
  each unit at most once;
- no whitespace anywhere;
- every segment is an ASCII decimal positive integer (leading zeros allowed
  but the numeric value must be > 0);
- the single zero exception is the complete input "0s", returning 0;
- empty, negative, decimal, unknown unit, repeated unit, wrong order and any
  zero-valued segment raise ValueError;
- units are case-sensitive (no case folding);
- huge values are exact and never silently truncated.
"""

import unittest

from duration import parse_duration


class TestSingleUnits(unittest.TestCase):
    def test_milliseconds(self):
        self.assertEqual(parse_duration("1ms"), 1)
        self.assertEqual(parse_duration("42ms"), 42)
        self.assertEqual(parse_duration("1000ms"), 1000)

    def test_seconds(self):
        self.assertEqual(parse_duration("1s"), 1000)
        self.assertEqual(parse_duration("60s"), 60000)

    def test_minutes(self):
        self.assertEqual(parse_duration("1m"), 60000)
        self.assertEqual(parse_duration("90m"), 5400000)

    def test_hours(self):
        self.assertEqual(parse_duration("1h"), 3600000)
        self.assertEqual(parse_duration("24h"), 86400000)

    def test_days(self):
        self.assertEqual(parse_duration("1d"), 86400000)
        self.assertEqual(parse_duration("3d"), 259200000)

    def test_returns_plain_int(self):
        self.assertIs(type(parse_duration("1s")), int)
        self.assertIs(type(parse_duration("0s")), int)


class TestCombinations(unittest.TestCase):
    def test_full_chain(self):
        self.assertEqual(parse_duration("1d2h3m4s5ms"), 86400000 + 7200000 + 180000 + 4000 + 5)

    def test_skipping_intermediate_units(self):
        self.assertEqual(parse_duration("1d1ms"), 86400001)
        self.assertEqual(parse_duration("1d1s"), 86401000)
        self.assertEqual(parse_duration("1h1ms"), 3600001)
        self.assertEqual(parse_duration("1m1ms"), 60001)
        self.assertEqual(parse_duration("2h30m"), 9000000)
        self.assertEqual(parse_duration("1h30s"), 3630000)
        self.assertEqual(parse_duration("5m500ms"), 300500)
        self.assertEqual(parse_duration("2d3h"), 183600000)

    def test_adjacent_larger_units(self):
        self.assertEqual(parse_duration("1h1m1s1ms"), 3661001)
        self.assertEqual(parse_duration("1d1h1m1s1ms"), 90061001)

    def test_leading_zeros_allowed(self):
        self.assertEqual(parse_duration("0001s"), 1000)
        self.assertEqual(parse_duration("007ms"), 7)
        self.assertEqual(parse_duration("01d02h"), 93600000)
        self.assertEqual(parse_duration("0000000000000000001ms"), 1)

    def test_zero_exception(self):
        self.assertEqual(parse_duration("0s"), 0)

    def test_zero_combinations_rejected(self):
        for value in (
            "0ms", "0m", "0h", "0d",
            "00s", "000s",
            "0d0h", "0d1h", "1h0m", "1s0ms", "0s1ms", "0s0ms", "1m0s",
            "0d0h0m0s", "1d0h0m0s0ms",
        ):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    parse_duration(value)

    def test_millisecond_unit_not_parsed_as_minute_plus_second(self):
        self.assertEqual(parse_duration("7ms"), 7)
        self.assertEqual(parse_duration("1s7ms"), 1007)


class TestRepeatedUnits(unittest.TestCase):
    def test_repeated_units_rejected(self):
        for value in (
            "1ms1ms", "1s1s", "1m1m", "1h1h", "1d1d",
            "2m3m", "1d2d", "1h1h1h", "1s1ms1s",
        ):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    parse_duration(value)


class TestOrdering(unittest.TestCase):
    def test_wrong_order_rejected(self):
        for value in (
            "1s1m", "1m1h", "1h1d", "1ms1s", "1ms1m", "1ms1h",
            "1s1d", "1m1d", "1h1m1d", "1s1h1m", "1ms1d",
        ):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    parse_duration(value)

    def test_correct_order_accepted_is_covered_above(self):
        self.assertEqual(parse_duration("1d2h3m4s5ms"), 93784005)


class TestWhitespace(unittest.TestCase):
    def test_whitespace_rejected(self):
        for value in (
            " 1s", "1s ", "1 s", "1 s ", "1s\n", "\n1s", "\t1s", "0s ",
            " 0s", "0 s",
            "1\tms", "1s 2m", "1s  2m", "1m 1s", "1s\u00a0",
            " ", "\n", "\t", "1s\t2ms",
        ):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    parse_duration(value)


class TestMalformed(unittest.TestCase):
    def test_empty_string_rejected(self):
        with self.assertRaises(ValueError):
            parse_duration("")

    def test_negative_rejected(self):
        for value in ("-1s", "-0s", "-1ms", "--1s", "- 1s"):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    parse_duration(value)

    def test_signed_positive_rejected(self):
        for value in ("+1s", "+0s"):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    parse_duration(value)

    def test_decimal_rejected(self):
        for value in ("1.5s", "0.5ms", ".5s", "1.0s", "1,5s", "1e3s", "1e3ms"):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    parse_duration(value)

    def test_unknown_units_rejected(self):
        for value in (
            "1x", "1min", "1sec", "1hr", "1day", "1w", "1y",
            "1S", "1MS", "1Ms", "1M", "1H", "1D", "1\u00b5s",
        ):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    parse_duration(value)

    def test_bare_units_and_numbers_rejected(self):
        for value in ("ms", "s", "m", "h", "d", "1", "123", "0", "1s2", "12ms3"):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    parse_duration(value)

    def test_garbage_rejected(self):
        for value in ("abc", "1sfoo", "s1", "1ss", "1h 1m", "NaN", "inf", "1ms."):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    parse_duration(value)

    def test_non_ascii_digits_rejected(self):
        for value in ("\u0661s", "\uff11ms", "\u09e7s"):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    parse_duration(value)


class TestHugeValues(unittest.TestCase):
    def test_beyond_signed_64_bit(self):
        self.assertEqual(parse_duration("9223372036854775808ms"), 2 ** 63)
        self.assertEqual(parse_duration("9223372036854775808s"), 2 ** 63 * 1000)

    def test_beyond_unsigned_64_bit(self):
        self.assertEqual(parse_duration("18446744073709551616d"), 2 ** 64 * 86400000)

    def test_exact_arithmetic_without_truncation(self):
        self.assertEqual(parse_duration("1000000000000000000000d"), 10 ** 21 * 86400000)
        self.assertEqual(parse_duration("1" + "0" * 100 + "s"), 10 ** 100 * 1000)

    def test_beyond_int_str_conversion_limit(self):
        # CPython 3.11+ limits int(str) to 4300 digits by default; parsing must
        # still be exact rather than silently truncated or rejected.
        digits = "9" * 5000
        self.assertEqual(parse_duration(digits + "ms"), 10 ** 5000 - 1)


if __name__ == "__main__":
    unittest.main()
