from typing import cast, Optional, Type, Union

from wml import ast as ast
from wml import object as obj
from wml.builtings import BUILTINS
from wml.errors import (
    UnknownPrefixOperator,
    UnknownInfixOperator,
    TypeMismatch,
    _TypeError,
    Error,
    InvalidTypeAssignment,
    ConstantReassignmentError,
    ModelReassignmentError,
    NotAnActionError,
)
from wml.token import Token, TokenType

TRUE = obj.Boolean(True)
FALSE = obj.Boolean(False)
NULL = obj.Null()


def evaluate(node: ast.ASTNode, env: obj.Environment) -> Optional[obj.Type]:
    node_type: Type = type(node)

    match node_type:

        case ast.Action:
            node = cast(ast.Action, node)

            assert node.body is not None
            return obj.Action(node.parameters, node.body, env, node.token)

        case ast.Block:
            node = cast(ast.Block, node)

            assert node.statements is not None
            return _evaluate_block_statement(node, env)

        case ast.Boolean:
            node = cast(ast.Boolean, node)
            assert node.value is not None
            return _to_boolean_object(node.value, node.token)

        case ast.Call:
            node = cast(ast.Call, node)

            action = evaluate(node.action, env)

            assert action is not None
            action = cast(obj.Action, action)

            if not isinstance(action, obj.BuiltIn):
                assert action.parameters is not None
            args = _evaluate_expression(node.arguments, env)

            assert action is not None
            return _do_action(action, args)

        case ast.Constant:
            node = cast(ast.Constant, node)

            return _evaluate_constant(node, env)

        case ast.ExpressionStatement:
            node = cast(ast.ExpressionStatement, node)

            assert node.expression is not None
            return evaluate(node.expression, env)

        case ast.Float:
            node = cast(ast.Float, node)
            assert node.value is not None
            return obj.Float(node.value, node.token)

        case ast.Identifier:
            node = cast(ast.Identifier, node)

            return _evaluate_identifier(node, env)

        case ast.If:
            node = cast(ast.If, node)

            return _evaluate_if_expression(node, env)

        case ast.Infix:
            node = cast(ast.Infix, node)

            assert node.left is not None and node.right is not None
            left = evaluate(node.left, env)
            right = evaluate(node.right, env)

            assert left is not None and right is not None
            res = _evaluate_infix_expression(node.operator, left, right)
            return res

        case ast.Integer:
            node = cast(ast.Integer, node)
            assert node.value is not None
            return obj.Integer(node.value, node.token)

        case ast.Prefix:
            node = cast(ast.Prefix, node)

            assert node.right is not None
            right = evaluate(node.right, env)

            assert right is not None
            return _evaluate_prefix_expression(node.operator, right)

        case ast.Program:
            node = cast(ast.Program, node)
            return _evaluate_program(node, env)

        case ast.ReturnStatement:
            node = cast(ast.ReturnStatement, node)

            assert node.value is not None
            value = evaluate(node.value, env)

            assert value is not None
            return obj.Return(value, node.token)

        case ast.SetStatement:
            node = cast(ast.SetStatement, node)

            assert node.value is not None
            value = evaluate(node.value, env)

            assert node.name is not None
            assert value is not None
            _set_environment_value(env, node.name.value, node.token, value)

        case ast.StringLiteral:
            node = cast(ast.StringLiteral, node)

            return obj.String(node.value, node.token)

        case ast.Variable:
            node = cast(ast.Variable, node)

            return _evaluate_variable(node, env)

        case _:
            return None


def _do_action(action: obj.Action, args: list[obj.Type]) -> obj.Type:
    if type(action) == obj.Action:
        action = cast(obj.Action, action)

        extended_env = _extend_action_environment(action, args)
        evaluated = evaluate(action.body, extended_env)

        assert evaluated is not None
        return _unwrap_return_value(evaluated)

    elif type(action) == obj.BuiltIn:
        action = cast(obj.BuiltIn, action)

        return action.function(*args)

    return NotAnActionError(action.type().name, action.token.line, action.token.column - len(action.token.literal))


def _evaluate_block_statement(block: ast.Block, env: obj.Environment) -> Optional[obj.Type]:
    result: Optional[obj.Type] = None
    for statement in block.statements:
        result = evaluate(statement, env)

        if result is not None and (type(result) == obj.Return or isinstance(result, Error)):
            return result

    return result


def _evaluate_constant(node: ast.Constant, env: obj.Environment) -> obj.Type:
    try:
        return BUILTINS.get(node.value, env[node.value])
    except KeyError:
        return _TypeError(node.value, node.token.line, node.token.column - len(node.token.literal))


def _evaluate_expression(expressions: list[ast.Expression], env: obj.Environment) -> list[obj.Type]:
    result: list[obj.Type] = []

    for expression in expressions:
        evaluated = evaluate(expression, env)

        assert evaluated is not None
        result.append(evaluated)

    return result


def _evaluate_identifier(node: ast.Identifier, env: obj.Environment) -> obj.Type:
    try:
        return env[node.value]
    except KeyError:
        return BUILTINS.get(
            node.value,
            _TypeError(node.value, node.token.line, node.token.column - len(node.token.literal))
        )


def _evaluate_if_expression(node: ast.If, env: obj.Environment) -> Optional[obj.Type]:
    assert node.condition is not None
    condition = evaluate(node.condition, env)

    assert condition is not None
    if _is_truthy(condition):
        assert node.consequence is not None
        return evaluate(node.consequence, env)
    elif node.alternative is not None:
        return evaluate(node.alternative, env)

    null = NULL
    null.token = node.token
    return null


def _evaluate_float_infix_expression(operator: str, left: obj.Float, right: obj.Float) -> obj.Type:
    left_value = left.value
    right_value = right.value

    # TODO: Don't repeat yourself
    if operator == "+":
        return obj.Float(left_value + right_value, right.token)
    if operator == "-":
        return obj.Float(left_value - right_value, right.token)
    if operator == "*":
        return obj.Float(left_value * right_value, right.token)
    if operator == "/":
        return obj.Float(left_value / right_value, right.token)
    if operator == "**":
        return obj.Float(left_value ** right_value, right.token)
    if operator == "<":
        return _to_boolean_object(left_value < right_value, right.token)
    if operator == ">":
        return _to_boolean_object(left_value > right_value, right.token)
    if operator == "<=":
        return _to_boolean_object(left_value <= right_value, right.token)
    if operator == ">=":
        return _to_boolean_object(left_value >= right_value, right.token)
    if operator == "==":
        return _to_boolean_object(left_value == right_value, right.token)
    if operator == "!=":
        return _to_boolean_object(left_value != right_value, right.token)

    null = NULL
    null.token = right.token
    return null


def _evaluate_infix_expression(operator: str, left: obj.Type, right: obj.Type) -> obj.Type:
    # If both sides are integers
    if type(left) == obj.Integer and type(right) == obj.Integer:
        left, right = cast(obj.Integer, left), cast(obj.Integer, right)
        if operator != "/":
            return _evaluate_integer_infix_expression(operator, left, right)

        left, right = obj.Float(left.value, left.token), obj.Float(right.value, right.token)
        return _evaluate_float_infix_expression(operator, left, right)

    # If both sides are floats or one side is a float and the other is an integer
    if type(left) == obj.Float or type(left) == obj.Integer and type(right) == obj.Float or type(right) == obj.Integer:
        if type(left) == obj.Integer:
            left = cast(obj.Integer, left)
            left = obj.Float(left.value, left.token)
        if type(right) == obj.Integer:
            right = cast(obj.Integer, right)
            right = obj.Float(right.value, right.token)
        return _evaluate_float_infix_expression(operator, left, right)

    # If both sides are strings
    if type(left) == obj.String and type(right) == obj.String:
        left, right = cast(obj.String, left), cast(obj.String, right)
        return _evaluate_string_infix_expression(operator, left, right)

    if operator == "==":
        return _to_boolean_object(left == right, right.token)  # noqa
    if operator == "!=":
        return _to_boolean_object(left != right, right.token)  # noqa
    # TODO: Implement logical operators
    # if operator == "&&":
    #     return _to_boolean_object(_is_truthy(left) and _is_truthy(right))
    # if operator == "||":
    #     return _to_boolean_object(_is_truthy(left) or _is_truthy(right))

    if left.type() != right.type():
        return TypeMismatch(left.type(), operator, right.type(), right.token.line,  # noqa
                            right.token.column - len(right.token.literal) - 3)  # noqa

    return UnknownInfixOperator(left.type(), operator, right.type(), right.token.line, # noqa
                                right.token.column - len(right.token.literal) - 3)  # noqa


def _evaluate_integer_infix_expression(operator: str, left: obj.Integer, right: obj.Integer) -> obj.Type:
    left_value = left.value
    right_value = right.value

    if operator == "+":
        return obj.Integer(left_value + right_value, right.token)
    if operator == "-":
        return obj.Integer(left_value - right_value, right.token)
    if operator == "*":
        return obj.Integer(left_value * right_value, right.token)
    if operator == "**":
        return obj.Integer(left_value ** right_value, right.token)
    if operator == "/":
        return obj.Float(left_value / right_value, right.token)
    if operator == "//":
        return obj.Integer(left_value // right_value, right.token)
    if operator == "%":
        return _to_boolean_object(left_value % right_value == 0, right.token)
    if operator == "==":
        return _to_boolean_object(left_value == right_value, right.token)
    if operator == "!=":
        return _to_boolean_object(left_value != right_value, right.token)
    if operator == "<":
        return _to_boolean_object(left_value < right_value, right.token)
    if operator == ">":
        return _to_boolean_object(left_value > right_value, right.token)
    if operator == "<=":
        return _to_boolean_object(left_value <= right_value, right.token)
    if operator == ">=":
        return _to_boolean_object(left_value >= right_value, right.token)

    return UnknownInfixOperator(left.type(), operator, right.type(), right.token.line,  # noqa
                                right.token.column - len(right.token.literal) - 1)  # noqa


def _evaluate_minus_prefix_operator_expression(right: obj.Type) -> obj.Type:
    if type(right) == obj.Integer:
        right = cast(obj.Integer, right)
        return obj.Integer(-right.value, right.token)

    if type(right) == obj.Float:
        right = cast(obj.Float, right)
        return obj.Float(-right.value, right.token)

    return UnknownPrefixOperator("-", right.type(), right.token.line,  # noqa
                                 right.token.column - len(right.token.literal) - 1)  # noqa


def _evaluate_prefix_expression(operator: str, right: obj.Type) -> obj.Type:
    if operator == "!":
        return FALSE if _is_truthy(right) else TRUE
    elif operator == "-":
        return _evaluate_minus_prefix_operator_expression(right)
    else:
        # TODO: Add unit tests
        return UnknownPrefixOperator(operator, right.type(), right.token.line,  # noqa
                                     right.token.column - len(right.token.literal) - 1)  # noqa


def _evaluate_program(program: ast.Program, env: obj.Environment) -> Optional[obj.Type]:
    result: Optional[obj.Type] = None
    for statement in program.statements:
        result = evaluate(statement, env)

        if type(result) == obj.Return:
            result = cast(obj.Return, result)
            assert result is not None
            return result.value  # noqa

        if isinstance(result, Error):
            return result

    return result


def _evaluate_variable(node: ast.Variable, env: obj.Environment) -> obj.Type:
    # if node.typing.token_type is not TokenType.ANY_TYPE or node.typing.token_type
    try:
        return env[node.value]
    except KeyError:  # FIXME: This is not being returned to the user, is returning to be processed by the evaluator
        return BUILTINS.get(
            node.value,
            _TypeError(node.value, node.token.line, node.token.column - len(node.token.literal))
        )


def _evaluate_string_infix_expression(operator: str, left: obj.String, right: obj.String) -> obj.Type:

    left_value = _standardize_string(left.value, True)
    right_value = _standardize_string(right.value, True)

    if operator == "+":
        new_content = left_value["value"][1:-1] + right_value["value"][1:-1]
        new_wrapper = "'" if (left_value["has_double_quotes"] or right_value["has_double_quotes"]) and not (left_value["has_simple_quotes"] or right_value["has_simple_quotes"]) else '"'
        new_content = f"{new_wrapper}{new_content}{new_wrapper}"
        return obj.String(new_content, right.token)
    if operator == "==":
        return _to_boolean_object(left_value == right_value, right.token)
    if operator == "!=":
        return _to_boolean_object(left_value != right_value, right.token)

    return UnknownInfixOperator(left.type(), operator, right.type(), right.token.line,  # noqa
                                right.token.column - len(right.token.literal) - 3)  # noqa


def _extend_action_environment(action: obj.Action, args: list[obj.Type]) -> obj.Environment:
    env = obj.Environment(action.env)

    for idx, param in enumerate(action.parameters):
        env[param.value] = args[idx - 1]

    return env


def _is_truthy(evaluated: obj.Type) -> bool:
    if evaluated is NULL:
        return False
    if evaluated is TRUE:
        return True
    if evaluated is FALSE:
        return False
    if type(evaluated) == obj.Integer:
        evaluated = cast(obj.Integer, evaluated)
        return evaluated.value != 0
    if type(evaluated) == obj.Float:
        evaluated = cast(obj.Float, evaluated)
        return evaluated.value != 0.0
    # if type(evaluated) == obj.String:  # TODO: Uncomment when strings are implemented
    #     evaluated = cast(obj.String, evaluated)
    #     return evaluated.value != ""
    return True


def _to_boolean_object(value: bool, token: Token) -> obj.Boolean:
    value = TRUE if value else FALSE
    value.token = token
    return value


def _set_environment_value(env: obj.Environment, key_str: str, key_token: Token, value: obj.Type):

    key_type = key_token.token_type
    value_type = value.token.token_type

    # Always set actions in the environment
    if value_type == TokenType.ACTION:
        env[key_str] = value
        return

    # Validate the types of the key and value (Int, Float, Str and Bool values
    # should only be assigned by a SetStatement of the same type)
    is_valid = _validate_set_statement_types(key_type, value_type)
    if not is_valid:
        return InvalidTypeAssignment(key_type, value_type, key_token.line, key_token.column - len(key_token.literal))

    # Avoid reassigning constants
    if key_type == TokenType.CONSTANT and key_str in env:
        return ConstantReassignmentError(key_token.literal, key_token.line, key_token.column - len(key_token.literal))

    # Avoid reassigning models
    if key_token.token_type == TokenType.IDENTIFIER and key_str in env:
        return ModelReassignmentError(key_token.literal, key_token.line, key_token.column - len(key_token.literal))

    env[key_str] = value


def _validate_set_statement_types(key_type, value_type):
    if key_type == TokenType.ANY_TYPE:
        return True
    if key_type == TokenType.INT_TYPE and value_type == TokenType.INT_VALUE:
        return True
    if key_type == TokenType.FLOAT_TYPE and value_type == TokenType.FLOAT_VALUE:
        return True
    if key_type == TokenType.STR_TYPE and value_type == TokenType.STR_VALUE:
        return True
    if key_type == TokenType.BOOL_TYPE and value_type == TokenType.BOOL_VALUE:
        return True

    return False


def _standardize_string(value: str, additional_info: bool = False) -> str | dict[str, Union[bool, str]]:
    value_wrapper = value[0]
    value_content = _unescape_string(value[1:-1], value_wrapper)
    value_has_simple_quotes = value_content.find("'") != -1
    value_has_double_quotes = value_content.find('"') != -1

    new_wrapper = "'" if value_has_double_quotes and not value_has_simple_quotes else '"'
    mew_value = f"{new_wrapper}{value_content}{new_wrapper}"

    if not additional_info:
        return mew_value
    return {
        "value": mew_value,
        "has_simple_quotes": value_has_simple_quotes,
        "has_double_quotes": value_has_double_quotes,
    }


def _unescape_string(value: str, wrapper: str) -> str:
    return value.replace(f"\\{wrapper}", wrapper)


def _unwrap_return_value(evaluated: obj.Type) -> obj.Type:
    if type(evaluated) == obj.Return:
        evaluated = cast(obj.Return, evaluated)
        return evaluated.value

    return evaluated
