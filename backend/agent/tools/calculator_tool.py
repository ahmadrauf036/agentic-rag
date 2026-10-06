"""
Calculator tool for the agent.

Deliberately does NOT use Python's eval() on the LLM's input — eval() would
let a crafted expression (whether from a malicious user or an LLM led
astray by prompt injection in retrieved documents) execute arbitrary code.
numexpr only understands numeric expressions, so it's safe by construction:
it has no access to Python builtins, imports, or attribute access.
"""

import logging

import numexpr
from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class CalculatorInput(BaseModel):
    expression: str = Field(
        ...,
        description=(
            "A mathematical expression to evaluate, e.g. '2 + 2', "
            "'(15 * 3.5) / 7', 'sqrt(144)'. Supports standard arithmetic "
            "operators and common math functions."
        ),
    )


def _run(expression: str) -> str:
    try:
        result = numexpr.evaluate(expression).item()
        return str(result)
    except Exception as error:
        logger.warning("calculator tool failed for expression=%r: %s", expression, error)
        return (
            f"Could not evaluate expression '{expression}': {error}. "
            "Make sure it's a valid mathematical expression."
        )


calculator_tool = StructuredTool.from_function(
    func=_run,
    name="calculator",
    description=(
        "Evaluate a mathematical expression and return the numeric result. "
        "Use this for any arithmetic, percentages, unit conversions, or "
        "numeric calculations. Do not use this for searching documents."
    ),
    args_schema=CalculatorInput,
)

