"""
Public subclasses of Exception
"""


class FigurativeError(Exception):
    """
    Top level Exception object for custom exception hierarchy
    """

    pass


class ExecutorError(FigurativeError):
    pass


# Smtlib


class SmtlibError(FigurativeError):
    pass


class Z3NotFoundError(SmtlibError):
    pass


class SolverError(SmtlibError):
    pass


class SolverUnknown(SolverError):
    pass


class TooManySolutions(SolverError):
    def __init__(self, solutions):
        super().__init__("Max number of different solutions hit")
        self.solutions = solutions


# Ethereum


class EthereumError(FigurativeError):
    pass


class DependencyError(EthereumError):
    def __init__(self, lib_names):
        super().__init__(
            "You must pre-load and provide libraries addresses{ libname:address, ...} for %r"
            % lib_names
        )
        self.lib_names = lib_names


class NoAliveStates(EthereumError):
    pass
