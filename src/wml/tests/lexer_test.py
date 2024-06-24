from wml.lexer import Lexer
from wml.token import Token, TokenType


def test_illegal_character() -> None:
    source: str = "¿¡"
    lexer = Lexer(source)

    tokens: list[Token] = []
    for _ in range(len(source)):
        tokens.append(lexer.next_token())

    expected_tokens: list[Token] = [
        Token(TokenType.ILLEGAL, "¿"),
        Token(TokenType.ILLEGAL, "¡"),
    ]

    assert tokens == expected_tokens


def test_one_character_operator() -> None:
    source: str = '=+-*/%.,:;{}()<>'
    lexer: Lexer = Lexer(source)

    tokens: list[Token] = []
    for _ in range(len(source)):
        tokens.append(lexer.next_token())

    expected_tokens: list[Token] = [
        Token(TokenType.ASSIGN, '='),
        Token(TokenType.PLUS, '+'),
        Token(TokenType.MINUS, '-'),
        Token(TokenType.MULTIPLICATION, '*'),
        Token(TokenType.DIVISION, '/'),
        Token(TokenType.MODULUS, '%'),
        Token(TokenType.DOT, '.'),
        Token(TokenType.COMMA, ','),
        Token(TokenType.COLON, ':'),
        Token(TokenType.SEMICOLON, ';'),
        Token(TokenType.LBRACE, '{'),
        Token(TokenType.RBRACE, '}'),
        Token(TokenType.LPAREN, '('),
        Token(TokenType.RPAREN, ')'),
        Token(TokenType.LESS_THAN, '<'),
        Token(TokenType.GREATER_THAN, '>'),
    ]

    assert tokens == expected_tokens


def test_two_character_operator() -> None:
    source: str = '== <= >='
    lexer: Lexer = Lexer(source)

    tokens: list[Token] = []
    for _ in range(len(source.split(" "))):
        tokens.append(lexer.next_token())

    expected_tokens: list[Token] = [
        Token(TokenType.EQUAL, '=='),
        Token(TokenType.LESS_THAN_EQUAL, '<='),
        Token(TokenType.GREATER_THAN_EQUAL, '>='),
    ]

    assert tokens == expected_tokens


def test_eof() -> None:
    source: str = ''
    lexer: Lexer = Lexer(source)

    tokens: list[Token] = []
    for _ in range(len(source) + 1):
        tokens.append(lexer.next_token())

    expected_tokens: list[Token] = [
        Token(TokenType.EOF, ''),
    ]

    assert tokens == expected_tokens


def test_identifiers() -> None:
    source = " ".join([
        "foo bar_baz BAZ FOO_BAR Bar BarFoo barFoo",
        "foo1 bar_baz1 BAZ1 FOO_BAR1 Bar1 BarFoo1 barFoo1",
        "foo1x bar_baz1x BAZ1X FOO_BAR1X Bar1x BarFoo1x barFoo1x",
        "_foo _bar_baz _BAZ _FOO_BAR _Bar _BarFoo _barFoo",
        "Bar_Foo",
    ])
    lexer: Lexer = Lexer(source)

    tokens: list[Token] = []
    for _ in range(len(source.split(" "))):
        tokens.append(lexer.next_token())

    expected_tokens: list[Token] = [
        # Alpha
        Token(TokenType.VARIABLE, 'foo'),
        Token(TokenType.VARIABLE, 'bar_baz'),
        Token(TokenType.CONSTANT, 'BAZ'),
        Token(TokenType.CONSTANT, 'FOO_BAR'),
        Token(TokenType.IDENTIFIER, 'Bar'),
        Token(TokenType.IDENTIFIER, 'BarFoo'),
        Token(TokenType.ILLEGAL, 'barFoo'),
        # AlphaNum (end)
        Token(TokenType.VARIABLE, 'foo1'),
        Token(TokenType.VARIABLE, 'bar_baz1'),
        Token(TokenType.CONSTANT, 'BAZ1'),
        Token(TokenType.CONSTANT, 'FOO_BAR1'),
        Token(TokenType.IDENTIFIER, 'Bar1'),
        Token(TokenType.IDENTIFIER, 'BarFoo1'),
        Token(TokenType.ILLEGAL, 'barFoo1'),
        # AlphaNum (middle)
        Token(TokenType.VARIABLE, 'foo1x'),
        Token(TokenType.VARIABLE, 'bar_baz1x'),
        Token(TokenType.CONSTANT, 'BAZ1X'),
        Token(TokenType.CONSTANT, 'FOO_BAR1X'),
        Token(TokenType.IDENTIFIER, 'Bar1x'),
        Token(TokenType.IDENTIFIER, 'BarFoo1x'),
        Token(TokenType.ILLEGAL, 'barFoo1x'),
        # Underscore (start)
        Token(TokenType.VARIABLE, '_foo'),
        Token(TokenType.VARIABLE, '_bar_baz'),
        Token(TokenType.CONSTANT, '_BAZ'),
        Token(TokenType.CONSTANT, '_FOO_BAR'),
        Token(TokenType.ILLEGAL, '_Bar'),
        Token(TokenType.ILLEGAL, '_BarFoo'),
        Token(TokenType.ILLEGAL, '_barFoo'),
        # Underscore (middle)
        Token(TokenType.ILLEGAL, 'Bar_Foo'),
    ]

    assert tokens == expected_tokens

def test_reserved_keywords() -> None:
    source = "Any bool else False flt if int model None True return str"
    lexer: Lexer = Lexer(source)

    tokens: list[Token] = []
    for i in range(len(source.split(" "))):
        tokens.append(lexer.next_token())

    expected_tokens: list[Token] = [
        Token(TokenType.ANY_TYPE, "Any"),
        Token(TokenType.BOOL_TYPE, "bool"),
        Token(TokenType.ELSE, "else"),
        Token(TokenType.BOOL_VALUE, "False"),
        Token(TokenType.FLOAT_TYPE, "flt"),
        Token(TokenType.IF, "if"),
        Token(TokenType.INT_TYPE, "int"),
        Token(TokenType.MODEL, "model"),
        Token(TokenType.NONE, "None"),
        Token(TokenType.BOOL_VALUE, "True"),
        Token(TokenType.RETURN, "return"),
        Token(TokenType.STR_TYPE, "str"),
    ]

    assert tokens == expected_tokens


def test_numbers() -> None:
    source = "123 321.456 123.456.789 123.456."
    lexer: Lexer = Lexer(source)

    tokens: list[Token] = []
    for i in range(len(source.split(" "))):
        tokens.append(lexer.next_token())

    expected_tokens: list[Token] = [
        Token(TokenType.INT_VALUE, "123"),
        Token(TokenType.FLOAT_VALUE, "321.456"),
        Token(TokenType.ILLEGAL, "123.456.789"),
        Token(TokenType.ILLEGAL, "123.456."),
    ]

    assert tokens == expected_tokens


def test_string() -> None:
    source = '''
        "Hello, World!";
        "World modeled with WML";
        'WML means World Modeling Language';
    '''
    lexer = Lexer(source)

    tokens: list[str] = []
    for _ in range(6):
        tokens.append(lexer.next_token())

    expected_tokens = [
        Token(TokenType.STR_VALUE, '"Hello, World!"'),
        Token(TokenType.SEMICOLON, ";"),
        Token(TokenType.STR_VALUE, '"World modeled with WML"'),
        Token(TokenType.SEMICOLON, ";"),
        Token(TokenType.STR_VALUE, "'WML means World Modeling Language'"),
        Token(TokenType.SEMICOLON, ";"),
    ]

    assert tokens == expected_tokens
