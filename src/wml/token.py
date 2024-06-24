from enum import (
    auto,
    unique,
    StrEnum,
)
from re import match
from typing import NamedTuple

from wml.utils.regex import REGEX_ALPHANUM, REGEX_NUM


@unique
class TokenType(StrEnum):
    ACTION = auto()
    ANY_TYPE = auto()
    ASSIGN = auto()
    BOOL_TYPE = auto()
    BOOL_VALUE = auto()
    COLON = auto()
    DOT = auto()
    ELSE = auto()
    EQUAL = auto()
    COMMA = auto()
    CONSTANT = auto()
    EOF = auto()
    FLOAT_TYPE = auto()
    FLOAT_VALUE = auto()
    GREATER_THAN = auto()
    GREATER_THAN_EQUAL = auto()
    IDENTIFIER = auto()
    IF = auto()
    ILLEGAL = auto()
    INT_TYPE = auto()
    INT_VALUE = auto()
    IS = auto()
    LBRACE = auto()
    LESS_THAN = auto()
    LESS_THAN_EQUAL = auto()
    LPAREN = auto()
    MINUS = auto()
    MODEL = auto()
    MODULUS = auto()
    MULTIPLICATION = auto()
    NONE = auto()
    NOT = auto()
    NOT_EQUAL = auto()
    PLUS = auto()
    RBRACE = auto()
    RETURN = auto()
    RPAREN = auto()
    SEMICOLON = auto()
    DIVISION = auto()
    STR_TYPE = auto()
    STR_VALUE = auto()
    VARIABLE = auto()


class Token(NamedTuple):
    token_type: TokenType
    literal: str
    line: int | None = None
    column: int | None = None

    def __str__(self):
        return f'Type: {self.token_type}, Literal: {self.literal}'

    def __eq__(self, other: "Token") -> bool:
        if not isinstance(other, Token):
            return False
        return self.token_type == other.token_type and self.literal == other.literal


def lookup_token_type(literal: str) -> TokenType:
    keywords = {
        "action": TokenType.ACTION,
        "Any": TokenType.ANY_TYPE,
        "bool": TokenType.BOOL_TYPE,
        "else": TokenType.ELSE,
        "False": TokenType.BOOL_VALUE,
        "flt": TokenType.FLOAT_TYPE,
        "if": TokenType.IF,
        "int": TokenType.INT_TYPE,
        "is": TokenType.IS,
        "model": TokenType.MODEL,
        "None": TokenType.NONE,
        "True": TokenType.BOOL_VALUE,
        "return": TokenType.RETURN,
        "str": TokenType.STR_TYPE,
    }

    token_type = keywords.get(literal, None)
    if token_type:
        return token_type

    if match(REGEX_NUM, literal):
        return TokenType.INT_VALUE

    if match(REGEX_ALPHANUM, literal):
        if literal.lower() == literal:
            return TokenType.VARIABLE
        if literal.upper() == literal:
            return TokenType.CONSTANT
        if "_" in literal:
            return TokenType.ILLEGAL
        if literal[0].isupper():
            return TokenType.IDENTIFIER

    return TokenType.ILLEGAL


def map_token_type(token_type: TokenType) -> TokenType:
    _map = {
        TokenType.BOOL_TYPE: TokenType.BOOL_VALUE,
        TokenType.FLOAT_TYPE: TokenType.FLOAT_VALUE,
        TokenType.INT_TYPE: TokenType.INT_VALUE,
        TokenType.STR_TYPE: TokenType.STR_VALUE,
    }

    return _map.get(token_type, TokenType.ILLEGAL)
