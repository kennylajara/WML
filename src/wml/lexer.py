from re import match, escape

from wml.utils.regex import REGEX_ALPHANUM, REGEX_DIGIT
from wml.token import Token, TokenType, lookup_token_type


class Lexer:

    def __init__(self, source: str) -> None:
        self._source: str = source
        self._character: str = ""
        self._position: int = 0
        self._read_position: int = 0  # next character to read
        self._current_line: int = 1
        self._current_column: int = 1

        self._read_character()

    def next_token(self):
        # TODO: Refactor to improve readability.
        #  Note that skip_read_character is a workaround and can be simplified by
        #  skipping the character if the token is exists.
        self._skip_whitespace()
        skip_read_character = False

        token = self._find_one_character_token()
        if token:
            if self._character in ["'", '"']:
                token = Token(TokenType.STR_VALUE, self._read_string(), self._current_line, self._current_column)
                skip_read_character = True
            else:
                token = self._find_two_character_token(token)
        else:
            token = self._find_digit_token()
            if token:
                skip_read_character = True
            else:
                literal = self._find_alphanumeric_token()
                if literal:
                    token_type = lookup_token_type(literal)
                    token = Token(token_type, literal, self._current_line, self._current_column)
                    skip_read_character = True
            if not token:
                token = Token(TokenType.ILLEGAL, self._character, self._current_line, self._current_column)
                skip_read_character = False

        if not skip_read_character:
            self._read_character()
        return token

    def _skip_whitespace(self) -> None:
        while match(r'^\s$', self._character):
            self._read_character()

    def _find_alphanumeric_token(self) -> str:
        start = self._position
        while match(REGEX_ALPHANUM, self._character):
            self._read_character()

        return self._source[start:self._position]

    def _find_digit_token(self) -> Token | None:
        if match(REGEX_DIGIT, self._character):
            literal = self._read_digit()
            if literal:
                if "." not in literal:
                    return Token(TokenType.INT_VALUE, literal, self._current_line, self._current_column)
                if literal.count(".") == 1:
                    return Token(TokenType.FLOAT_VALUE, literal, self._current_line, self._current_column)
                return Token(TokenType.ILLEGAL, literal, self._current_line, self._current_column)
        return None

    def _read_digit(self) -> str:
        start = self._position
        while match(REGEX_DIGIT, self._character):  # If off by one error, use _peek_character() and return position + 1
            self._read_character()

        return self._source[start:self._position]

    def _read_string(self) -> str:
        string_wrapper = self._character
        initial_position = self._position

        self._read_character()
        while self._character != string_wrapper and self._read_position < len(self._source):
            self._read_character()
        self._read_character()

        return self._source[initial_position:self._position]

    def _peek_character(self) -> str:
        if self._read_position >= len(self._source):
            return ""
        return self._source[self._read_position]

    def _find_one_character_token(self) -> Token | None:
        one_character_tokens = {
            "=": TokenType.ASSIGN,
            ":": TokenType.COLON,
            ",": TokenType.COMMA,
            "/": TokenType.DIVISION,
            ".": TokenType.DOT,
            ">": TokenType.GREATER_THAN,
            "{": TokenType.LBRACE,
            "<": TokenType.LESS_THAN,
            "(": TokenType.LPAREN,
            "-": TokenType.MINUS,
            "%": TokenType.MODULUS,
            "*": TokenType.MULTIPLICATION,
            "!": TokenType.NOT,
            "+": TokenType.PLUS,
            "}": TokenType.RBRACE,
            ")": TokenType.RPAREN,
            ";": TokenType.SEMICOLON,
            "'": TokenType.STR_TYPE,
            '"': TokenType.STR_TYPE,
            # EOF at end to avoid conflict and improve performance
            "": TokenType.EOF,
        }

        for character, token_type in one_character_tokens.items():
            if match(r'^{}$'.format(escape(character)), self._character):
                return Token(token_type, self._character, self._current_line, self._current_column)

        return None

    def _find_two_character_token(self, token: Token) -> Token:
        two_character_tokens = {
            "==": TokenType.EQUAL,
            "<=": TokenType.LESS_THAN_EQUAL,
            ">=": TokenType.GREATER_THAN_EQUAL,
            "!=": TokenType.NOT_EQUAL,
        }

        for character, token_type in two_character_tokens.items():
            if token.literal == character[0] and self._peek_character() == character[1]:
                prefix = self._character
                self._read_character()
                suffix = self._character
                return Token(token_type, prefix + suffix, self._current_line, self._current_column)

        return token

    def _read_character(self) -> None:
        if self._read_position >= len(self._source):
            self._character = ""
        else:
            self._character = self._source[self._read_position]
            if self._character == "\n":
                self._current_line += 1
                self._current_column = 1
            else:
                self._current_column += 1

        self._position = self._read_position
        self._read_position += 1
