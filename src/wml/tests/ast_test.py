from wml.ast import Program, SetStatement, ReturnStatement, Identifier
from wml.token import Token, TokenType


def test_set_statement() -> None:
    # int foo = bar;
    program = Program(statements=[
        SetStatement(
            token=Token(TokenType.INT_TYPE, "int"),
            name=Identifier(Token(TokenType.IDENTIFIER, "foo"), typing=Token(TokenType.INT_TYPE, "Any"), value="foo"),
            value=Identifier(Token(TokenType.IDENTIFIER, "bar"), typing=Token(TokenType.INT_TYPE, "Any"), value="bar")
        )
    ])

    program_str = str(program)
    assert program_str == "int foo = bar;"


def test_return_statement() -> None:
    # return baz;
    program = Program(statements=[
        ReturnStatement(
            token=Token(TokenType.RETURN, "return"),
            value=Identifier(Token(TokenType.IDENTIFIER, "baz"), typing=Token(TokenType.ANY_TYPE, "Any"), value="baz")
        )
    ])

    program_str = str(program)
    assert program_str == "return baz;"
