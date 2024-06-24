from wml.ast import Program
from wml.evaluator import evaluate
from wml.lexer import Lexer
from wml.object import Environment
from wml.parser import Parser
from wml.token import Token, TokenType


EOF_TOKEN: Token = Token(TokenType.EOF, "")


def _print_errors(errors: list[str]) -> None:
    for error in errors:
        print(error)


def start_repl() -> None:

    scanned: list[str] = []

    while (source := input(">>> ")) != "exit":
        if source != "pretty":
            scanned.append(source)

        lexer: Lexer = Lexer("\n".join(scanned))
        parser: Parser = Parser(lexer)

        program: Program = parser.parse_program()
        env: Environment = Environment()

        if len(parser.errors) > 0:
            _print_errors(parser.errors)
            if source != "pretty":
                scanned.pop()
            continue

        if source == "pretty":
            print(program.beautify())
            continue

        evaluated = evaluate(program, env)

        if evaluated is not None:
            print(evaluated.inspect())
            scanned = program.beautify().split("\n")


def execute_file(filename: str) -> None:
    with open(filename, "r") as f:
        source = f.read()

    lexer: Lexer = Lexer(source)
    parser: Parser = Parser(lexer)
    program: Program = parser.parse_program()
    env: Environment = Environment()

    if len(parser.errors) > 0:
        _print_errors(parser.errors)
        return

    evaluated = evaluate(program, env)

    if evaluated is not None:
        print(evaluated.inspect())
