import re
import ast
import math
from typing import Set

_ALLOWED_FUNC_NAMES: Set[str] = {
    *vars(math).keys(),
}

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
)


def validate_formula(expr: str, allowed_symbols: Set[str]) -> None:
    """
    Raises ValueError if `expr` is not a valid calc expression.
    """
    tree = ast.parse(expr, mode="eval")

    for node in ast.walk(tree):
        if not isinstance(node, _ALLOWED_NODES):
            raise ValueError(f"Operator “{type(node).__name__}” not allowed")

        if isinstance(node, ast.Call):
            fn = node.func.id if isinstance(node.func, ast.Name) else None
            if fn not in _ALLOWED_FUNC_NAMES:
                raise ValueError(f"Function “{fn}” not permitted")

        if isinstance(node, ast.Name):
            if node.id not in allowed_symbols and node.id not in _ALLOWED_FUNC_NAMES:
                raise ValueError(f"Unknown symbol “{node.id}”")

    # compile(tree, "<formula>", "eval")


def sanitize_for_validation(expr: str) -> tuple[str, set[str]]:
    """
    Replace each  {VAR_NAME}  with a temporary identifier (v0, v1 …).

    Returns
    -------
    python_expr : str
        Expression that the Python AST can parse.
    allowed_syms : set[str]
        The generated identifiers, ready to pass to `validate_formula`.
    """
    mapping = {}

    def _repl(match):
        var = match.group(1)
        if var not in mapping:
            mapping[var] = f"v{len(mapping)}"
        return mapping[var]

    python_expr = re.sub(r"{([^}]+)}", _repl, expr)
    return python_expr, set(mapping.values())
