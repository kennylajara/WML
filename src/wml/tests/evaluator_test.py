from typing import cast, Any, Union

import wml.object as obj
from wml.ast import Program
from wml.errors import Error
from wml.evaluator import evaluate, NULL
from wml.lexer import Lexer
from wml.parser import Parser


def test_action_evaluation() -> None:
    source: str = "action(a) { return a + 5; }"
    evaluated = _evaluate_test(source)

    assert isinstance(evaluated, obj.Action)

    evaluated = cast(obj.Action, evaluated)
    assert len(evaluated.parameters) == 1
    assert str(evaluated.parameters[0]) == "a"
    assert str(evaluated.body) == "return (a + 5);"


def test_action_call_evaluation() -> None:
    tests: list[tuple[str, Any]] = [
        ("int age = action(a) { return a + 1; }; age(5);", 6),
        ("""
            int get_age = action(a) {
                return a;
            };
            get_age(5);
        """, 5),
        ("""
            int twice = action(a) {
                return a * 2;
            };
            twice(5);
        """, 10),
        ("""
            int add = action(a, b) {
                return a + b;
            };
            add(15, 11);
        """, 26),
        ("""
            int add = action(a, b) {
                return a + b;
            };
            add(8, add(5, 3));
        """, 16),
        ("action(a) { return a + 5; }(5);", 10),
        ("""
            bool tell_if_is_adult = action(int age) {
                if (age >= 18) {
                    return True;
                } else {
                    return False;
                };
            };
            tell_if_is_adult(18);
        """, True),
    ]

    for source, expected in tests:
        evaluated = _evaluate_test(source)
        if type(evaluated) is obj.Integer:
            _test_integer_object(evaluated, expected)
        elif type(evaluated) is obj.Boolean:
            _test_boolean_object(evaluated, expected)
        else:
            assert False, f"Unexpected type: {type(evaluated)}"


def test_assignment_evaluation() -> None:
    tests: list[tuple[str, Any]] = [
        ("int a = 5; a;", 5),
        ("flt a = 5.5 * 2; a;", 11.0),
        ("int a = 5; int b = a; b;", 5),
        ("int a = 5; int b = a; flt c = a + b + 5.0; c;", 15.0),
    ]

    for source, expected in tests:
        evaluated = _evaluate_test(source)
        if type(evaluated) is obj.Integer:
            _test_integer_object(evaluated, expected)
        elif type(evaluated) is obj.Float:
            _test_float_object(evaluated, expected)
        elif isinstance(evaluated, Error):
            assert False, f"Error: {evaluated}"
        else:
            assert False, f"Unexpected type: {type(evaluated)}"


# def test_assignment_evaluation_errors() -> None:  # TODO: Merge this with `test_error_handling`
#     tests: list[tuple[str, str]] = [
#         ("int a = 5.5;", "InvalidTypeAssignment: int != flt on line 1, column 5"),
#         # TODO: Add more tests, including constant reassignment and model reassignment
#     ]
#
#     for source, expected in tests:
#         evaluated = _evaluate_test_errors(source)
#         assert isinstance(evaluated, Error)
#         assert evaluated.message == expected
#
#
# # TODO: Add test for using variables before they are declared


def test_bang_operator() -> None:
    tests: list[tuple[str, bool]] = [
        ("!True", False),
        ("!False", True),
        ("!!True", True),
        ("!!False", False),
        ("!5", False),
        ("!!5", True),
        ('!0', True),
        ('!!0', False),
    ]

    for source, expected in tests:
        evaluated = _evaluate_test(source)
        _test_boolean_object(evaluated, expected)


def test_boolean_evaluation() -> None:
    tests: list[tuple[str, bool]] = [
        ("True", True),
        ("False", False),
        ("1 < 2", True),
        ("1 > 2", False),
        ("1 < 1", False),
        ("1 > 1", False),
        ("1 == 1", True),
        ("1 != 1", False),
        ("1 != 2", True),
        ("True == True", True),
        ("False == False", True),
        ("True == False", False),
        ("True != False", True),
        ("False != True", True),
        ("(1 < 2) == True", True),
        ("(1 < 2) == False", False),
        ("(1 > 2) == True", False),
        ("(1 > 2) == False", True),
    ]

    for source, expected in tests:
        evaluated = _evaluate_test(source)
        _test_boolean_object(evaluated, expected)


def test_builtin_functions() -> None:
    tests: list[tuple[str, Union[str, bytes]]] = [
        ("length('')", 0),
        ("length('four')", 4),
        ("length('hello, world!')", 13),
        ("length(1)", "UnsupportedArgumentType: Expected String, got Integer"),
        ("length('one', 'two')", "InvalidNumberOfArguments: Expected 1, got 2"),
    ]

    for source, expected in tests:
        evaluated = _evaluate_test(source)

        if type(expected) == int:
            expected = cast(int, expected)
            _test_integer_object(evaluated, expected)
        else:
            expected = cast(str, expected)
            _test_error_object(evaluated, expected)


def test_error_handling() -> None:
    tests: list[tuple[str, str]] = [
        ("5 + True;", "TypeMismatch: Integer + Boolean on line 1, column 3"),
        ("5 + True; 5;", "TypeMismatch: Integer + Boolean on line 1, column 3"),
        ("-True", "UnknownPrefixOperator: -Boolean on line 1, column 1"),
        ("True + False;", "UnknownInfixOperator: Boolean + Boolean on line 1, column 6"),
        ("5; True - False; 5", "UnknownInfixOperator: Boolean - Boolean on line 1, column 9"),
        ("if (10 > 1) { True + False; }", "UnknownInfixOperator: Boolean + Boolean on line 1, column 20"),
        ("""
            if (10 > 1) {
                if (10 > 1) {
                    return True + False;
                }
                return 1;
            }
        """, "UnknownInfixOperator: Boolean + Boolean on line 4, column 33"),
        ("foobar", "TypeError: foobar, line 1, column 1"),
        ('"Hello" / "World"', "UnknownInfixOperator: String / String on line 1, column 8"),
    ]

    for source, expected in tests:
        evaluated = _evaluate_test(source)

        evaluated = cast(Error, evaluated)
        assert evaluated.message == expected


def test_if_evaluation() -> None:
    tests: list[tuple[str, Any]] = [
        ("if (True) { 10 }", 10),
        ("if (False) { 10 }", None),
        ("if (1) { 10.5 }", 10.5),
        ("if (1 < 2) { 10.5 }", 10.5),
        ("if (1 > 2) { 10 }", None),
        ("if (1 < 2) { 10 } else { 20 }", 10),
        ("if (1 > 2) { 10 } else { 20 }", 20),
    ]

    for source, expected in tests:
        evaluated = _evaluate_test(source)

        if type(evaluated) is obj.Integer:
            _test_integer_object(evaluated, expected)
        elif type(evaluated) is obj.Float:
            _test_float_object(evaluated, expected)
        else:
            _test_null_object(evaluated)


def test_float_evaluation() -> None:
    tests: list[tuple[str, float]] = [
        ("5.5", 5.5),
        ("-5.5", -5.5),
        ("5.5 + 5.5", 11.0),
        ("5.5 - 5.5", 0.0),
        ("5.5 * 5.5", 30.25),
        ("5.5 / 5.5", 1.0),
        ("5.5 + 5", 10.5),
        ("5.5 - 5", 0.5),
        ("5.5 * 5", 27.5),
        ("5.5 / 5", 1.1),
    ]

    for source, expected in tests:
        evaluated = _evaluate_test(source)
        _test_float_object(evaluated, expected)


def test_integer_evaluation() -> None:
    tests: list[tuple[str, int]] = [
        ("5", 5),
        ("10", 10),
        ("-5", -5),
        ("-10", -10),
        ("5 + 5", 10),
        ("5 - 10", -5),
        ("2 * 2 * 2 * 2", 16),
        ("2 * 5 - 3", 7),
        ("2 * (5 - 3)", 4),
        # ("5 // 2", 2),  # TODO: Implement integer division
        # ("5 % 2", 1),  # TODO: Implement modulo
        # ("2 ** 3", 8),  # TODO: Implement exponentiation
        # ("50 / 2", 25),  # TODO: Move to float evaluation
        # ("(2 + 7) / 3", 3),  # TODO: Move to float evaluation
        # ("50 / 2 * 2 + 10", 60),  # TODO: Move to float evaluation
    ]

    for source, expected in tests:
        evaluated = _evaluate_test(source)
        _test_integer_object(evaluated, expected)


def test_return_evaluation() -> None:
    tests: list[tuple[str, Any]] = [
        ("return 10.5;", 10.5),
        ("return 10.5; 9;", 10.5),
        ("return 2 * 5; 9;", 10),
        ("9; return 2 * 5; 9;", 10),  # TODO: Remove support for implicit returns
        ("""
            if (10 > 1) {
                if (20 > 10) {
                    return 9;
                }
                return 10;
            }
        """, 9),
    ]

    for source, expected in tests:
        evaluated = _evaluate_test(source)
        if type(evaluated) is obj.Integer:
            _test_integer_object(evaluated, expected)
        elif type(evaluated) is obj.Float:
            _test_float_object(evaluated, expected)
        else:
            _test_null_object(evaluated)


def test_string_evaluation() -> None:
    tests: list[tuple[str, str]] = [
        ('"Hello, World!"', '"Hello, World!"'),
        ("action() { return 'WML is awesome!'; }();", "'WML is awesome!'"),
    ]

    for source, expected in tests:
        evaluated = _evaluate_test(source)
        _test_string_object(evaluated, expected)


def test_string_concatenation() -> None:
    tests: list[tuple[str, str]] = [
        ("'Foo' + 'Bar'", '"FooBar"'),  # Simple concatenation
        ('"Hello" + " " + "World!"', '"Hello World!"'),  # Multiple concatenation
        ('"Hello" + \'World!\'', '"HelloWorld!"'),  # Different quotes (prefer double quotes)
        ('"Stacy\'s " + "Mom"', '"Stacy\'s Mom"'),  # Single quote inside double quotes (prefer double quotes)
        ("'I am ' + 'the \"king\"'", "'I am the \"king\"'"),  # Double quote inside single quotes (prefer single quotes)
        ('"I\'m " + \'the "king"\'', '"I\'m the \"king\""'),  # Single quote inside double quotes (prefer double quotes)
        (
            '''
            str hello = action(str name) {
                return "Hello, " + name + '!';
            };
            hello("Kenny");
            ''',
            '"Hello, Kenny!"',
        )
    ]

    for source, expected in tests:
        evaluated = _evaluate_test(source)
        _test_string_object(evaluated, expected)

def test_string_comparison() -> None:
    tests: list[tuple[str, bool]] = [
        ('"Hello" == "Hello"', True),
        ("'Hello' == 'Hello'", True),
        ('"Hello" == \'Hello\'', True),
        ('\'Hello\' == "Hello"', True),
        ('"Hello" != "Hello"', False),
        ("'Hello' != 'Hello'", False),
        ('"Hello" != \'Hello\'', False),
        ('\'Hello\' != "Hello"', False),
        ('"Hello" == "World"', False),
        ("'Hello' == 'World'", False),
        ('"Hello" == \'World\'', False),
        ('\'Hello\' == "World"', False),
        ('"Hello" != "World"', True),
        ("'Hello' != 'World'", True),
        ('"Hello" != \'World\'', True),
        ('\'Hello\' != "World"', True),
        ('"Hello" == "Hello, World!"', False),
        ("'Hello' == 'Hello, World!'", False),
        ('"Hello" == \'Hello, World!\'', False),
        ('\'Hello\' == "Hello, World!"', False),
        ('"Hello" != "Hello, World!"', True),
        ("'Hello' != 'Hello, World!'", True),
        ('"Hello" != \'Hello, World!\'', True),
        ('\'Hello\' != "Hello, World!"', True),
    ]

    for source, expected in tests:
        evaluated = _evaluate_test(source)
        _test_boolean_object(evaluated, expected)


def _evaluate_test(source: str) -> obj.Type:
    lexer: Lexer = Lexer(source)
    parser: Parser = Parser(lexer)
    program: Program = parser.parse_program()
    env: obj.Environment = obj.Environment()

    assert len(parser.errors) == 0, f"Errors found: {parser.errors}"

    evaluated: obj.Type = evaluate(program, env)

    assert evaluated is not None
    return evaluated


def _evaluate_test_errors(source: str):
    lexer: Lexer = Lexer(source)
    parser: Parser = Parser(lexer)
    program: Program = parser.parse_program()
    env: obj.Environment = obj.Environment()

    assert len(parser.errors) == 0, f"Errors found: {parser.errors}"

    evaluated: obj.Type = evaluate(program, env)
    assert evaluated is None

    return program.errors[0]


def _test_boolean_object(evaluated: obj.Type, expected: bool) -> None:
    assert isinstance(evaluated, obj.Boolean), f"Expected {expected}, got {evaluated.inspect()}"

    evaluated = cast(obj.Boolean, evaluated)
    assert evaluated.value == expected


def _test_error_object(evaluated: obj.Type, expected: str) -> None:
    assert isinstance(evaluated, Error)

    evaluated = cast(Error, evaluated)
    assert evaluated.message == expected


def _test_float_object(evaluated: obj.Type, expected: float) -> None:
    assert isinstance(evaluated, obj.Float), f"Expected {expected}, got {evaluated.inspect()}"

    evaluated = cast(obj.Float, evaluated)
    assert evaluated.value == expected


def _test_integer_object(evaluated: obj.Type, expected: int) -> None:
    assert isinstance(evaluated, obj.Integer)

    evaluated = cast(obj.Integer, evaluated)
    assert evaluated.value == expected


def _test_null_object(evaluated: obj.Type) -> None:
    assert evaluated is NULL


def _test_string_object(evaluated: obj.Type, expected: str) -> None:
    assert isinstance(evaluated, obj.String)

    evaluated = cast(obj.String, evaluated)
    assert evaluated.value == expected
