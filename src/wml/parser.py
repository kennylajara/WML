from enum import IntEnum
from typing import Optional, Callable

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
    Statement,
    SetStatement,
    Variable, StringLiteral,
)
from wml.errors import SyntaxError, Error, ParseError
from wml.lexer import Lexer
from wml.token import Token, TokenType


# Type aliases for parsing functions
PrefixParseFn = Callable[[], Optional[Expression]]
InfixParseFn = Callable[[Expression], Optional[Expression]]
PrefixParseFns = dict[TokenType, PrefixParseFn]
InfixParseFns = dict[TokenType, InfixParseFn]


# Precedence levels for operator precedence parsing
class Precedence(IntEnum):
    LOWEST = 1
    EQUALS = 2
    LESSGREATER = 3
    SUM = 4
    PRODUCT = 5
    PREFIX = 6
    CALL = 7


PRECEDENCES: dict[TokenType, Precedence] = {
    TokenType.DIVISION: Precedence.PRODUCT,
    TokenType.EQUAL: Precedence.EQUALS,
    TokenType.GREATER_THAN: Precedence.LESSGREATER,
    TokenType.GREATER_THAN_EQUAL: Precedence.LESSGREATER,
    TokenType.LESS_THAN: Precedence.LESSGREATER,
    TokenType.LESS_THAN_EQUAL: Precedence.LESSGREATER,
    TokenType.LPAREN: Precedence.CALL,
    TokenType.MINUS: Precedence.SUM,
    TokenType.MULTIPLICATION: Precedence.PRODUCT,
    TokenType.NOT_EQUAL: Precedence.EQUALS,
    TokenType.PLUS: Precedence.SUM,
}


class Parser:
    def __init__(self, lexer: Lexer) -> None:
        self._lexer = lexer
        self._current_token: Optional[Token] = None
        self._peek_token: Optional[Token] = None
        self._errors: list[Error] = []

        self._prefix_parse_fns: PrefixParseFns = self._register_prefix_parse_fns()
        self._infix_parse_fns: InfixParseFns = self._register_infix_parse_fns()
        self._advance_tokens()
        self._advance_tokens()

    def parse_program(self) -> Program:
        program: Program = Program(statements=[])

        assert self._current_token is not None
        while self._current_token.token_type != TokenType.EOF:
            statement = self._parse_statement()
            if statement is not None:
                program.statements.append(statement)

            self._advance_tokens()

        return program

    @property
    def errors(self) -> list[str]:
        return [str(error) for error in self._errors]

    def _advance_tokens(self) -> None:
        self._current_token = self._peek_token
        self._peek_token = self._lexer.next_token()

    def _current_precedence(self) -> Precedence:
        assert self._current_token is not None
        try:
            return PRECEDENCES[self._current_token.token_type]
        except KeyError:
            return Precedence.LOWEST

    def _expected_token(self, token_type: TokenType) -> bool:
        assert self._peek_token is not None
        if self._peek_token.token_type == token_type:
            self._advance_tokens()
            return True

        self._expected_token_errors(token_type)
        return False

    def _expected_token_errors(self, token_type: TokenType) -> None:
        assert self._peek_token is not None
        error = SyntaxError(
            message=f"Expected next token to be {token_type}, got {self._peek_token.token_type} instead",
            line=self._peek_token.line,
            column=self._peek_token.column - len(self._peek_token.literal) - 1,
        )
        self._errors.append(error)


    def _parse_action(self) -> Optional[Action]:
        assert self._current_token is not None
        action = Action(token=self._current_token)

        if not self._expected_token(TokenType.LPAREN):
            return None

        action.parameters = self._parse_action_parameters()

        if not self._expected_token(TokenType.LBRACE):
            return None

        action.body = self._parse_block()

        return action

    def _parse_action_parameters(self) -> list[Identifier]:
        # TODO: Don't repeat yourself (parameter after comma)
        params: list[Identifier] = []

        assert self._peek_token is not None
        if self._peek_token.token_type == TokenType.RPAREN:
            self._advance_tokens()

            return params

        self._advance_tokens()

        assert self._current_token is not None

        # Optional typing
        if self._current_token.token_type in [
            TokenType.BOOL_TYPE,
            TokenType.FLOAT_TYPE,
            TokenType.INT_TYPE,
            TokenType.STR_TYPE,
        ]:
            typing = self._current_token
            self._advance_tokens()
        else:
            typing = Token(
                token_type=TokenType.ANY_TYPE,
                literal="Any",
            )

        assert self._current_token is not None
        identifier = Identifier(
            token=self._current_token,
            typing=typing,
            value=self._current_token.literal,
        )
        params.append(identifier)

        while self._peek_token.token_type == TokenType.COMMA:
            self._advance_tokens()
            self._advance_tokens()

            # Optional typing
            if self._current_token.token_type in [
                TokenType.BOOL_TYPE,
                TokenType.FLOAT_TYPE,
                TokenType.INT_TYPE,
                TokenType.STR_TYPE,
            ]:
                typing = self._current_token
                self._advance_tokens()
            else:
                typing = Token(
                    token_type=TokenType.ANY_TYPE,
                    literal="Any",
                )

            identifier = Identifier(
                token=self._current_token,
                typing=typing,
                value=self._current_token.literal,
            )
            params.append(identifier)

        if not self._expected_token(TokenType.RPAREN):
            return []

        return params

    def _parse_block(self) -> Block:
        assert self._current_token is not None
        block = Block(token=self._current_token, statements=[])

        self._advance_tokens()

        while not self._current_token.token_type == TokenType.RBRACE and self._current_token.token_type != TokenType.EOF:
            statement = self._parse_statement()
            if statement is not None:
                assert isinstance(statement, (Statement, ExpressionStatement))
                if not isinstance(statement, ExpressionStatement) or statement.expression is not None:
                    block.statements.append(statement)
            self._advance_tokens()

        return block

    def _parse_boolean(self) -> Optional[Boolean]:
        assert self._current_token is not None
        bln = Boolean(token=self._current_token, value=True if self._current_token.literal == "True" else False)
        return bln

    def _parse_expression(self, precedence: Precedence) -> Optional[Expression]:
        assert self._current_token is not None

        if self._current_token.token_type in [TokenType.EOF, TokenType.SEMICOLON]:
            return None

        try:
            prefix_parse_fn = self._prefix_parse_fns[self._current_token.token_type]
        except KeyError:
            message = f"No prefix parse function found for to parse `{self._current_token.literal}`"
            self._errors.append(ParseError(
                message=message,
                line=self._current_token.line,
                column=self._current_token.column - len(self._current_token.literal),
            ))
            return None

        left_expression = prefix_parse_fn()

        assert self._peek_token is not None
        while not self._peek_token.token_type == TokenType.SEMICOLON and precedence < self._peek_precedence():
            try:
                infix_parse_fn = self._infix_parse_fns[self._peek_token.token_type]

                self._advance_tokens()

                assert left_expression is not None
                left_expression = infix_parse_fn(left_expression)
            except KeyError:
                return left_expression

        return left_expression

    def _parse_expression_statement(self) -> Optional[ExpressionStatement]:
        assert self._current_token is not None
        expression_statement = ExpressionStatement(token=self._current_token)

        expression_statement.expression = self._parse_expression(Precedence.LOWEST)

        assert self._peek_token is not None
        if self._peek_token.token_type == TokenType.SEMICOLON:
            self._advance_tokens()

        return expression_statement

    def _parse_call(self, function: Expression) -> Call:
        assert self._current_token is not None
        call = Call(self._current_token, function)
        call.arguments = self._parse_call_arguments()

        return call

    def _parse_call_arguments(self) -> Optional[list[Expression]]:
        arguments: list[Expression] = []

        assert self._peek_token is not None
        if self._peek_token.token_type == TokenType.RPAREN:
            self._advance_tokens()

            return arguments

        self._advance_tokens()
        if expression := self._parse_expression(Precedence.LOWEST):
            arguments.append(expression)

        while self._peek_token.token_type == TokenType.COMMA:
            self._advance_tokens()
            self._advance_tokens()

            if expression := self._parse_expression(Precedence.LOWEST):
                arguments.append(expression)

        if not self._expected_token(TokenType.RPAREN):
            return None

        return arguments

    def _parse_constant(self, typing: Token | None = None) -> Optional[Constant]:
        assert self._current_token is not None
        if typing is None:
            typing = Token(TokenType.ANY_TYPE, "Any")
        return Constant(
            token=self._current_token,
            typing=typing,
            value=self._current_token.literal,
        )

    def _parse_grouped_expression(self) -> Optional[Expression]:
        self._advance_tokens()

        expression = self._parse_expression(Precedence.LOWEST)

        if not self._expected_token(TokenType.RPAREN):
            return None

        return expression

    def _parse_identifier(self, typing: Token | None = None) -> Optional[Identifier]:
        assert self._current_token is not None
        if typing is None:
            typing = Token(TokenType.ANY_TYPE, "Any")
        return Identifier(
            token=self._current_token,
            typing=typing,
            value=self._current_token.literal,
        )

    def _parse_if(self) -> Optional[If]:
        assert self._current_token is not None
        if_expression = If(token=self._current_token)

        if not self._expected_token(TokenType.LPAREN):
            return None

        self._advance_tokens()

        if_expression.condition = self._parse_expression(Precedence.LOWEST)

        if not self._expected_token(TokenType.RPAREN):
            return None

        if not self._expected_token(TokenType.LBRACE):
            return None

        if_expression.consequence = self._parse_block()

        assert self._peek_token is not None
        if self._peek_token.token_type == TokenType.ELSE:
            self._advance_tokens()

            if not self._expected_token(TokenType.LBRACE):
                return None

            if_expression.alternative = self._parse_block()

        return if_expression

    def _parse_infix_expression(self, left: Expression) -> Infix:
        assert self._current_token is not None
        infix = Infix(token=self._current_token, operator=self._current_token.literal, left=left)

        precedence = self._current_precedence()

        self._advance_tokens()

        infix.right = self._parse_expression(precedence)

        return infix

    def _parse_float(self) -> Optional[Float]:
        assert self._current_token is not None
        flt = Float(token=self._current_token)

        try:
            flt.value = float(self._current_token.literal)
        except ValueError:
            message = f"Imposible to parse {self._current_token.literal} as float"
            error = ParseError(
                message=message,
                line=self._current_token.line,
                column=self._current_token.column - len(self._current_token.literal),
            )
            self._errors.append(error)
            return None

        return flt
    def _parse_integer(self) -> Optional[Integer]:
        assert self._current_token is not None
        integer = Integer(token=self._current_token)

        try:
            integer.value = int(self._current_token.literal)
        except ValueError:
            message = f"Imposible to parse {self._current_token.literal} as integer"
            error = ParseError(
                message=message,
                line=self._current_token.line,
                column=self._current_token.column - len(self._current_token.literal),
            )
            self._errors.append(error)
            return None

        return integer

    def _parse_model_statement(self) -> Optional[ModelStatement]:
        assert self._current_token is not None
        class_statement = ModelStatement(token=self._current_token)
        typing = self._current_token

        if not self._expected_token(TokenType.IDENTIFIER):
            return None

        class_statement.name = Identifier(token=self._current_token, value=self._current_token.literal, typing=typing)

        # Optional inheritance
        if self._peek_token.token_type == TokenType.LPAREN:
            self._advance_tokens()

            if not self._expected_token(TokenType.IDENTIFIER):
                return None

            class_statement.parent = Identifier(token=self._current_token, value=self._current_token.literal, typing=typing)

            if not self._expected_token(TokenType.RPAREN):
                return None

        if not self._expected_token(TokenType.LBRACE):
            return None

        class_statement.body = self._parse_block()

        # If the next token is a semicolon, we consume it
        assert self._peek_token is not None
        if self._peek_token.token_type == TokenType.SEMICOLON:
            self._advance_tokens()

        return class_statement

    def _peek_precedence(self) -> Precedence:
        assert self._peek_token is not None
        try:
            return PRECEDENCES[self._peek_token.token_type]
        except KeyError:
            return Precedence.LOWEST

    def _parse_prefix_expression(self) -> Prefix:
        assert self._current_token is not None
        prefix = Prefix(token=self._current_token, operator=self._current_token.literal)

        self._advance_tokens()

        prefix.right = self._parse_expression(Precedence.PREFIX)

        return prefix

    def _parse_return_statement(self) -> Optional[ReturnStatement]:
        assert self._current_token is not None
        return_statement = ReturnStatement(token=self._current_token)

        self._advance_tokens()

        return_statement.value = self._parse_expression(Precedence.LOWEST)

        assert self._peek_token is not None
        if self._peek_token.token_type == TokenType.SEMICOLON:
            self._advance_tokens()

        return return_statement

    def _parse_set_statement(self) -> Optional[SetStatement]:
        assert self._current_token is not None
        set_statement = SetStatement(token=self._current_token)

        if not self._expected_token(TokenType.VARIABLE):
            return None

        set_statement.name = self._parse_identifier(set_statement.token)

        if not self._expected_token(TokenType.ASSIGN):
            return None

        self._advance_tokens()

        set_statement.value = self._parse_expression(Precedence.LOWEST)

        assert self._peek_token is not None
        if self._peek_token.token_type == TokenType.SEMICOLON:
            self._advance_tokens()

        return set_statement

    def _parse_statement(self) -> Optional[Statement]:
        if self._current_token.token_type in [
            TokenType.BOOL_TYPE,
            TokenType.FLOAT_TYPE,
            TokenType.INT_TYPE,
            TokenType.STR_TYPE,
        ]:
            return self._parse_set_statement()
        if self._current_token.token_type == TokenType.RETURN:
            return self._parse_return_statement()
        if self._current_token.token_type == TokenType.MODEL:
            return self._parse_model_statement()
        return self._parse_expression_statement()

    def _parse_string_literal(self) -> Optional[Expression]:
        assert self._current_token is not None
        return StringLiteral(token=self._current_token, value=self._current_token.literal)

    def _parse_variable(self, typing: Token | None = None) -> Optional[Variable]:
        assert self._current_token is not None
        if typing is None:
            typing = Token(TokenType.ANY_TYPE, "Any")
        return Variable(
            token=self._current_token,
            typing=typing,
            value=self._current_token.literal,
        )


    def _register_infix_parse_fns(self) -> InfixParseFns:
        return {
            TokenType.DIVISION: self._parse_infix_expression,
            TokenType.EQUAL: self._parse_infix_expression,
            TokenType.GREATER_THAN: self._parse_infix_expression,
            TokenType.GREATER_THAN_EQUAL: self._parse_infix_expression,
            TokenType.LESS_THAN: self._parse_infix_expression,
            TokenType.LESS_THAN_EQUAL: self._parse_infix_expression,
            TokenType.LPAREN: self._parse_call,
            TokenType.MINUS: self._parse_infix_expression,
            TokenType.MULTIPLICATION: self._parse_infix_expression,
            TokenType.NOT_EQUAL: self._parse_infix_expression,
            TokenType.PLUS: self._parse_infix_expression,
        }

    def _register_prefix_parse_fns(self) -> PrefixParseFns:
        return {
            TokenType.ACTION: self._parse_action,
            TokenType.BOOL_VALUE: self._parse_boolean,
            TokenType.CONSTANT: self._parse_constant,
            TokenType.FLOAT_VALUE: self._parse_float,
            TokenType.IDENTIFIER: self._parse_identifier,
            TokenType.IF: self._parse_if,
            TokenType.INT_VALUE: self._parse_integer,
            TokenType.LPAREN: self._parse_grouped_expression,
            TokenType.MINUS: self._parse_prefix_expression,
            TokenType.NOT: self._parse_prefix_expression,
            TokenType.STR_VALUE: self._parse_string_literal,
            TokenType.VARIABLE: self._parse_variable,
        }
