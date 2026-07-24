from __future__ import annotations

import re
from typing import Any

from .ast_nodes import (
    ArrayAccessExpr,
    ArrayTarget,
    ArrayType,
    AssignStmt,
    BinaryExpr,
    CallExpr,
    CaseStmt,
    ConstantStmt,
    DeclareStmt,
    ForStmt,
    IfStmt,
    InputStmt,
    LiteralExpr,
    OutputStmt,
    Program,
    RepeatStmt,
    UnaryExpr,
    VariableExpr,
    VarTarget,
    WhileStmt,
)
from .errors import PseudoRuntimeError
from .runtime import (
    ArrayValue,
    Runtime,
    output_value,
    runtime_type_name,
    same_type,
    type_to_str,
)
from .tokens import T
from .values import Char, DateValue, make_date


class Interpreter:
    def __init__(self, runtime: Runtime):
        self.runtime = runtime

    @property
    def env(self):
        return self.runtime.env

    def execute_program(self, program: Program):
        for stmt in program.statements:
            self.execute(stmt)

    def execute_block(self, statements: list[Any]):
        for stmt in statements:
            self.execute(stmt)

    def execute(self, stmt: Any):
        try:
            return self._execute(stmt)

        except PseudoRuntimeError as err:
            if err.line is None:
                span = getattr(stmt, "span", None)

                if span is not None:
                    raise err.with_location(span.line, span.col) from None

            raise

    def _execute(self, stmt: Any):
        if isinstance(stmt, DeclareStmt):
            self.env.define(stmt.name, stmt.type_spec)
            return

        if isinstance(stmt, ConstantStmt):
            value = self.eval(stmt.expr)
            self.env.define_constant(stmt.name, value)
            return

        if isinstance(stmt, AssignStmt):
            value = self.eval(stmt.expr)
            self.assign_target(stmt.target, value)
            return

        if isinstance(stmt, InputStmt):
            type_spec = self.target_type(stmt.target)
            text = self.runtime.input_provider()
            value = parse_input_value(text, type_spec)
            self.assign_target(stmt.target, value)
            return

        if isinstance(stmt, OutputStmt):
            values = [
                output_value(self.eval(expr))
                for expr in stmt.exprs
            ]

            self.runtime.output_writer("".join(values))
            return

        if isinstance(stmt, IfStmt):
            condition = self.require_bool(self.eval(stmt.condition))

            if condition:
                self.execute_block(stmt.then_body)
            else:
                self.execute_block(stmt.else_body)

            return

        if isinstance(stmt, CaseStmt):
            self.execute_case(stmt)
            return

        if isinstance(stmt, WhileStmt):
            while self.require_bool(self.eval(stmt.condition)):
                self.execute_block(stmt.body)

            return

        if isinstance(stmt, RepeatStmt):
            while True:
                self.execute_block(stmt.body)

                if self.require_bool(self.eval(stmt.condition)):
                    break

            return

        if isinstance(stmt, ForStmt):
            self.execute_for(stmt)
            return

        raise PseudoRuntimeError(f"Unknown statement type: {stmt!r}")

    def execute_case(self, stmt: CaseStmt):
        selector = self.eval(stmt.selector)

        for clause in stmt.clauses:
            start = self.eval(clause.start)
            end = self.eval(clause.end) if clause.end is not None else None

            if self.case_matches(selector, start, end):
                self.execute_block(clause.body)
                return

        self.execute_block(stmt.otherwise_body)

    def case_matches(self, selector: Any, start: Any, end: Any | None) -> bool:
        if end is None:
            return selector == start

        return (
            self.compare_values(start, T.LESS_EQUAL, selector)
            and self.compare_values(selector, T.LESS_EQUAL, end)
        )

    def execute_for(self, stmt: ForStmt):
        start = self.require_int(self.eval(stmt.start))
        end = self.require_int(self.eval(stmt.end))
        step = self.require_int(self.eval(stmt.step)) if stmt.step is not None else 1

        if step == 0:
            raise PseudoRuntimeError("FOR loop STEP cannot be 0")

        if self.env.exists(stmt.var_name):
            binding = self.env.get_binding(stmt.var_name)

            if not same_type(binding.type_spec, T.INTEGER):
                raise PseudoRuntimeError("FOR loop variable must be INTEGER")
        else:
            if self.runtime.strict:
                raise PseudoRuntimeError(
                    f"Undefined FOR loop variable {stmt.var_name!r}"
                )

            self.env.define(stmt.var_name, T.INTEGER, 0)

        i = start

        def keep_going():
            return i <= end if step > 0 else i >= end

        while keep_going():
            self.env.assign(stmt.var_name, i)
            self.execute_block(stmt.body)
            i += step

    def assign_target(self, target: Any, value: Any):
        if isinstance(target, VarTarget):
            self.env.assign(target.name, value)
            return

        if isinstance(target, ArrayTarget):
            arr = self.env.get(target.name)

            if not isinstance(arr, ArrayValue):
                raise PseudoRuntimeError(f"{target.name!r} is not an ARRAY")

            indices = [
                self.require_int(self.eval(expr))
                for expr in target.indices
            ]

            arr.set(indices, value)
            return

        raise PseudoRuntimeError(f"Invalid assignment target {target!r}")

    def target_type(self, target: Any) -> Any:
        if isinstance(target, VarTarget):
            if self.env.exists(target.name):
                return self.env.get_binding(target.name).type_spec

            if self.runtime.strict:
                raise PseudoRuntimeError(f"Undefined variable {target.name!r}")

            return T.STRING

        if isinstance(target, ArrayTarget):
            arr = self.env.get(target.name)

            if not isinstance(arr, ArrayValue):
                raise PseudoRuntimeError(f"{target.name!r} is not an ARRAY")

            return arr.type_spec.element_type

        raise PseudoRuntimeError(f"Invalid target {target!r}")

    def eval(self, expr: Any) -> Any:
        if isinstance(expr, LiteralExpr):
            return expr.value

        if isinstance(expr, VariableExpr):
            return self.env.get(expr.name)

        if isinstance(expr, ArrayAccessExpr):
            arr = self.eval(expr.array_expr)

            if not isinstance(arr, ArrayValue):
                raise PseudoRuntimeError("Indexed value is not an ARRAY")

            indices = [
                self.require_int(self.eval(e))
                for e in expr.indices
            ]

            return arr.get(indices)

        if isinstance(expr, UnaryExpr):
            right = self.eval(expr.right)

            if expr.op.type == T.MINUS:
                self.require_number(right)
                return -right

            if expr.op.type == T.NOT:
                return not self.require_bool(right)

            raise PseudoRuntimeError(f"Unknown unary operator {expr.op.lexeme!r}")

        if isinstance(expr, BinaryExpr):
            if expr.op.type == T.AND:
                left = self.require_bool(self.eval(expr.left))

                if not left:
                    return False

                return self.require_bool(self.eval(expr.right))

            if expr.op.type == T.OR:
                left = self.require_bool(self.eval(expr.left))

                if left:
                    return True

                return self.require_bool(self.eval(expr.right))

            left = self.eval(expr.left)
            right = self.eval(expr.right)
            return self.eval_binary(left, expr.op, right)

        if isinstance(expr, CallExpr):
            args = [
                self.eval(arg)
                for arg in expr.args
            ]

            return self.call_builtin(expr.name, args)

        raise PseudoRuntimeError(f"Unknown expression type: {expr!r}")

    def eval_binary(self, left: Any, op: Any, right: Any):
        t = op.type

        if t == T.PLUS:
            self.require_number(left)
            self.require_number(right)
            return left + right

        if t == T.MINUS:
            self.require_number(left)
            self.require_number(right)
            return left - right

        if t == T.STAR:
            self.require_number(left)
            self.require_number(right)
            return left * right

        if t == T.SLASH:
            self.require_number(left)
            self.require_number(right)

            if right == 0:
                raise PseudoRuntimeError("Division by zero")

            return float(left) / float(right)

        if t == T.DIV:
            left_i = self.require_int(left)
            right_i = self.require_int(right)

            if right_i == 0:
                raise PseudoRuntimeError("Division by zero")

            return int(left_i / right_i)

        if t == T.MOD:
            left_i = self.require_int(left)
            right_i = self.require_int(right)

            if right_i == 0:
                raise PseudoRuntimeError("Modulo by zero")

            return left_i % right_i

        if t == T.AMP:
            if not isinstance(left, str) or not isinstance(right, str):
                raise PseudoRuntimeError("& requires STRING or CHAR operands")

            return str(left) + str(right)

        if t == T.EQUAL:
            return left == right

        if t == T.NOT_EQUAL:
            return left != right

        if t in {
            T.LESS,
            T.LESS_EQUAL,
            T.GREATER,
            T.GREATER_EQUAL,
        }:
            return self.compare_values(left, t, right)

        if t == T.AND:
            return self.require_bool(left) and self.require_bool(right)

        if t == T.OR:
            return self.require_bool(left) or self.require_bool(right)

        raise PseudoRuntimeError(f"Unknown binary operator {op.lexeme!r}")

    def compare_values(self, left: Any, op_type: str, right: Any) -> bool:
        if self.is_number(left) and self.is_number(right):
            a, b = left, right

        elif isinstance(left, str) and isinstance(right, str):
            a, b = str(left), str(right)

        elif isinstance(left, DateValue) and isinstance(right, DateValue):
            a, b = left.key(), right.key()

        else:
            raise PseudoRuntimeError(
                f"Cannot compare {runtime_type_name(left)} "
                f"with {runtime_type_name(right)}"
            )

        if op_type == T.LESS:
            return a < b

        if op_type == T.LESS_EQUAL:
            return a <= b

        if op_type == T.GREATER:
            return a > b

        if op_type == T.GREATER_EQUAL:
            return a >= b

        raise PseudoRuntimeError(f"Unknown comparison operator {op_type}")

    def call_builtin(self, name: str, args: list[Any]) -> Any:
        upper = name.upper()

        if upper == "LENGTH":
            self.require_arg_count(upper, args, 1)
            s = self.require_string(args[0])
            return len(s)

        if upper == "RIGHT":
            self.require_arg_count(upper, args, 2)
            s = self.require_string(args[0])
            x = self.require_int(args[1])

            if x < 0:
                raise PseudoRuntimeError("RIGHT length cannot be negative")

            if x == 0:
                return ""

            return s[-x:]

        if upper == "MID":
            self.require_arg_count(upper, args, 3)
            s = self.require_string(args[0])
            x = self.require_int(args[1])
            y = self.require_int(args[2])

            if x < 1:
                raise PseudoRuntimeError(
                    "MID start position is 1-based and must be >= 1"
                )

            if y < 0:
                raise PseudoRuntimeError("MID length cannot be negative")

            start = x - 1
            return s[start:start + y]

        if upper == "LCASE":
            self.require_arg_count(upper, args, 1)
            c = self.require_char(args[0])
            return Char(c.lower())

        if upper == "UCASE":
            self.require_arg_count(upper, args, 1)
            c = self.require_char(args[0])
            return Char(c.upper())

        if upper == "INT":
            self.require_arg_count(upper, args, 1)
            self.require_number(args[0])
            return int(args[0])

        if upper == "RAND":
            self.require_arg_count(upper, args, 1)
            x = self.require_int(args[0])

            if x <= 0:
                raise PseudoRuntimeError("RAND argument must be positive")

            return self.runtime.rng.random() * x

        raise PseudoRuntimeError(f"Unknown function {name!r}")

    @staticmethod
    def require_arg_count(name: str, args: list[Any], count: int):
        if len(args) != count:
            raise PseudoRuntimeError(
                f"{name} expects {count} argument(s), got {len(args)}"
            )

    @staticmethod
    def is_number(value: Any) -> bool:
        return type(value) is int or type(value) is float

    def require_number(self, value: Any):
        if not self.is_number(value):
            raise PseudoRuntimeError(
                f"Expected number, got {runtime_type_name(value)}"
            )

    @staticmethod
    def require_int(value: Any) -> int:
        if type(value) is int:
            return value

        raise PseudoRuntimeError(
            f"Expected INTEGER, got {runtime_type_name(value)}"
        )

    @staticmethod
    def require_bool(value: Any) -> bool:
        if type(value) is bool:
            return value

        raise PseudoRuntimeError(
            f"Expected BOOLEAN, got {runtime_type_name(value)}"
        )

    @staticmethod
    def require_string(value: Any) -> str:
        if isinstance(value, str):
            return str(value)

        raise PseudoRuntimeError(
            f"Expected STRING, got {runtime_type_name(value)}"
        )

    @staticmethod
    def require_char(value: Any) -> Char:
        if isinstance(value, Char):
            return value

        if isinstance(value, str) and len(value) == 1:
            return Char(value)

        raise PseudoRuntimeError(
            f"Expected CHAR, got {runtime_type_name(value)}"
        )


def parse_input_value(text: str, type_spec: Any) -> Any:
    if isinstance(type_spec, ArrayType):
        raise PseudoRuntimeError("Cannot INPUT a whole ARRAY")

    t = type_to_str(type_spec)

    try:
        if t == T.INTEGER:
            return int(text)

        if t == T.REAL:
            return float(text)

        if t == T.CHAR:
            if len(text) != 1:
                raise PseudoRuntimeError(
                    "CHAR input must contain exactly one character"
                )

            return Char(text)

        if t == T.STRING:
            return text

        if t == T.BOOLEAN:
            upper = text.strip().upper()

            if upper == "TRUE":
                return True

            if upper == "FALSE":
                return False

            raise PseudoRuntimeError("BOOLEAN input must be TRUE or FALSE")

        if t == T.DATE:
            match = re.fullmatch(
                r"(\d{1,2})/(\d{1,2})/(\d{4})",
                text.strip(),
            )

            if not match:
                raise PseudoRuntimeError(
                    "DATE input must use dd/mm/yyyy format"
                )

            day, month, year = map(int, match.groups())
            return make_date(day, month, year)

    except ValueError as e:
        raise PseudoRuntimeError(f"Invalid input for {t}: {text!r}") from e

    raise PseudoRuntimeError(f"Unsupported INPUT type {type_spec!r}")
