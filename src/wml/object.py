from abc import ABC, abstractmethod
from typing_extensions import Protocol

from wml import ast
from wml.token import Token, TokenType


class TypeName: #TODO: metaclass=Singleton

    def __init__(self, value: str) -> None:
        if value.startswith("_"):
            value = value[1:]
        self.value = value

    def __eq__(self, other: object) -> bool:
        return isinstance(other, TypeName) and self.value == other.value

    def __ne__(self, other: object) -> bool:
        return not self.__eq__(other)

    def __hash__(self) -> int:
        return hash(self.value)

    def __str__(self) -> str:
        return self.value

    def __repr__(self) -> str:
        return self.value


### Base classes ###


class Type(ABC):

    @classmethod
    def type(cls) -> TypeName:
        return TypeName(cls.__name__)

    @abstractmethod
    def inspect(self) -> str:
        pass


class BuiltInFunction(Protocol):

    def __call__(self, *args: Type) -> Type:
        ...


class BuiltIn(Type):

    def __init__(self, function: BuiltInFunction) -> None:
        self.function = function
        pass

    def inspect(self) -> str:
        return 'Built-in function'


class DataType(Type, ABC):
    pass


class ReservedWord(Type, ABC):
    pass


### Environment ###


class Environment(Type):

    # TODO: Do we need to pass a dict?
    #  Maybe we can just initialize an empty dict in the constructor every time
    def __init__(self, outer: dict | None = None) -> None:
        if outer is None:
            outer = {}
        self._store = dict()
        self._outer = outer
        super().__init__()

    def __getitem__(self, key: str) -> object:
        try:
            return self._store[key]
        except KeyError as err:
            if self._outer is not None:
                return self._outer[key]
            raise err

    def __setitem__(self, key: str, value: object) -> None:
        self._store[key] = value

    def __contains__(self, key: str) -> bool:
        return key in self._store

    def __delitem__(self, key: str) -> None:
        if key in self._store:
            del self._store[key]

    def __iter__(self):
        return iter(self._store)

    def __len__(self) -> int:
        return len(self._store)

    def __str__(self) -> str:
        return str(self._store)

    def __repr__(self) -> str:
        return str(self._store)

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Environment) and self._store == other._store

    def __ne__(self, other: object) -> bool:
        return not self.__eq__(other)

    def __hash__(self) -> int:
        return hash(self._store)

    def __bool__(self) -> bool:
        return bool(self._store)

    def __add__(self, other: object) -> object:
        if isinstance(other, Environment):
            return Environment({**self._store, **other._store})
        return NotImplemented

    def __sub__(self, other: object) -> object:
        if isinstance(other, Environment):
            return Environment({key: value for key, value in self._store.items() if key not in other._store})
        return NotImplemented

    def keys(self) -> list[str]:
        return list(self._store.keys())

    def values(self) -> list[object]:
        return list(self._store.values())

    def items(self) -> list[tuple[str, object]]:
        return list(self._store.items())

    def inspect(self) -> str:
        return str(self._store)


### Data types ###


class Boolean(DataType):

    def __init__(self, value: bool, token: Token | None = None) -> None:
        self.value = value
        self.token = token

    def inspect(self) -> str:
        return "True" if self.value else "False"


class Float(DataType):

    def __init__(self, value: float, token: Token) -> None:
        if token.token_type == TokenType.INT_VALUE:
            value = float(value)
            token = Token(TokenType.FLOAT_VALUE, str(value), token.line, token.column)
        self.value = value
        self.token = token

    def inspect(self) -> str:
        return str(self.value)


class Integer(DataType):

    def __init__(self, value: int, token: Token) -> None:
        self.value = value
        self.token = token

    def inspect(self) -> str:
        return str(self.value)


class Null(DataType):

    def __init__(self, token: Token | None = None) -> None:
        self.token = token

    def inspect(self) -> str:
        return "Null"


class String(DataType):

    def __init__(self, value: str, token: Token) -> None:
        self.value = value
        self.token = token

    def inspect(self) -> str:
        return self.value


### Reserved words ###


class Action(ReservedWord):

    def __init__(
            self,
            parameters: list[ast.Identifier],
            body: ast.Block,
            env: Environment,
            token: Token,
    ) -> None:
        self.parameters = parameters
        self.body = body
        self.env = env
        self.token = token

    def inspect(self) -> str:
        params = [str(param) for param in self.parameters]
        return f"action({', '.join(params)}) {{ {str(self.body)} }};"


class Return(ReservedWord):

    def __init__(self, value: Type, token: Token) -> None:
        self.value = value
        self.token = token

    def inspect(self) -> str:
        return self.value.inspect()
