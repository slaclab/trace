import re
import ast
import math
from typing import Set

_ALLOWED_FUNC_NAMES: Set[str] = {*vars(math).keys(), "mean", "ln"}

_ALLOWED_NODES = (
    ast.Expression,
    ast.Constant,
    ast.UnaryOp,
    ast.UAdd,
    ast.USub,
    ast.BinOp,
    ast.Add,
    ast.Sub,
    ast.Mult,
    ast.Div,
    ast.Pow,
    ast.Mod,
    ast.Call,
    ast.Name,
    ast.Load,
    ast.BitXor,
)


def validate_formula(expr: str, allowed_symbols: Set[str]) -> None:
    """Validate a mathematical formula expression for safety and correctness.

    This function parses the expression using Python's AST and validates that:
    - Only allowed operators and functions are used
    - All variable names are in the allowed symbols set
    - The expression is syntactically valid

    Parameters
    ----------
    expr : str
        The mathematical expression to validate
    allowed_symbols : Set[str]
        Set of allowed variable names in the expression

    Raises
    ------
    ValueError
        If the expression contains disallowed operators, functions, or symbols
    SyntaxError
        If the expression is not syntactically valid Python
    """
    tree = ast.parse(expr, mode="eval")

    for node in ast.walk(tree):
        if not isinstance(node, _ALLOWED_NODES):
            raise ValueError(f'Operator "{type(node).__name__}" not allowed')

        if isinstance(node, ast.Call):
            fn = node.func.id if isinstance(node.func, ast.Name) else None
            if fn not in _ALLOWED_FUNC_NAMES:
                raise ValueError(f'Function "{fn}" not permitted')

        if isinstance(node, ast.Name):
            if node.id not in allowed_symbols and node.id not in _ALLOWED_FUNC_NAMES:
                raise ValueError(f'Unknown symbol "{node.id}"')

    # compile(tree, "<formula>", "eval")


def sanitize_for_validation(expr: str) -> tuple[str, set[str]]:
    """Convert formula expression with variable placeholders to valid Python expression.

    This function replaces variable placeholders in the format {VAR_NAME} with
    temporary identifiers (v0, v1, etc.) that can be parsed by Python's AST.
    This allows validation of formulas that reference curve variables.

    Parameters
    ----------
    expr : str
        The formula expression containing variable placeholders like {PV1}

    Returns
    -------
    tuple[str, set[str]]
        A tuple containing:
        - python_expr : str
            Expression that the Python AST can parse with temporary identifiers
        - allowed_syms : set[str]
            The generated temporary identifiers, ready to pass to `validate_formula`
    """
    mapping = {}

    def _repl(match):
        var = match.group(1)
        if var not in mapping:
            mapping[var] = f"v{len(mapping)}"
        return mapping[var]

    python_expr = re.sub(r"{([^}]+)}", _repl, expr)
    return python_expr, set(mapping.values())
