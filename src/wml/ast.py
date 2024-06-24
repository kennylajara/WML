from abc import ABC, abstractmethod
from typing import Optional

from wml.token import Token


class ASTNode(ABC):

    @abstractmethod
    def token_literal(self) -> str:
        pass

    @abstractmethod
    def __str__(self) -> str:
        pass

    def __repr__(self):
        return f"<{self.__class__.__name__} {self.__str__()}>"


class Statement(ASTNode):  # noqa  # Would not be executed directly, don't implement __str__

    def __init__(self, token: Token) -> None:
        self.token = token

    def token_literal(self) -> str:
        return self.token.literal


class Expression(ASTNode):  # noqa  # Would not be executed directly, don't implement __str__

    def __init__(self, token: Token) -> None:
        self.token = token

    def token_literal(self) -> str:
        return self.token.literal


class Block(Statement):
    def __init__(self, token: Token, statements: Optional[list[Statement]] = None) -> None:
        super().__init__(token)
        self.statements = statements

    def __str__(self) -> str:
        return "".join([str(statement) for statement in self.statements])


class ExpressionStatement(Statement):
    def __init__(self, token: Token, expression: Optional[Expression] = None) -> None:
        super().__init__(token)
        self.expression = expression

    def __str__(self) -> str:
        return f'{str(self.expression)};'


class Boolean(Expression):
    def __init__(self, token: Token, value: Optional[bool] = None) -> None:
        super().__init__(token)
        self.value = value

    def __str__(self) -> str:
        return str(self.value)


class Constant(Expression):
    def __init__(self, token: Token, typing: Token, value: str) -> None:
        super().__init__(token)
        self.typing = typing
        self.value = value

    def __str__(self) -> str:
        return self.value


class Identifier(Expression):
    def __init__(self, token: Token, typing: Token, value: str) -> None:
        super().__init__(token)
        self.typing = typing
        self.value = value

    def __str__(self) -> str:
        return self.value


class If(Expression):

    def __init__(
            self,
            token: Token,
            condition: Optional[Expression]=None,
            consequence: Optional[Block]=None,
            alternative: Optional[Block]=None
    ) -> None:
        super().__init__(token)
        self.condition = condition
        self.consequence = consequence
        self.alternative = alternative

    def __str__(self):
        out: str = f'if ({str(self.condition)}) {{ {str(self.consequence)} }}'
        if self.alternative is not None:
            out += f' else {{ {str(self.alternative)} }}'
        return out

class Action(Expression):

    def __init__(self,
                 token: Token,
                 parameters: list[Identifier] = None,
                 body: Optional[Block] = None) -> None:
        super().__init__(token)
        self.parameters = parameters or []
        self.body = body

    def __str__(self) -> str:
        param_list: list[str] = [str(parameter) for parameter in self.parameters]

        params: str = ', '.join(param_list)

        return f'{self.token_literal()}({params}){{ {str(self.body)} }}'

class Variable(Expression):
    def __init__(self, token: Token, typing: Token, value: str) -> None:
        super().__init__(token)
        self.typing = typing
        self.value = value

    def __str__(self) -> str:
        return self.value


class Float(Expression):
    def __init__(self, token: Token, value: Optional[float] = None) -> None:
        super().__init__(token)
        self.value = value

    def __str__(self) -> str:
        return str(self.value)


class Integer(Expression):
    def __init__(self, token: Token, value: Optional[int] = None) -> None:
        super().__init__(token)
        self.value = value

    def __str__(self) -> str:
        return str(self.value)


class Infix(Expression):

    def __init__(self, token: Token, left: Optional[Expression], operator: str, right: Optional[Expression] = None) -> None:
        super().__init__(token)
        self.left = left
        self.operator = operator
        self.right = right

    def __str__(self) -> str:
        return f"({str(self.left)} {self.operator} {str(self.right)})"


class Prefix(Expression):
    def __init__(self, token: Token, operator: str, right: Optional[Expression] = None) -> None:
        super().__init__(token)
        self.operator = operator
        self.right = right

    def __str__(self) -> str:
        return f"({self.operator}{str(self.right)})"


class StringLiteral(Expression):
    def __init__(self, token: Token, value: str = None) -> None:
        super().__init__(token)
        self.value = value

    def __str__(self) -> str:
        return self.value


class Call(Expression):

    def __init__(self,
                 token: Token,
                 action: Expression,
                 arguments: Optional[list[Expression]] = None) -> None:
        super().__init__(token)
        self.action = action
        self.arguments = arguments

    def __str__(self) -> str:
        assert self.arguments is not None
        arg_list: list[str] = [str(argument) for argument in self.arguments]
        args: str = ', '.join(arg_list)

        return f'{str(self.action)}({args})'

class ModelStatement(Statement):
    def __init__(
            self,
            token: Token,
            name: Optional[Identifier] = None,
            parent: Optional[Identifier] = None,
            body: Optional[Block] = None,
    ) -> None:
        super().__init__(token)
        self.name = name
        self.parent = parent
        self.body = body

    def __str__(self) -> str:
        if self.parent is not None:
            return f'{self.token_literal()} {self.name}({self.parent}) {{ {self.body} }};'
        return f'{self.token_literal()} {self.name} {{{self.body}}}'


class SetStatement(Statement):
    # TODO: Allow constant and variable types
    def __init__(self, token: Token, name: Optional[Identifier]=None, value: Optional[Expression]=None) -> None:
        super().__init__(token)
        self.name = name
        self.value = value

    def __str__(self) -> str:
        return f'{self.token_literal()} {self.name} = {self.value};'


class ReturnStatement(Statement):
    def __init__(self, token: Token, value: Optional[Expression]=None) -> None:
        super().__init__(token)
        self.value = value

    def __str__(self) -> str:
        return f'{self.token_literal()} {self.value};'


class Program(ASTNode):
    def __init__(self, statements: list[Statement]) -> None:
        self.statements = statements

    def token_literal(self) -> str:
        if self.statements:
            return self.statements[0].token_literal()
        return ""

    def __str__(self) -> str:
        return "".join([str(statement) for statement in self.statements])

    def beautify(self) -> str:
        code = str(self)

        # Add newlines
        code = code.replace("{", "{\n")
        code = code.replace(";", ";\n")

        # Add indentation
        indentation = 0
        beautified_code = ""
        for line in code.split("\n"):
            if "}" in line:
                indentation -= 1
            beautified_code += "    " * indentation + line.strip() + "\n"
            if line.strip().endswith("};") and indentation == 0:
                beautified_code += "\n"
            if "{" in line:
                indentation += 1

        return beautified_code.strip() + "\n"
