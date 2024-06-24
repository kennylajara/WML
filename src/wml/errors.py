from abc import ABC, abstractmethod

from wml.object import Type, TypeName


class Error(Type, ABC):
    """Base class for exceptions in this module."""

    @abstractmethod
    def __init__(self) -> None:
        pass

    def __str__(self) -> str:
        raise NotImplementedError("Subclasses must implement this method")

    def type(self) -> TypeName:
        return super().type()


    def inspect(self) -> str:
        return self.__str__()


class ParseError(Error):
    """Exception raised for errors in the input.

    Attributes:
        message -- explanation of the error
        line -- line number where the error occurred
        column -- column number where the error occurred
    """

    def __init__(self, message: str, line: int, column: int) -> None:  # TODO: Do not pass the message as an argument
        self.message = message
        self.line = line
        self.column = column
        super().__init__()

    def __str__(self) -> str:
        return f"ParseError: {self.message} at line {self.line}, column {self.column}"


class SyntaxError(Error):
    """Exception raised for errors in the input.

    Attributes:
        message -- explanation of the error
        line -- line number where the error occurred
        column -- column number where the error occurred
    """

    def __init__(self, message: str, line: int, column: int) -> None:
        self.message = message
        self.line = line
        self.column = column
        super().__init__()

    def __str__(self) -> str:
        return f"SyntaxError: {self.message} at line {self.line}, column {self.column}"


class TypeMismatch(Error):  # TODO: Replace by TypeError
    """Exception raised for errors in the input.

    Attributes:
        message -- explanation of the error
        line -- line number where the error occurred
        column -- column number where the error occurred
    """

    def __init__(self, left: Type, operator: str, right: Type, line: int, column: int) -> None:
        self.message = f"{self.type()}: {left} {operator} {right} on line {line}, column {column}"
        self.line = line
        self.column = column

    def __str__(self) -> str:
        return self.message


class UnknownPrefixOperator(Error):  # TODO: Replace by TypeError
    """Exception raised for errors in the input.

    Attributes:
        message -- explanation of the error
        line -- line number where the error occurred
        column -- column number where the error occurred
    """

    def __init__(self, operator: str, right: Type, line: int, column: int) -> None:
        self.message = f"{self.type()}: {operator}{right} on line {line}, column {column}"
        self.line = line
        self.column = column
        super().__init__()

    def __str__(self) -> str:
        return self.message


class UnknownInfixOperator(Error):  # TODO: Replace by TypeError
    """Exception raised for errors in the input.

    Attributes:
        message -- explanation of the error
        line -- line number where the error occurred
        column -- column number where the error occurred
    """

    def __init__(self, left: Type, operator: str, right: Type, line: int, column: int) -> None:
        self.message = f"{self.type()}: {left} {operator} {right} on line {line}, column {column}"
        self.line = line
        self.column = column
        super().__init__()

    def __str__(self) -> str:
        return self.message


class _TypeError(Error):
    """Exception raised for errors in the input.

    Attributes:
        message -- explanation of the error
        line -- line number where the error occurred
        column -- column number where the error occurred
    """

    def __init__(self, identifier: str, line: int, column: int) -> None:
        self.message = f"{self.type()}: {identifier}, line {line}, column {column}"
        self.line = line
        self.column = column
        super().__init__()

    def __str__(self) -> str:
        return self.message


class InvalidNumberOfArguments(Error):  # TODO: Replace by TypeError
    """Exception raised for errors in the input.

    Attributes:
        message -- explanation of the error
        line -- line number where the error occurred
        column -- column number where the error occurred
    """

    def __init__(self, expected: int, actual: int, line: int, column: int) -> None:
        self.message = f"{self.type()}: Expected {expected}, got {actual}"
        self.line = line
        self.column = column
        super().__init__()

    def __str__(self) -> str:
        return self.message


class UnsupportedArgumentType(Error):  # TODO: Replace by TypeError
    """Exception raised for errors in the input.

    Attributes:
        message -- explanation of the error
        line -- line number where the error occurred
        column -- column number where the error occurred
    """

    def __init__(self, expected: TypeName, actual: Type, line: int, column: int) -> None:
        self.message = f"{self.type()}: Expected {expected}, got {actual}"
        self.line = line
        self.column = column
        super().__init__()

    def __str__(self) -> str:
        return self.message


class InvalidTypeAssignment(Error):  # TODO: Replace by TypeError
    """Exception raised for errors in the input.

    Attributes:
        message -- explanation of the error
        line -- line number where the error occurred
        column -- column number where the error occurred
    """

    def __init__(self, expected: Type, actual: Type, line: int, column: int) -> None:
        self.message = f"{self.type()}: {expected} != {actual} on line {line}, column {column}"
        self.line = line
        self.column = column
        super().__init__()

    def __str__(self) -> str:
        return self.message


class ConstantReassignmentError(Error):  # TODO: Replace by TypeError

    def __init__(self, identifier: str, line: int, column: int) -> None:
        self.message = f"{self.type()}: {identifier} on line {line}, column {column}"
        self.line = line
        self.column = column
        super().__init__()

    def __str__(self) -> str:
        return self.message


class ModelReassignmentError(Error):  # TODO: Replace by TypeError

        def __init__(self, identifier: str, line: int, column: int) -> None:
            self.message = f"{self.type()}: {identifier} on line {line}, column {column}"
            self.line = line
            self.column = column
            super().__init__()

        def __str__(self) -> str:
            return self.message


class _ValueError(Error):
    """Exception raised for errors in the input.

    Attributes:
        message -- explanation of the error
        line -- line number where the error occurred
        column -- column number where the error occurred
    """

    def __init__(self, identifier: str, line: int, column: int) -> None:
        self.message = f"{self.type()}: {identifier}, line {line}, column {column}"
        self.line = line
        self.column = column
        super().__init__()

    def __str__(self) -> str:
        return self.message


class NotAnActionError(Error):

    def __init__(self, identifier: str, line: int, column: int) -> None:
        self.message = f"{self.type()}: {identifier}, line {line}, column {column}"
        self.line = line
        self.column = column
        super().__init__()

    def __str__(self) -> str:
        return self.message
