# -*- coding: utf-8 -*-
"""Тесты ядра L++ (unittest).

Запуск:  python -m unittest discover -s tests -v
"""

import io
import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
ADDONS = os.path.join(ROOT, "addons")
if ADDONS not in sys.path:
    sys.path.insert(0, ADDONS)

from lpp import (  # noqa: E402
    Interpreter, Lexer, LppError, LppNameError, LppSyntaxError, Parser,
    run_self_tests,
)


def run_code(code):
    """Выполняет код и возвращает собранный вывод."""
    buf = io.StringIO()
    interp = Interpreter(output=buf.write, input_reader=lambda p="": "")
    interp.run(code)
    return buf.getvalue()


class TestLexer(unittest.TestCase):
    def test_number_at_eof(self):
        # регрессия: раньше падало с IndexError
        toks = Lexer("x = 5").tokenize()
        self.assertEqual(toks[-2].value, 5)

    def test_hex_at_eof(self):
        toks = Lexer("x = 0xFF").tokenize()
        self.assertEqual(toks[-2].value, 255)

    def test_exponent_at_eof(self):
        toks = Lexer("x = 1e3").tokenize()
        self.assertEqual(toks[-2].value, 1000.0)

    def test_broken_exponent_is_not_number(self):
        # "1e" — это число 1 и идентификатор e
        toks = Lexer("x = 1e").tokenize()
        self.assertEqual(toks[2].value, 1)
        self.assertEqual(toks[3].type, "ID")

    def test_leading_dot_number(self):
        toks = Lexer("x = .5").tokenize()
        self.assertEqual(toks[-2].value, 0.5)

    def test_line_comment_slash(self):
        toks = Lexer("1 // комментарий\n2").tokenize()
        values = [t.value for t in toks]
        self.assertEqual(values, [1, 2, None])

    def test_hash_comment(self):
        toks = Lexer("1 # комментарий\n2").tokenize()
        values = [t.value for t in toks]
        self.assertEqual(values, [1, 2, None])

    def test_comment_inside_string(self):
        toks = Lexer('"http://x"').tokenize()
        self.assertEqual(toks[0].value, "http://x")

    def test_unclosed_string(self):
        with self.assertRaises(LppSyntaxError):
            Lexer('"abc').tokenize()

    def test_unknown_char(self):
        with self.assertRaises(LppSyntaxError):
            Lexer("a @ b").tokenize()


class TestParser(unittest.TestCase):
    def parse(self, code):
        return Parser(Lexer(code).tokenize()).program()

    def test_precedence(self):
        self.assertEqual(run_code("вывести(2+3*4)"), "14\n")

    def test_power_right_assoc(self):
        self.assertEqual(run_code("вывести(2**3**2)"), "512\n")

    def test_missing_end(self):
        with self.assertRaises(LppSyntaxError):
            self.parse("если 1 < 2 то:\nвывести(1)")

    def test_extra_end(self):
        with self.assertRaises(LppSyntaxError):
            self.parse("вывести(1)\nконец")

    def test_chained_assign(self):
        self.assertEqual(run_code("a = b = 3\nвывести(a + b)"), "6\n")

    def test_include_dotted(self):
        prog = self.parse("включить mixday.mathcore")
        self.assertEqual(prog[0].name, "mixday.mathcore")


class TestScope(unittest.TestCase):
    def test_local_does_not_leak(self):
        # регрессия: раньше локальная переменная становилась глобальной
        with self.assertRaises(LppNameError):
            run_code("функция ф():\nу = 42\nконец\nф()\nвывести(у)")

    def test_local_returns_value(self):
        self.assertEqual(
            run_code("функция ф():\nу = 42\nвернуть у\nконец\nвывести(ф())"),
            "42\n",
        )

    def test_global_is_mutated(self):
        self.assertEqual(
            run_code("x = 1\nфункция ф():\nx = 2\nконец\nф()\nвывести(x)"), "2\n"
        )

    def test_block_variable_visible_after(self):
        self.assertEqual(
            run_code("пока ложь то:\nконец\nесли истина то:\nz = 7\nконец\nвывести(z)"),
            "7\n",
        )


class TestRuntime(unittest.TestCase):
    def test_division_by_zero(self):
        with self.assertRaises(LppError):
            run_code("вывести(1/0)")

    def test_division_by_zero_message(self):
        try:
            run_code("вывести(1/0)")
        except LppError as e:
            self.assertIn("ноль", str(e))

    def test_type_error_is_friendly(self):
        with self.assertRaises(LppError):
            run_code('вывести("x" + 1)')

    def test_number_conversion_error(self):
        with self.assertRaises(LppError):
            run_code('вывести(число("abc"))')

    def test_len_of_number_error(self):
        with self.assertRaises(LppError):
            run_code("вывести(длина(5))")

    def test_undefined_variable(self):
        with self.assertRaises(LppNameError):
            run_code("вывести(нет_такой)")

    def test_index_out_of_range(self):
        with self.assertRaises(LppError):
            run_code("a = [1]\nвывести(a[5])")

    def test_float_index_rejected(self):
        with self.assertRaises(LppError):
            run_code("a = [1,2]\nвывести(a[0.5])")

    def test_string_len_callable_both_ways(self):
        self.assertEqual(run_code('вывести("абв".длина)'), "3\n")
        self.assertEqual(run_code('вывести("абв".длина())'), "3\n")

    def test_deep_recursion_is_friendly(self):
        code = (
            "функция ф(n):\n"
            "если n <= 0 то:\nвернуть 0\nконец\n"
            "вернуть 1 + ф(n - 1)\n"
            "конец\n"
            "вывести(ф(100000))"
        )
        with self.assertRaises(LppError):
            run_code(code)

    def test_infinite_loop_guard(self):
        with self.assertRaises(LppError):
            run_code("пока истина то:\nконец")

    def test_stop_flag(self):
        calls = {"n": 0}

        def should_stop():
            calls["n"] += 1
            return calls["n"] > 3

        interp = Interpreter(
            output=lambda s: None, input_reader=lambda p="": "",
            should_stop=should_stop,
        )
        with self.assertRaises(LppError):
            interp.run("i = 0\nпока истина то:\ni = i + 1\nконец")


class TestBuiltins(unittest.TestCase):
    def test_types(self):
        self.assertEqual(run_code("вывести(тип(5))"), "число\n")
        self.assertEqual(run_code('вывести(тип("x"))'), "строка\n")
        self.assertEqual(run_code("вывести(тип([1]))"), "массив\n")
        self.assertEqual(run_code("вывести(тип({}))"), "словарь\n")
        self.assertEqual(run_code("вывести(тип(истина))"), "логическое\n")

    def test_min_max(self):
        self.assertEqual(run_code("вывести(мин(3,1,2))"), "1\n")
        self.assertEqual(run_code("вывести(макс([3,1,2]))"), "3\n")

    def test_int_division_builtin(self):
        self.assertEqual(run_code("вывести(дел(7,2))"), "3\n")
        with self.assertRaises(LppError):
            run_code("вывести(дел(1,0))")

    def test_round(self):
        self.assertEqual(run_code("вывести(округ(3.14159, 2))"), "3.14\n")

    def test_random_int_in_range(self):
        for _ in range(20):
            out = run_code("вывести(случайное(1, 3))").strip()
            self.assertIn(out, ("1", "2", "3"))

    def test_string_methods(self):
        self.assertEqual(run_code('вывести("abc".верхний())'), "ABC\n")
        self.assertEqual(run_code('вывести(" a ".обрезать())'), "a\n")
        self.assertEqual(run_code('вывести("a,b".разбить(",")[1])'), "b\n")

    def test_array_methods(self):
        self.assertEqual(
            run_code("a = [3,1,2]\na.сортировать()\nвывести(a[0])"), "1\n"
        )

    def test_dict_methods(self):
        self.assertEqual(run_code('d = {"a":1}\nвывести(d.есть("a"))'), "истина\n")


class TestAddons(unittest.TestCase):
    def test_include_math(self):
        self.assertEqual(run_code("включить math\nвывести(math.sqrt(4))"), "2\n")

    def test_include_mixday(self):
        out = run_code("включить mixday\nвывести(mixday.Сумма(1,2,3))")
        self.assertIn("6", out)

    def test_mixday_platformer_exists(self):
        import mixday
        self.assertTrue(hasattr(mixday, "СоздатьПлатформер"))


class TestSelfTests(unittest.TestCase):
    def test_all_self_tests_pass(self):
        results = run_self_tests()
        failed = [(n, e) for n, ok, e in results if not ok]
        self.assertEqual(failed, [], f"провалились: {failed}")


class TestNewFeatures(unittest.TestCase):
    """v2.1: перебор коллекций, выбрать, поймать, классы, файлы."""

    def test_foreach_list(self):
        self.assertEqual(
            run_code("s = 0\nдля каждого x из [1,2,3] то:\ns = s + x\nконец\nвывести(s)"),
            "6\n",
        )

    def test_foreach_break(self):
        code = (
            "s = 0\n"
            "для каждого x из [1,2,3,4] то:\n"
            "если x == 3 то:\nпрервать\nконец\n"
            "s = s + x\n"
            "конец\n"
            "вывести(s)"
        )
        self.assertEqual(run_code(code), "3\n")

    def test_foreach_dict_keys(self):
        self.assertEqual(
            run_code('d = {"a":1,"b":2}\nдля каждого k из d то:\nвывести(k)\nконец'),
            "a\nb\n",
        )

    def test_switch_first_match(self):
        code = (
            "x = 2\nвыбрать x:\n"
            "вариант 1:\nвывести(1)\n"
            "вариант 2:\nвывести(2)\n"
            "вариант 3:\nвывести(3)\n"
            "конец"
        )
        self.assertEqual(run_code(code), "2\n")

    def test_switch_multiple_values(self):
        code = "x = 3\nвыбрать x:\nвариант 1, 3:\nвывести(\"да\")\nконец"
        self.assertEqual(run_code(code), "да\n")

    def test_switch_else(self):
        code = "x = 7\nвыбрать x:\nвариант 1:\nвывести(1)\nиначе:\nвывести(0)\nконец"
        self.assertEqual(run_code(code), "0\n")

    def test_try_catch(self):
        self.assertEqual(
            run_code("попробовать:\nвывести(1/0)\nпоймать:\nвывести(\"ok\")\nконец"),
            "ok\n",
        )

    def test_try_catch_message(self):
        out = run_code(
            "попробовать:\nвывести(1/0)\nпоймать о:\nвывести(о)\nконец"
        )
        self.assertIn("ноль", out)

    def test_try_does_not_swallow_stop(self):
        from lpp import LppError
        interp = Interpreter(
            output=lambda s: None, input_reader=lambda p="": "",
            should_stop=lambda: True,
        )
        with self.assertRaises(LppError):
            interp.run("попробовать:\nпока истина то:\nконец\nпоймать:\nвывести(1)\nконец")

    def test_class_basic(self):
        code = (
            "класс Точка:\n"
            "функция создать(x, y):\nя.x = x\nя.y = y\nконец\n"
            "функция длина():\nвернуть корень(я.x*я.x + я.y*я.y)\nконец\n"
            "конец\n"
            "т = новый Точка(3, 4)\n"
            "вывести(т.длина())"
        )
        self.assertEqual(run_code(code), "5\n")

    def test_class_field_mutation(self):
        code = (
            "класс Счётчик:\n"
            "функция создать():\nя.n = 0\nконец\n"
            "функция плюс():\nя.n = я.n + 1\nконец\n"
            "конец\n"
            "с = новый Счётчик()\nс.плюс()\nс.плюс()\nвывести(с.n)"
        )
        self.assertEqual(run_code(code), "2\n")

    def test_class_method_calls_other_method(self):
        code = (
            "класс А:\n"
            "функция два():\nвернуть 2\nконец\n"
            "функция четыре():\nвернуть я.два() * 2\nконец\n"
            "конец\n"
            "вывести(новый А().четыре())"
        )
        self.assertEqual(run_code(code), "4\n")

    def test_new_unknown_class(self):
        with self.assertRaises(LppError):
            run_code("x = новый НетТакого()")

    def test_include_file(self):
        import tempfile
        tmp = tempfile.mkdtemp()
        helper = os.path.join(tmp, "helper.lpp")
        with open(helper, "w", encoding="utf-8") as f:
            f.write("функция удвоить(x):\nвернуть x * 2\nконец\n")

        buf = io.StringIO()
        interp = Interpreter(output=buf.write, input_reader=lambda p="": "",
                             base_dir=tmp)
        interp.run('включить "helper.lpp"\nвывести(удвоить(21))')
        self.assertEqual(buf.getvalue(), "42\n")

    def test_include_missing_file(self):
        with self.assertRaises(LppError):
            run_code('включить "нет_такого.lpp"')

    def test_range_and_join(self):
        self.assertEqual(run_code("вывести(диапазон(3))"), "[0, 1, 2]\n")
        self.assertEqual(run_code('вывести(соединить(["a","b"], "+"))'), "a+b\n")


if __name__ == "__main__":
    unittest.main(verbosity=2)
