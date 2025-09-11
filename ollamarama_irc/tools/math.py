from __future__ import annotations

import ast
import operator as op
from typing import Dict, Any

_ALLOWED_OPERATORS = {
    ast.Add: op.add,
    ast.Sub: op.sub,
    ast.Mult: op.mul,
    ast.Div: op.truediv,
    ast.Pow: op.pow,
    ast.Mod: op.mod,
    ast.FloorDiv: op.floordiv,
    ast.UAdd: op.pos,
    ast.USub: op.neg,
}


def _eval(node: ast.AST) -> float:
    """Evaluate a restricted arithmetic AST safely.

    Supports binary operations (+, -, *, /, %, **, //) and unary +/- on
    numeric constants only. Any other node type raises ``ValueError``.

    Args:
        node: Parsed AST node (from ``ast.parse(expr, mode="eval")``).

    Returns:
        The numeric result as a float.

    Raises:
        ValueError: If the expression contains unsupported nodes/operators.
    """
    if isinstance(node, ast.Expression):
        return _eval(node.body)
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return float(node.value)
    if isinstance(node, ast.BinOp) and type(node.op) in _ALLOWED_OPERATORS:
        left = _eval(node.left)
        right = _eval(node.right)
        return _ALLOWED_OPERATORS[type(node.op)](left, right)
    if isinstance(node, ast.UnaryOp) and type(node.op) in _ALLOWED_OPERATORS:
        operand = _eval(node.operand)
        return _ALLOWED_OPERATORS[type(node.op)](operand)
    raise ValueError("Unsupported expression")


def calculate_expression(expression: str) -> Dict[str, Any]:
    """Evaluate a basic arithmetic expression string.

    The evaluator accepts numbers, parentheses, and operators ``+``, ``-``,
    ``*``, ``/``, ``%``, ``**`` and unary ``+/-``. It rejects variable names
    and any non-arithmetic operations.

    Args:
        expression: The arithmetic expression to evaluate.

    Returns:
        A mapping with either ``{"result": float}`` on success, or
        ``{"error": str}`` when parsing/evaluation fails.
    """
    try:
        parsed = ast.parse(expression, mode="eval")
        result = _eval(parsed)
    except Exception:
        return {"error": "Invalid arithmetic expression."}
    return {"result": float(result)}
