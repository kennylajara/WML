from typing import cast

from wml import object as obj
from wml.errors import InvalidNumberOfArguments, UnsupportedArgumentType, Error
from wml.token import TokenType, Token


def length(*args: obj.Type) -> obj.Integer | Error:
    if len(args) != 1:
        return InvalidNumberOfArguments(1, len(args), 0,0)
    elif type(args[0]) == obj.String:
        argument = cast(obj.String, args[0])
        value = len(argument.value[1:-1])
        token = Token(TokenType.INT_VALUE, str(value), 0, 0)
        return obj.Integer(value, token)
    else:
        return UnsupportedArgumentType(obj.String.type(), args[0].type(), 0,0)


BUILTINS: dict[str, obj.BuiltIn] = {
    'length': obj.BuiltIn(function=length),
}
