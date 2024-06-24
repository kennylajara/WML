from typing import cast, Any, Type

import pytest

from wml.lexer import Lexer
from wml.parser import Parser
from wml.ast import (
    Action,
    Block,
    Boolean,
    Call,
    ModelStatement,
    Constant,
    Expression,
    ExpressionStatement,
    Float,
    Identifier,
    If,
    Infix,
    Integer,
    Prefix,
    Program,
    ReturnStatement,
    SetStatement,
    Variable, StringLiteral,
)


def test_parser_program():
    source = "class Foo {}"
    lexer = Lexer(source)
    parser = Parser(lexer)

    program = parser.parse_program()

    assert program is not None
    assert isinstance(program, Program)

def test_action_literal() -> None:
    source = "action(x, y) { x + y; }"
    lexer = Lexer(source)
    parser = Parser(lexer)

    program = parser.parse_program()

    _test_program_statements(parser, program)

    # Test correct node type
    action_literal = cast(Action, cast(ExpressionStatement, program.statements[0]).expression)
    assert isinstance(action_literal, Action)

    # Test parameters
    assert len(action_literal.parameters) == 2
    assert action_literal.parameters[0].value == "x"
    assert action_literal.parameters[1].value == "y"

    # Test body
    assert action_literal.body is not None
    assert len(action_literal.body.statements) == 1

    body_statement = cast(ExpressionStatement, action_literal.body.statements[0])
    assert body_statement.expression is not None
    _test_infix_expression(body_statement.expression, "x", "+", "y")


def test_action_parameters_type() -> None:
    source = "action(int x, flt y) { x + y; }"
    lexer = Lexer(source)
    parser = Parser(lexer)

    program = parser.parse_program()

    _test_program_statements(parser, program)

    # Test correct node type
    action_literal = cast(Action, cast(ExpressionStatement, program.statements[0]).expression)
    assert isinstance(action_literal, Action)

    # Test parameters
    assert len(action_literal.parameters) == 2
    assert action_literal.parameters[0].typing is not None
    assert action_literal.parameters[0].typing.literal == "int"
    assert action_literal.parameters[1].typing is not None
    assert action_literal.parameters[1].typing.literal == "flt"



def test_action_parameters() -> None:
    tests = [
        {
            "input": "action() {};",
            "expected_params": [],
        },
        {
            "input": "action(x) {};",
            "expected_params": ["x"],
        },
        {
            "input": "action(x, y, z) {};",
            "expected_params": ["x", "y", "z"],
        },
    ]

    for test in tests:
        lexer = Lexer(test["input"])
        parser = Parser(lexer)
        program = parser.parse_program()

        action = cast(Action, cast(ExpressionStatement, program.statements[0]).expression)
        assert cast(Action, cast(ExpressionStatement, program.statements[0]).expression)

        assert len(action.parameters) == len(test["expected_params"])

        for idx, param in enumerate(test["expected_params"]):
            assert action.parameters[idx].value == param


def test_parse_error() -> None:
    source = "model thing {};" # Lowercase class name
    lexer = Lexer(source)
    parser = Parser(lexer)
    parser.parse_program()

    print(parser.errors)
    assert len(parser.errors) == 3


def test_boolean_expression() -> None:
    source = "True; False;"
    lexer = Lexer(source)
    parser = Parser(lexer)

    program = parser.parse_program()

    _test_program_statements(parser, program, 2)

    expected_values = [True, False]

    for statement, expected_value in zip(program.statements, expected_values):
        expression_statement = cast(ExpressionStatement, statement)

        assert expression_statement.expression is not None
        assert isinstance(expression_statement.expression, Boolean)
        _test_literal_expression(expression_statement.expression, expected_value)


def test_call_expression() -> None:
    source: str = 'sum(1, 2 * 3, 4 + 5);'
    lexer: Lexer = Lexer(source)
    parser: Parser = Parser(lexer)

    program: Program = parser.parse_program()

    _test_program_statements(parser, program)

    call = cast(Call, cast(ExpressionStatement,
                           program.statements[0]).expression)
    assert isinstance(call, Call)
    _test_variable(call.action, 'sum')

    # Test arguments
    assert call.arguments is not None
    assert len(call.arguments) == 3
    _test_literal_expression(call.arguments[0], 1)
    _test_infix_expression(call.arguments[1], 2, '*', 3)
    _test_infix_expression(call.arguments[2], 4, '+', 5)


def test_constant_expression() -> None:
    source = "FOOBAR;"
    lexer = Lexer(source)
    parser = Parser(lexer)

    program = parser.parse_program()

    _test_program_statements(parser, program)

    expression_statement = cast(ExpressionStatement, program.statements[0])
    assert expression_statement.expression is not None
    _test_literal_expression(expression_statement.expression, "FOOBAR")


def test_float_expression() -> None:
    source = "5.5;"
    lexer = Lexer(source)
    parser = Parser(lexer)

    program = parser.parse_program()

    _test_program_statements(parser, program)

    expression_statement = cast(ExpressionStatement, program.statements[0])
    assert expression_statement.expression is not None
    _test_literal_expression(expression_statement.expression, 5.5)


def test_if_expression() -> None:
    source: str = "if (x < y) { z; }"
    lexer: Lexer = Lexer(source)
    parser: Parser = Parser(lexer)

    program: Program = parser.parse_program()

    _test_program_statements(parser, program)

    # Test correct node type
    if_expression = cast(If, cast(ExpressionStatement, program.statements[0]).expression)
    assert isinstance(if_expression, If)

    # Test condition
    assert if_expression.condition is not None
    _test_infix_expression(if_expression.condition, "x", "<", "y")

    # Test consequence
    assert if_expression.consequence is not None
    assert len(if_expression.consequence.statements) == 1
    assert isinstance(if_expression.consequence, Block)

    consequence_statement = cast(ExpressionStatement, if_expression.consequence.statements[0])
    assert consequence_statement.expression is not None
    _test_variable(consequence_statement.expression, "z")

    # Test alternative
    assert if_expression.alternative is None


def test_if_else_expression() -> None:
    source: str = 'if (x != y) { x } else { y }'
    lexer: Lexer = Lexer(source)
    parser: Parser = Parser(lexer)

    program: Program = parser.parse_program()

    _test_program_statements(parser, program)

    # Test correct node type
    if_expression = cast(If, cast(ExpressionStatement, program.statements[0]).expression)
    assert isinstance(if_expression, If)

    # Test condition
    assert if_expression.condition is not None
    _test_infix_expression(if_expression.condition, 'x', '!=', 'y')

    # Test consequence
    assert if_expression.consequence is not None
    assert isinstance(if_expression.consequence, Block)
    assert len(if_expression.consequence.statements) == 1

    consequence_statement = cast(ExpressionStatement, if_expression.consequence.statements[0])
    assert consequence_statement.expression is not None
    _test_variable(consequence_statement.expression, 'x')

    # Test alternative
    assert if_expression.alternative is not None
    assert isinstance(if_expression.alternative, Block)
    assert len(if_expression.alternative.statements) == 1

    alternative_statement = cast(ExpressionStatement, if_expression.alternative.statements[0])
    assert alternative_statement.expression is not None
    _test_variable(alternative_statement.expression, 'y')


def test_infix_expression() -> None:
    source = "5 + 5; 5 - 5; 5 * 5; 5 / 5; 5 < 5; 5 > 5; 5 == 5; 5 != 5; 5 <= 5; 5 >= 5; True == True; False != True; False == False;"
    lexer = Lexer(source)
    parser = Parser(lexer)

    program = parser.parse_program()

    _test_program_statements(parser, program, 13)

    expected_operators_and_values: list[tuple[Any, str, Any]] = [
        (5, "+", 5),
        (5, "-", 5),
        (5, "*", 5),
        (5, "/", 5),
        (5, "<", 5),
        (5, ">", 5),
        (5, "==", 5),
        (5, "!=", 5),
        (5, "<=", 5),
        (5, ">=", 5),
        (True, "==", True),
        (False, "!=", True),
        (False, "==", False),
    ]

    for statement, (expected_left, expected_operator, expected_right) in zip(program.statements, expected_operators_and_values):
        statement = cast(ExpressionStatement, statement)
        assert statement.expression is not None
        assert isinstance(statement.expression, Infix)
        _test_infix_expression(statement.expression, expected_left, expected_operator, expected_right)


def test_identifier_expression() -> None:
    source = "FooBar;"
    lexer = Lexer(source)
    parser = Parser(lexer)

    program = parser.parse_program()

    _test_program_statements(parser, program)

    expression_statement = cast(ExpressionStatement, program.statements[0])
    assert expression_statement.expression is not None
    _test_literal_expression(expression_statement.expression, "FooBar")


def test_integer_expression() -> None:
    source = "5;"
    lexer = Lexer(source)
    parser = Parser(lexer)

    program = parser.parse_program()

    _test_program_statements(parser, program)

    expression_statement = cast(ExpressionStatement, program.statements[0])
    assert expression_statement.expression is not None
    _test_literal_expression(expression_statement.expression, 5)


def test_model_statements() -> None:
    source = """
        model Foo {};
        model Bar(Foo){};
        model Baz(Bar){};
    """
    lexer = Lexer(source)
    parser = Parser(lexer)

    program = parser.parse_program()

    assert len(parser.errors) == 0
    assert len(program.statements) == 3
    for i, stmt in enumerate(program.statements):
        assert stmt.token_literal() == "model"
        assert isinstance(stmt, ModelStatement)
        assert stmt.name is not None
        assert stmt.name.value == ["Foo", "Bar", "Baz"][i]
        assert stmt.parent is None if i == 0 else stmt.parent is not None and stmt.parent.value == ["Foo", "Bar"][i - 1]


def test_model_statements_with_body() -> None:
    source = """
        model Foo {
            int x = 1;
            flt y = 1.5;
            bool z = True;
        };
        model Bar {
            int a = 2;
            flt b = 2.5;
            bool c = False;
        };
    """
    lexer = Lexer(source)
    parser = Parser(lexer)

    program = parser.parse_program()

    assert len(parser.errors) == 0
    assert len(program.statements) == 2

    for i, stmt in enumerate(program.statements):
        assert stmt.token_literal() == "model"
        assert isinstance(stmt, ModelStatement)
        assert stmt.name is not None
        assert stmt.name.value == ["Foo", "Bar"][i]

        assert stmt.body is not None
        assert isinstance(stmt.body, Block)
        assert stmt is not None
        assert isinstance(stmt.body.statements, list)
        assert len(stmt.body.statements) == 3

        for j, body_stmt in enumerate(stmt.body.statements):
            assert isinstance(body_stmt, SetStatement)
            body_stmt = cast(SetStatement, body_stmt)
            assert body_stmt.token_literal() == ["int", "flt", "bool"][j]
            assert body_stmt.name is not None
            assert body_stmt.name.value == ["x", "y", "z", "a", "b", "c"][3 * i + j]
            assert body_stmt.value is not None
            assert body_stmt.value.token_literal() == ["1", "1.5", "True", "2", "2.5", "False"][3 * i + j]


def test_operator_precedence() -> None:
    # TODO: Remove unnecessary parentheses
    #  This can be done by adding a precedence table to the ExpressionStatement parse function
    test_sources: list[tuple[str, str, int]] = [
        ('-a * b;', '((-a) * b);', 1),
        ('!-a;', '(!(-a));', 1),
        ('a + b + c;', '((a + b) + c);', 1),
        ('a + b - c;', '((a + b) - c);', 1),
        ('a * b * c;', '((a * b) * c);', 1),
        ('a + b / c;', '(a + (b / c));', 1),
        ('a * b / c;', '((a * b) / c);', 1),
        ('a + b * c + d / e - f;', '(((a + (b * c)) + (d / e)) - f);', 1),
        ('5 > 4 == 3 < 4;', '((5 > 4) == (3 < 4));', 1),
        ('3 - 4 * 5 == 3 * 1 + 4 * 5;', '((3 - (4 * 5)) == ((3 * 1) + (4 * 5)));', 1),
        ('3 + 4; -5 * 5;', '(3 + 4);((-5) * 5);', 2),
        ('True;', 'True;', 1),
        ('False;', 'False;', 1),
        ('3 > 5 == True;', '((3 > 5) == True);', 1),
        ('3 < 5 == False;', '((3 < 5) == False);', 1),
        ('1 + (2 + 3) + 4;', '((1 + (2 + 3)) + 4);', 1),
        ('(5 + 5) * 2;', '((5 + 5) * 2);', 1),
        ('2 / (5 + 5);', '(2 / (5 + 5));', 1),
        ('-(5 + 5);', '(-(5 + 5));', 1),
        ('a + sum(b * c) + d;', '((a + sum((b * c))) + d);', 1),
        ('sum(a, b, 1, 2 * 3, 4 + 5, sum(6, 7 * 8));', 'sum(a, b, 1, (2 * 3), (4 + 5), sum(6, (7 * 8)));', 1),
        ('sum(a + b + c * d / f + g);', 'sum((((a + b) + ((c * d) / f)) + g));', 1),
    ]

    for source, expected_result, expected_statement_count in test_sources:
        lexer: Lexer = Lexer(source)
        parser: Parser = Parser(lexer)

        program: Program = parser.parse_program()

        _test_program_statements(parser, program, expected_statement_count)
        assert str(program) == expected_result


def test_prefix_expression() -> None:
    source = "!8; -7; !True; !False;"
    lexer = Lexer(source)
    parser = Parser(lexer)

    program = parser.parse_program()

    _test_program_statements(parser, program, 4)

    for statement, (expected_operator, expected_value) in zip(program.statements, [("!", 8), ("-", 7), ("!", True), ("!", False)]):
        statement = cast(ExpressionStatement, statement)
        assert statement.expression is not None
        assert isinstance(statement.expression, Prefix)

        prefix = cast(Prefix, statement.expression)
        assert prefix.operator == expected_operator

        assert prefix.right is not None
        _test_literal_expression(prefix.right, expected_value)


def test_return_statement() -> None:
    source = """
        return 1;
        return 1.5;
        return foo;
        return Bar;
        return BAX;
        return True;
        return False;
    """
    lexer = Lexer(source)
    parser = Parser(lexer)

    program = parser.parse_program()

    assert len(program.statements) == 7

    expected_instances_types = [Integer, Float, Variable, Identifier, Constant, Boolean, Boolean]
    expected_literal_values = [1, 1.5, "foo", "Bar", "BAX", True, False]

    for i, stmt in enumerate(program.statements):
        assert stmt.token_literal() == "return"
        assert isinstance(stmt, ReturnStatement)
        stmt = cast(ReturnStatement, stmt)
        assert stmt.value is not None
        assert isinstance(stmt.value, expected_instances_types[i])
        _test_literal_expression(stmt.value, expected_literal_values[i])


def test_set_statement_boolean() -> None:
    source = """
        bool x = True;
        bool y = False;
    """
    lexer = Lexer(source)
    parser = Parser(lexer)

    program = parser.parse_program()

    assert len(program.statements) == 2
    for i, stmt in enumerate(program.statements):
        assert stmt.token_literal() == "bool"
        assert isinstance(stmt, SetStatement)
        assert isinstance(stmt.name, Identifier)
        assert stmt.name.value == ["x", "y"][i]
        assert isinstance(stmt.value, Boolean)
        assert stmt.value.token_literal() == ["True", "False"][i]


def test_set_statement_float() -> None:
    source = """
            flt x = 1.5;
    """
    lexer = Lexer(source)
    parser = Parser(lexer)

    program = parser.parse_program()

    assert len(program.statements) == 1
    stmt = program.statements[0]
    assert isinstance(stmt, SetStatement)
    assert stmt.token_literal() == "flt"
    assert isinstance(stmt.name, Identifier)
    assert stmt.name.value == "x"
    assert isinstance(stmt.value, Float)
    assert stmt.value.token_literal() == "1.5"


def test_set_statement_int() -> None:
    source = """
            int x = 1;
    """
    lexer = Lexer(source)
    parser = Parser(lexer)

    program = parser.parse_program()

    assert len(program.statements) == 1
    stmt = program.statements[0]
    assert isinstance(stmt, SetStatement)
    assert stmt.token_literal() == "int"
    assert isinstance(stmt.name, Identifier)
    assert stmt.name.value == "x"
    assert isinstance(stmt.value, Integer)
    assert stmt.value.token_literal() == "1"


def test_string_literal_expression() -> None:
    tests: list[tuple[str, str]] = [
        ('"Hello, World!";', '"Hello, World!"'),  # Double quotes
        ("'Hello, World!';", "'Hello, World!'"),  # Single quotes
    ]
    for source, expected_value in tests:
        lexer: Lexer = Lexer(source)
        parser: Parser = Parser(lexer)

        program: Program = parser.parse_program()

        expression_statement: ExpressionStatement = cast(ExpressionStatement, program.statements[0])
        string_literal: StringLiteral = cast(StringLiteral, expression_statement.expression)

        assert string_literal is not None
        assert string_literal.value == expected_value


def test_variable_expression() -> None:
    # TODO: Do not allow referencing variables that have not been declared (at parse time)
    source = "foobar;"
    lexer = Lexer(source)
    parser = Parser(lexer)

    program = parser.parse_program()

    _test_program_statements(parser, program)

    expression_statement = cast(ExpressionStatement, program.statements[0])
    assert expression_statement.expression is not None
    _test_literal_expression(expression_statement.expression, "foobar")


def _test_program_statements(parser: Parser, program: Program, expected_statements_count: int = 1) -> None:
    assert program is not None
    assert len(parser.errors) == 0
    assert len(program.statements) == expected_statements_count
    for stmt in program.statements:
        assert isinstance(stmt, ExpressionStatement)


def _test_boolean(expression: Expression, expected_value: bool) -> None:
    assert expression is not None
    assert isinstance(expression, Boolean)

    identifier = cast(Boolean, expression)
    assert identifier.value == expected_value
    assert identifier.token_literal() == str(expected_value)


def _test_constant(expression: Expression, expected_value: str) -> None:
    assert expression is not None
    assert isinstance(expression, Constant)

    identifier = cast(Constant, expression)
    assert identifier.value == expected_value
    assert identifier.token_literal() == expected_value


def _test_float(expression: Expression, expected_value: float) -> None:
    assert expression is not None
    assert isinstance(expression, Float)

    identifier = cast(Float, expression)
    assert identifier.value == expected_value
    assert identifier.token.literal == str(expected_value)


def _test_identifier(expression: Expression, expected_value: str) -> None:
    assert expression is not None
    assert isinstance(expression, Identifier)

    identifier = cast(Identifier, expression)
    assert identifier.value == expected_value
    assert identifier.token_literal() == expected_value


def _test_infix_expression(expression: Expression, expected_left: Any, expected_operator: str, expected_right: Any) -> None:
    assert expression is not None
    assert isinstance(expression, Infix)

    infix = cast(Infix, expression)

    assert infix.left is not None
    _test_literal_expression(infix.left, expected_left)
    assert infix.operator == expected_operator
    assert infix.right is not None
    _test_literal_expression(infix.right, expected_right)


def _test_integer(expression: Expression, expected_value: int) -> None:
    assert expression is not None
    assert isinstance(expression, Integer)

    identifier = cast(Integer, expression)
    assert identifier.value == expected_value
    assert identifier.token.literal == str(expected_value)


def _test_literal_expression(expression: Expression, expected_value: Any) -> None:
    value_type: Type = type(expected_value)
    if value_type == str:
        if expression.token_literal().upper() == expression.token_literal():
            _test_constant(expression, expected_value)
        elif expression.token_literal().lower() == expression.token_literal():
            _test_variable(expression, expected_value)
        else:
            _test_identifier(expression, expected_value)
    elif value_type == int:
        _test_integer(expression, expected_value)
    elif value_type == float:
        _test_float(expression, expected_value)
    elif value_type == bool:
        _test_boolean(expression, expected_value)
    else:
        pytest.fail(f"Type of expression not handled. Got={type(expected_value)}")


def _test_variable(expression: Expression, expected_value: str) -> None:
    assert expression is not None
    assert isinstance(expression, Variable)

    identifier = cast(Variable, expression)
    assert identifier.value == expected_value
    assert identifier.token_literal() == expected_value
