from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from .ast_nodes import (
    AddressOfExpr,
    ArrayAccessExpr,
    ArrayTarget,
    ArrayType,
    AssignStmt,
    BinaryExpr,
    CallExpr,
    CallStmt,
    CaseStmt,
    ClassDecl,
    ClassFieldDecl,
    CloseFileStmt,
    ConstantStmt,
    DeclareStmt,
    DefineSetStmt,
    DerefExpr,
    DerefTarget,
    FieldAccessExpr,
    FieldTarget,
    ForStmt,
    FunctionDecl,
    GetRecordStmt,
    IfStmt,
    IndexTarget,
    InputStmt,
    LiteralExpr,
    MethodCallExpr,
    MethodCallStmt,
    MethodDecl,
    NewExpr,
    OpenFileStmt,
    OutputStmt,
    Param,
    PointerType,
    ProcedureDecl,
    Program,
    PutRecordStmt,
    ReadFileStmt,
    RepeatStmt,
    ReturnStmt,
    SeekStmt,
    SetTypeSpec,
    SourceSpan,
    SuperExpr,
    TypeDeclEnum,
    TypeDeclPointer,
    TypeDeclRecord,
    TypeDeclSet,
    UnaryExpr,
    UserTypeRef,
    VariableExpr,
    VarTarget,
    WhileStmt,
    WriteFileStmt,
)
from .lexer import Lexer
from .parser import Parser
from .tokens import T
from .values import Char, DateValue


SEMANTIC_CODES = {
    "SEM001": "undefined identifier",
    "SEM002": "duplicate declaration",
    "SEM003": "read before explicit initialization",
    "SEM004": "incompatible assignment",
    "SEM005": "invalid condition or operator operand",
    "SEM006": "unknown or incorrectly used callable",
    "SEM007": "wrong argument count",
    "SEM008": "incompatible argument",
    "SEM009": "invalid BYREF argument",
    "SEM010": "invalid member or index access",
    "SEM011": "function may not return a value",
    "SEM012": "invalid RETURN",
    "SEM013": "incompatible return value",
    "SEM014": "unreachable statement",
    "SEM015": "unknown or invalid type",
}


@dataclass(frozen=True)
class SemanticDiagnostic:
    code: str
    severity: str
    message: str
    line: int
    col: int

    def format(self, filename: str | None = None) -> str:
        location = f"{self.line}:{self.col}"
        if filename is not None:
            location = f"{filename}:{location}"
        return f"{location}: {self.severity} {self.code}: {self.message}"

    def to_dict(self) -> dict[str, str | int]:
        return asdict(self)


@dataclass(frozen=True)
class SemanticReport:
    diagnostics: tuple[SemanticDiagnostic, ...]
    strict: bool
    recommendations: bool

    @property
    def valid(self) -> bool:
        return not any(item.severity == "error" for item in self.diagnostics)

    @property
    def has_warnings(self) -> bool:
        return any(item.severity == "warning" for item in self.diagnostics)

    def to_dict(self) -> dict[str, object]:
        return {
            "valid": self.valid,
            "strict": self.strict,
            "recommendations": self.recommendations,
            "diagnostics": [item.to_dict() for item in self.diagnostics],
        }


@dataclass
class _Symbol:
    name: str
    type_spec: Any
    initialized: bool
    constant: bool = False
    access: str | None = None
    owner: str | None = None


class _Scope:
    def __init__(self, parent: _Scope | None = None):
        self.parent = parent
        self.symbols: dict[str, _Symbol] = {}

    def resolve(self, name: str) -> _Symbol | None:
        key = _norm(name)
        if key in self.symbols:
            return self.symbols[key]
        if self.parent is not None:
            return self.parent.resolve(name)
        return None


@dataclass(frozen=True)
class _UnknownType:
    pass


UNKNOWN = _UnknownType()


@dataclass
class _ClassInfo:
    decl: ClassDecl
    fields: dict[str, ClassFieldDecl]
    methods: dict[str, MethodDecl]


_BUILTINS: dict[str, tuple[tuple[Any, ...], Any]] = {
    "EOF": ((T.STRING,), T.BOOLEAN),
    "LENGTH": ((T.STRING,), T.INTEGER),
    "RIGHT": ((T.STRING, T.INTEGER), T.STRING),
    "MID": ((T.STRING, T.INTEGER, T.INTEGER), T.STRING),
    "LCASE": ((T.CHAR,), T.CHAR),
    "UCASE": ((T.CHAR,), T.CHAR),
    "RAND": ((T.INTEGER,), T.REAL),
}

_SET_QUERY_FUNCTIONS = {
    "CARDINALITY": T.INTEGER,
    "ISEMPTY": T.BOOLEAN,
}
_SET_BINARY_PREDICATES = {
    "ISSUBSET",
    "ISPROPERSUBSET",
    "ISSUPERSET",
    "ISPROPERSUPERSET",
    "ISDISJOINT",
}
_SET_ALGEBRA = {
    "UNION",
    "INTERSECTION",
    "DIFFERENCE",
    "SYMMETRICDIFFERENCE",
}
_SET_PROCEDURES = {"SETADD", "SETREMOVE", "SETDISCARD", "SETCLEAR"}


def analyze_source(
    source: str,
    *,
    strict: bool = False,
    recommendations: bool = False,
) -> SemanticReport:
    tokens = Lexer(source, strict=strict).scan_tokens()
    program = Parser(tokens).parse_program()
    return analyze_program(
        program,
        strict=strict,
        recommendations=recommendations,
    )


def analyze_file(
    path: str | Path,
    *,
    strict: bool = False,
    recommendations: bool = False,
) -> SemanticReport:
    source = Path(path).read_text(encoding="utf-8")
    return analyze_source(
        source,
        strict=strict,
        recommendations=recommendations,
    )


def analyze_program(
    program: Program,
    *,
    strict: bool = False,
    recommendations: bool = False,
) -> SemanticReport:
    analyzer = _Analyzer(strict=strict, recommendations=recommendations)
    return analyzer.analyze(program)


class _Analyzer:
    def __init__(self, *, strict: bool, recommendations: bool):
        self.strict = strict
        self.recommendations = recommendations
        self.diagnostics: list[SemanticDiagnostic] = []
        self.global_scope = _Scope()
        self.scope = self.global_scope
        self.types: dict[str, Any] = {}
        self.enum_values: dict[str, Any] = {}
        self.procedures: dict[str, ProcedureDecl] = {}
        self.functions: dict[str, FunctionDecl] = {}
        self.classes: dict[str, _ClassInfo] = {}
        self.current_callable: ProcedureDecl | FunctionDecl | MethodDecl | None = None
        self.current_class: ClassDecl | None = None

    def analyze(self, program: Program) -> SemanticReport:
        self._register_declarations(program)

        declaration_types = (
            TypeDeclEnum,
            TypeDeclPointer,
            TypeDeclRecord,
            TypeDeclSet,
            ClassDecl,
            ProcedureDecl,
            FunctionDecl,
        )
        self._analyze_block(
            [
                statement
                for statement in program.statements
                if not isinstance(statement, declaration_types)
            ]
        )

        for declaration in self.procedures.values():
            self._analyze_callable(declaration)
        for declaration in self.functions.values():
            self._analyze_callable(declaration)
        for info in self.classes.values():
            self._analyze_class(info)

        unique = {
            (item.code, item.severity, item.message, item.line, item.col): item
            for item in self.diagnostics
        }
        diagnostics = tuple(
            sorted(
                unique.values(),
                key=lambda item: (
                    item.line,
                    item.col,
                    0 if item.severity == "error" else 1,
                    item.code,
                ),
            )
        )
        return SemanticReport(diagnostics, self.strict, self.recommendations)

    def _register_declarations(self, program: Program) -> None:
        for statement in program.statements:
            if isinstance(
                statement,
                (TypeDeclEnum, TypeDeclPointer, TypeDeclRecord, TypeDeclSet),
            ):
                self._register_type(statement)
            elif isinstance(statement, ClassDecl):
                self._register_class(statement)

        for statement in program.statements:
            if isinstance(statement, ProcedureDecl):
                self._register_callable(statement, self.procedures)
            elif isinstance(statement, FunctionDecl):
                self._register_callable(statement, self.functions)

        for declaration in self.types.values():
            self._validate_type_declaration(declaration)
        for info in self.classes.values():
            self._validate_class_declaration(info)
        for declaration in self.functions.values():
            self._resolve_type(declaration.return_type, declaration.span)

    def _register_type(self, declaration: Any) -> None:
        key = _norm(declaration.name)
        if key in self.types or key in self.classes:
            self._error(
                "SEM002",
                f"TYPE {declaration.name!r} is already defined",
                declaration.span,
            )
            return
        self.types[key] = declaration

        if isinstance(declaration, TypeDeclEnum):
            seen: set[str] = set()
            for value in declaration.values:
                value_key = _norm(value)
                if value_key in seen or value_key in self.enum_values:
                    self._error(
                        "SEM002",
                        f"Enumerated value {value!r} is already defined",
                        declaration.span,
                    )
                    continue
                seen.add(value_key)
                self.enum_values[value_key] = UserTypeRef(declaration.name)

    def _register_class(self, declaration: ClassDecl) -> None:
        key = _norm(declaration.name)
        if key in self.types or key in self.classes:
            self._error(
                "SEM002",
                f"CLASS {declaration.name!r} is already defined",
                declaration.span,
            )
            return
        fields = {
            _norm(member.name): member
            for member in declaration.members
            if isinstance(member, ClassFieldDecl)
        }
        methods = {
            _norm(member.name): member
            for member in declaration.members
            if isinstance(member, MethodDecl)
        }
        self.classes[key] = _ClassInfo(declaration, fields, methods)

    def _register_callable(self, declaration: Any, destination: dict[str, Any]) -> None:
        key = _norm(declaration.name)
        other = self.functions if destination is self.procedures else self.procedures
        if key in destination or key in other:
            self._error(
                "SEM002",
                f"Callable {declaration.name!r} is already defined",
                declaration.span,
            )
            return
        destination[key] = declaration

    def _validate_type_declaration(self, declaration: Any) -> None:
        if isinstance(declaration, TypeDeclPointer):
            self._resolve_type(declaration.target_type, declaration.span)
        elif isinstance(declaration, TypeDeclSet):
            element_type = self._resolve_type(
                declaration.element_type,
                declaration.span,
            )
            if not self._valid_set_element_type(element_type):
                self._error(
                    "SEM015",
                    f"SET element type cannot be {_type_name(element_type)}",
                    declaration.span,
                )
        elif isinstance(declaration, TypeDeclRecord):
            seen: set[str] = set()
            for field in declaration.fields:
                key = _norm(field.name)
                if key in seen:
                    self._error(
                        "SEM002",
                        f"Duplicate field {field.name!r} in TYPE {declaration.name!r}",
                        field.span or declaration.span,
                    )
                seen.add(key)
                self._resolve_type(field.type_spec, field.span or declaration.span)
            if any(
                self._record_contains(
                    field.type_spec,
                    declaration.name,
                    set(),
                )
                for field in declaration.fields
            ):
                self._error(
                    "SEM015",
                    f"Recursive record TYPE {declaration.name!r} is not supported",
                    declaration.span,
                )

    def _validate_class_declaration(self, info: _ClassInfo) -> None:
        declaration = info.decl
        if declaration.parent_name is not None:
            parent = self.classes.get(_norm(declaration.parent_name))
            if parent is None:
                self._error(
                    "SEM015",
                    f"Unknown superclass {declaration.parent_name!r}",
                    declaration.span,
                )
            elif self._class_inherits(parent.decl.name, declaration.name):
                self._error(
                    "SEM015",
                    f"Inheritance cycle involving CLASS {declaration.name!r}",
                    declaration.span,
                )

        seen: set[str] = set()
        inherited_fields = (
            self._all_class_fields(declaration.parent_name)
            if declaration.parent_name is not None
            else {}
        )
        for member in declaration.members:
            key = _norm(member.name)
            if key in seen:
                self._error(
                    "SEM002",
                    f"Duplicate member {member.name!r} in CLASS {declaration.name!r}",
                    getattr(member, "span", None) or declaration.span,
                )
            seen.add(key)
            if isinstance(member, ClassFieldDecl):
                if key in inherited_fields:
                    self._error(
                        "SEM002",
                        f"Property {member.name!r} in CLASS "
                        f"{declaration.name!r} duplicates an inherited property",
                        member.span or declaration.span,
                    )
                self._resolve_type(member.type_spec, member.span or declaration.span)
            else:
                if key == _norm("NEW") and member.kind != T.PROCEDURE:
                    self._error(
                        "SEM006",
                        "Constructor NEW must be a PROCEDURE",
                        member.span or declaration.span,
                    )
                self._validate_parameters(member.params, member.span)
                if member.return_type is not None:
                    self._resolve_type(member.return_type, member.span)

    def _validate_parameters(
        self,
        parameters: list[Param],
        fallback_span: SourceSpan | None,
    ) -> None:
        seen: set[str] = set()
        for parameter in parameters:
            key = _norm(parameter.name)
            if key in seen:
                self._error(
                    "SEM002",
                    f"Duplicate parameter {parameter.name!r}",
                    parameter.span or fallback_span,
                )
            seen.add(key)
            self._resolve_type(parameter.type_spec, parameter.span or fallback_span)

    def _analyze_class(self, info: _ClassInfo) -> None:
        previous_class = self.current_class
        self.current_class = info.decl
        class_scope = _Scope(self.global_scope)
        for field in self._all_class_fields(info.decl.name).values():
            _field, owner = self._find_field(info.decl.name, field.name)
            self._define_symbol(
                class_scope,
                field.name,
                field.type_spec,
                initialized=not self.recommendations,
                span=field.span or info.decl.span,
                access=field.access,
                owner=owner,
            )

        previous_scope = self.scope
        self.scope = class_scope
        self._analyze_block(info.decl.initializers)
        self.scope = previous_scope

        for method in info.methods.values():
            self._analyze_callable(method, parent_scope=class_scope)
        self.current_class = previous_class

    def _analyze_callable(
        self,
        declaration: ProcedureDecl | FunctionDecl | MethodDecl,
        *,
        parent_scope: _Scope | None = None,
    ) -> None:
        self._validate_parameters(declaration.params, declaration.span)
        previous_scope = self.scope
        previous_callable = self.current_callable
        self.scope = _Scope(parent_scope or self.global_scope)
        self.current_callable = declaration

        for parameter in declaration.params:
            self._define_symbol(
                self.scope,
                parameter.name,
                parameter.type_spec,
                initialized=True,
                span=parameter.span or declaration.span,
            )

        always_returns = self._analyze_block(declaration.body)
        if isinstance(declaration, FunctionDecl) or (
            isinstance(declaration, MethodDecl)
            and declaration.kind == T.FUNCTION
        ):
            if not always_returns:
                self._error(
                    "SEM011",
                    f"FUNCTION {declaration.name!r} may finish without RETURN",
                    declaration.span,
                )

        self.scope = previous_scope
        self.current_callable = previous_callable

    def _analyze_block(self, statements: list[Any]) -> bool:
        always_returns = False
        for statement in statements:
            if always_returns:
                self._warning("SEM014", "Unreachable statement", statement.span)
            statement_returns = self._analyze_statement(statement)
            always_returns = always_returns or statement_returns
        return always_returns

    def _analyze_statement(self, statement: Any) -> bool:
        if isinstance(statement, DeclareStmt):
            type_spec = self._resolve_type(statement.type_spec, statement.span)
            self._define_symbol(
                self.scope,
                statement.name,
                type_spec,
                initialized=not self.recommendations,
                span=statement.span,
            )
        elif isinstance(statement, ConstantStmt):
            value_type = self._expression_type(statement.expr)
            self._define_symbol(
                self.scope,
                statement.name,
                value_type,
                initialized=True,
                constant=True,
                span=statement.span,
            )
        elif isinstance(statement, DefineSetStmt):
            set_type = self._resolve_type(statement.type_spec, statement.span)
            element_type = self._set_element_type(set_type)
            for value in statement.values:
                self._require_assignable(
                    self._expression_type(value),
                    element_type,
                    value.span,
                    code="SEM004",
                    context="set element",
                )
            self._define_symbol(
                self.scope,
                statement.name,
                set_type,
                initialized=True,
                constant=True,
                span=statement.span,
            )
        elif isinstance(statement, AssignStmt):
            value_type = self._expression_type(statement.expr)
            target_type = self._target_type(
                statement.target,
                allow_inference=True,
                inferred_type=value_type,
            )
            self._require_assignable(
                value_type,
                target_type,
                statement.expr.span or statement.span,
                code="SEM004",
                context="assignment",
            )
            self._mark_initialized(statement.target)
        elif isinstance(statement, InputStmt):
            self._target_type(statement.target, allow_inference=False)
            self._mark_initialized(statement.target)
        elif isinstance(statement, OutputStmt):
            for expression in statement.exprs:
                self._expression_type(expression)
        elif isinstance(statement, OpenFileStmt):
            self._require_type(
                self._expression_type(statement.file_expr),
                T.STRING,
                statement.file_expr.span,
                "file identifier",
            )
        elif isinstance(statement, ReadFileStmt):
            self._require_type(
                self._expression_type(statement.file_expr),
                T.STRING,
                statement.file_expr.span,
                "file identifier",
            )
            target_type = self._target_type(statement.target, allow_inference=False)
            self._require_type(target_type, T.STRING, statement.target.span, "READFILE target")
            self._mark_initialized(statement.target)
        elif isinstance(statement, WriteFileStmt):
            self._require_type(
                self._expression_type(statement.file_expr),
                T.STRING,
                statement.file_expr.span,
                "file identifier",
            )
            self._expression_type(statement.data_expr)
        elif isinstance(statement, CloseFileStmt):
            self._require_type(
                self._expression_type(statement.file_expr),
                T.STRING,
                statement.file_expr.span,
                "file identifier",
            )
        elif isinstance(statement, SeekStmt):
            self._require_type(self._expression_type(statement.file_expr), T.STRING, statement.file_expr.span, "file identifier")
            self._require_type(self._expression_type(statement.address_expr), T.INTEGER, statement.address_expr.span, "SEEK address")
        elif isinstance(statement, GetRecordStmt):
            self._require_type(self._expression_type(statement.file_expr), T.STRING, statement.file_expr.span, "file identifier")
            self._target_type(statement.target, allow_inference=False)
            self._mark_initialized(statement.target)
        elif isinstance(statement, PutRecordStmt):
            self._require_type(self._expression_type(statement.file_expr), T.STRING, statement.file_expr.span, "file identifier")
            self._expression_type(statement.value_expr)
        elif isinstance(statement, IfStmt):
            self._require_boolean(statement.condition)
            then_returns = self._analyze_block(statement.then_body)
            else_returns = self._analyze_block(statement.else_body)
            return bool(statement.else_body) and then_returns and else_returns
        elif isinstance(statement, CaseStmt):
            selector_type = self._expression_type(statement.selector)
            clause_returns = []
            for clause in statement.clauses:
                start_type = self._expression_type(clause.start)
                if clause.end is not None:
                    self._require_comparable(
                        selector_type,
                        start_type,
                        clause.start.span,
                        ordered=True,
                    )
                    self._require_comparable(
                        selector_type,
                        self._expression_type(clause.end),
                        clause.end.span,
                        ordered=True,
                    )
                else:
                    self._require_comparable(
                        selector_type,
                        start_type,
                        clause.start.span,
                    )
                clause_returns.append(self._analyze_block(clause.body))
            otherwise_returns = self._analyze_block(statement.otherwise_body)
            return bool(statement.otherwise_body) and all(clause_returns) and otherwise_returns
        elif isinstance(statement, WhileStmt):
            self._require_boolean(statement.condition)
            self._analyze_block(statement.body)
        elif isinstance(statement, RepeatStmt):
            body_returns = self._analyze_block(statement.body)
            self._require_boolean(statement.condition)
            return body_returns
        elif isinstance(statement, ForStmt):
            symbol = self.scope.resolve(statement.var_name)
            if symbol is None:
                if self.strict:
                    self._error("SEM001", f"Undefined loop variable {statement.var_name!r}", statement.span)
                else:
                    self._define_symbol(self.scope, statement.var_name, T.INTEGER, initialized=True, span=statement.span)
            else:
                self._require_type(symbol.type_spec, T.INTEGER, statement.span, "FOR variable")
                symbol.initialized = True
            self._require_type(self._expression_type(statement.start), T.INTEGER, statement.start.span, "FOR start")
            self._require_type(self._expression_type(statement.end), T.INTEGER, statement.end.span, "FOR end")
            if statement.step is not None:
                self._require_type(self._expression_type(statement.step), T.INTEGER, statement.step.span, "FOR step")
            self._analyze_block(statement.body)
        elif isinstance(statement, CallStmt):
            self._analyze_procedure_call(statement.name, statement.args, statement.span)
        elif isinstance(statement, MethodCallStmt):
            self._method_call_type(statement.call, expression_context=False)
        elif isinstance(statement, ReturnStmt):
            return_type = self._expression_type(statement.expr)
            callable_decl = self.current_callable
            if callable_decl is None or isinstance(callable_decl, ProcedureDecl) or (
                isinstance(callable_decl, MethodDecl)
                and callable_decl.kind == T.PROCEDURE
            ):
                self._error("SEM012", "RETURN can only be used inside FUNCTION", statement.span)
            else:
                self._require_assignable(
                    return_type,
                    callable_decl.return_type,
                    statement.expr.span or statement.span,
                    code="SEM013",
                    context="return value",
                )
            return True
        return False

    def _expression_type(self, expression: Any) -> Any:
        if isinstance(expression, LiteralExpr):
            return _literal_type(expression.value)
        if isinstance(expression, VariableExpr):
            symbol = self.scope.resolve(expression.name)
            if symbol is not None:
                self._check_symbol_access(symbol, expression.span)
                if self.recommendations and not symbol.initialized:
                    self._warning(
                        "SEM003",
                        f"Variable {expression.name!r} is read before explicit assignment",
                        expression.span,
                    )
                return symbol.type_spec
            enum_type = self.enum_values.get(_norm(expression.name))
            if enum_type is not None:
                return enum_type
            self._error("SEM001", f"Undefined identifier {expression.name!r}", expression.span)
            return UNKNOWN
        if isinstance(expression, ArrayAccessExpr):
            return self._index_type(
                self._expression_type(expression.array_expr),
                expression.indices,
                expression.span,
            )
        if isinstance(expression, FieldAccessExpr):
            return self._field_type(
                self._expression_type(expression.record_expr),
                expression.field_name,
                expression.span,
            )
        if isinstance(expression, AddressOfExpr):
            if not self._is_writable_expression(expression.target_expr):
                self._error("SEM009", "Address-of operand must be a writable value", expression.span)
                return UNKNOWN
            return PointerType(self._lvalue_expression_type(expression.target_expr))
        if isinstance(expression, DerefExpr):
            pointer_type = self._expression_type(expression.pointer_expr)
            resolved = self._underlying_type(pointer_type, expression.span)
            if isinstance(resolved, PointerType):
                return self._resolve_type(resolved.target_type, expression.span)
            self._error("SEM010", "Dereference operand must be a POINTER", expression.span)
            return UNKNOWN
        if isinstance(expression, UnaryExpr):
            operand = self._expression_type(expression.right)
            if expression.op.type == T.NOT:
                self._require_type(operand, T.BOOLEAN, expression.span, "NOT operand")
                return T.BOOLEAN
            self._require_numeric(operand, expression.span, "unary '-' operand")
            return operand
        if isinstance(expression, BinaryExpr):
            return self._binary_type(expression)
        if isinstance(expression, CallExpr):
            return self._function_call_type(expression)
        if isinstance(expression, MethodCallExpr):
            return self._method_call_type(expression, expression_context=True)
        if isinstance(expression, NewExpr):
            info = self.classes.get(_norm(expression.class_name))
            if info is None:
                self._error("SEM015", f"Unknown CLASS {expression.class_name!r}", expression.span)
                for argument in expression.args:
                    self._expression_type(argument)
                return UNKNOWN
            constructor = info.methods.get(_norm("NEW"))
            if constructor is not None:
                self._check_private_access(
                    constructor.access,
                    info.decl.name,
                    "method",
                    constructor.name,
                    expression.span,
                )
            parameters = constructor.params if constructor is not None else []
            self._check_arguments("NEW", parameters, expression.args, expression.span)
            return UserTypeRef(info.decl.name)
        if isinstance(expression, SuperExpr):
            if self.current_class is None or self.current_class.parent_name is None:
                self._error("SEM010", "SUPER requires an inherited CLASS", expression.span)
                return UNKNOWN
            return UserTypeRef(self.current_class.parent_name)
        return UNKNOWN

    def _binary_type(self, expression: BinaryExpr) -> Any:
        left = self._expression_type(expression.left)
        right = self._expression_type(expression.right)
        operator = expression.op.type
        if operator in {T.AND, T.OR}:
            self._require_type(left, T.BOOLEAN, expression.left.span, "logical operand")
            self._require_type(right, T.BOOLEAN, expression.right.span, "logical operand")
            return T.BOOLEAN
        if operator == T.AMP:
            self._require_type(left, T.STRING, expression.left.span, "& operand")
            self._require_type(right, T.STRING, expression.right.span, "& operand")
            return T.STRING
        if operator in {T.EQUAL, T.NOT_EQUAL}:
            self._require_comparable(left, right, expression.span, ordered=False)
            return T.BOOLEAN
        if operator in {T.LESS, T.LESS_EQUAL, T.GREATER, T.GREATER_EQUAL}:
            self._require_comparable(left, right, expression.span, ordered=True)
            return T.BOOLEAN
        if operator in {T.DIV, T.MOD}:
            self._require_type(left, T.INTEGER, expression.left.span, f"{expression.op.lexeme} operand")
            self._require_type(right, T.INTEGER, expression.right.span, f"{expression.op.lexeme} operand")
            return T.INTEGER
        if operator == T.SLASH:
            self._require_numeric(left, expression.left.span, "/ operand")
            self._require_numeric(right, expression.right.span, "/ operand")
            return T.REAL
        if operator in {T.PLUS, T.MINUS} and self._is_enum_type(left) and _same_type(right, T.INTEGER):
            return left
        self._require_numeric(left, expression.left.span, "arithmetic operand")
        self._require_numeric(right, expression.right.span, "arithmetic operand")
        if _same_type(left, T.REAL) or _same_type(right, T.REAL):
            return T.REAL
        return T.INTEGER

    def _function_call_type(self, expression: CallExpr) -> Any:
        key = _norm(expression.name)
        if key in self.functions:
            declaration = self.functions[key]
            self._check_arguments(declaration.name, declaration.params, expression.args, expression.span)
            return self._resolve_type(declaration.return_type, declaration.span)
        if key in self.procedures:
            self._error("SEM006", f"PROCEDURE {expression.name!r} cannot be used as a FUNCTION", expression.span)
            for argument in expression.args:
                self._expression_type(argument)
            return UNKNOWN
        return self._builtin_call_type(expression)

    def _builtin_call_type(self, expression: CallExpr) -> Any:
        name = expression.name.upper()
        if name == "INT":
            if len(expression.args) != 1:
                self._error(
                    "SEM007",
                    f"INT expects 1 argument(s), got {len(expression.args)}",
                    expression.span,
                )
            for argument in expression.args:
                self._require_numeric(
                    self._expression_type(argument),
                    argument.span,
                    "INT argument",
                )
            return T.INTEGER
        if name in _BUILTINS:
            expected, result = _BUILTINS[name]
            parameters = [Param(f"argument {index + 1}", item, T.BYVAL) for index, item in enumerate(expected)]
            self._check_arguments(name, parameters, expression.args, expression.span)
            return result
        if name in _SET_QUERY_FUNCTIONS:
            self._check_set_arguments(name, expression.args, 1, expression.span)
            return _SET_QUERY_FUNCTIONS[name]
        if name == "CONTAINS":
            types = self._check_set_arguments(name, expression.args, 2, expression.span)
            if len(types) == 2:
                self._require_assignable(types[1], self._set_element_type(types[0]), expression.args[1].span, code="SEM008", context=f"{name} element")
            return T.BOOLEAN
        if name in _SET_BINARY_PREDICATES:
            self._check_set_arguments(name, expression.args, 2, expression.span, matching=True)
            return T.BOOLEAN
        if name in _SET_ALGEBRA:
            types = self._check_set_arguments(name, expression.args, 2, expression.span, matching=True)
            return types[0] if types else UNKNOWN
        self._error("SEM006", f"Unknown FUNCTION {expression.name!r}", expression.span)
        for argument in expression.args:
            self._expression_type(argument)
        return UNKNOWN

    def _analyze_procedure_call(self, name: str, arguments: list[Any], span: SourceSpan | None) -> None:
        key = _norm(name)
        if key in self.procedures:
            declaration = self.procedures[key]
            self._check_arguments(declaration.name, declaration.params, arguments, span)
            return
        if key in self.functions:
            self._error("SEM006", f"FUNCTION {name!r} cannot be called as a PROCEDURE", span)
            for argument in arguments:
                self._expression_type(argument)
            return
        upper = name.upper()
        if upper in _SET_PROCEDURES:
            required = 1 if upper == "SETCLEAR" else 2
            types = self._check_set_arguments(upper, arguments, required, span)
            if arguments and not self._is_writable_expression(arguments[0]):
                self._error("SEM009", f"{upper} first argument must be writable", arguments[0].span)
            if required == 2 and len(types) == 2:
                self._require_assignable(types[1], self._set_element_type(types[0]), arguments[1].span, code="SEM008", context=f"{upper} element")
            return
        self._error("SEM006", f"Unknown PROCEDURE {name!r}", span)
        for argument in arguments:
            self._expression_type(argument)

    def _method_call_type(self, expression: MethodCallExpr, *, expression_context: bool) -> Any:
        holder_type = self._expression_type(expression.object_expr)
        class_name = self._class_name(holder_type)
        if class_name is None:
            self._error("SEM010", "Method call target must be an object", expression.span)
            for argument in expression.args:
                self._expression_type(argument)
            return UNKNOWN
        method, owner = self._find_method(class_name, expression.method_name)
        if method is None or owner is None:
            self._error("SEM006", f"Class {class_name!r} has no method {expression.method_name!r}", expression.span)
            for argument in expression.args:
                self._expression_type(argument)
            return UNKNOWN
        self._check_private_access(
            method.access,
            owner,
            "method",
            method.name,
            expression.span,
        )
        is_function = method.kind == T.FUNCTION
        if expression_context and not is_function:
            self._error("SEM006", f"PROCEDURE method {expression.method_name!r} cannot be used as a FUNCTION", expression.span)
        if not expression_context and is_function:
            self._error("SEM006", f"FUNCTION method {expression.method_name!r} cannot be a statement", expression.span)
        self._check_arguments(method.name, method.params, expression.args, expression.span)
        return self._resolve_type(method.return_type, method.span) if is_function else UNKNOWN

    def _check_arguments(self, name: str, parameters: list[Param], arguments: list[Any], span: SourceSpan | None) -> None:
        if len(arguments) != len(parameters):
            self._error("SEM007", f"{name} expects {len(parameters)} argument(s), got {len(arguments)}", span)
        for parameter, argument in zip(parameters, arguments):
            argument_type = self._expression_type(argument)
            parameter_type = self._resolve_type(parameter.type_spec, parameter.span or span)
            if parameter.passing == T.BYREF:
                if not _is_lvalue_expression(argument) or not self._is_writable_expression(argument):
                    self._error("SEM009", f"BYREF argument for {parameter.name!r} must be a writable lvalue", argument.span)
                elif not self._types_equal(
                    argument_type,
                    parameter_type,
                    argument.span,
                ):
                    self._error("SEM009", f"BYREF argument for {parameter.name!r} has type {_type_name(argument_type)}, expected {_type_name(parameter_type)}", argument.span)
            else:
                self._require_assignable(argument_type, parameter_type, argument.span, code="SEM008", context=f"argument {parameter.name!r}")
        for argument in arguments[len(parameters):]:
            self._expression_type(argument)

    def _check_set_arguments(self, name: str, arguments: list[Any], count: int, span: SourceSpan | None, *, matching: bool = False) -> list[Any]:
        if len(arguments) != count:
            self._error("SEM007", f"{name} expects {count} argument(s), got {len(arguments)}", span)
        types = [self._expression_type(argument) for argument in arguments]
        if types and self._set_element_type(types[0]) is UNKNOWN:
            self._error("SEM008", f"{name} requires a SET argument", arguments[0].span)
        if matching and len(types) >= 2 and not self._types_equal(
            types[0],
            types[1],
            arguments[1].span,
        ):
            self._error("SEM008", f"{name} requires SET arguments of the same type", arguments[1].span)
        return types

    def _target_type(self, target: Any, *, allow_inference: bool, inferred_type: Any = UNKNOWN) -> Any:
        if isinstance(target, VarTarget):
            symbol = self.scope.resolve(target.name)
            if symbol is None:
                if allow_inference and not self.strict:
                    self._define_symbol(self.scope, target.name, inferred_type, initialized=True, span=target.span)
                    return inferred_type
                self._error("SEM001", f"Undefined variable {target.name!r}", target.span)
                return UNKNOWN
            if symbol.constant:
                self._error("SEM004", f"Cannot assign to constant {target.name!r}", target.span)
            self._check_symbol_access(symbol, target.span)
            return symbol.type_spec
        if isinstance(target, ArrayTarget):
            symbol = self.scope.resolve(target.name)
            if symbol is None:
                self._error("SEM001", f"Undefined variable {target.name!r}", target.span)
                return UNKNOWN
            if symbol.constant:
                self._error("SEM004", f"Cannot assign to constant {target.name!r}", target.span)
            self._check_symbol_access(symbol, target.span)
            return self._index_type(symbol.type_spec, target.indices, target.span)
        if isinstance(target, IndexTarget):
            return self._index_type(self._expression_type(target.array_expr), target.indices, target.span)
        if isinstance(target, FieldTarget):
            return self._field_type(self._expression_type(target.record_expr), target.field_name, target.span)
        if isinstance(target, DerefTarget):
            pointer_type = self._underlying_type(
                self._expression_type(target.pointer_expr),
                target.span,
            )
            if isinstance(pointer_type, PointerType):
                return self._resolve_type(pointer_type.target_type, target.span)
            self._error("SEM010", "Dereference target must be a POINTER", target.span)
        return UNKNOWN

    def _index_type(self, holder_type: Any, indices: list[Any], span: SourceSpan | None) -> Any:
        resolved = self._resolve_type(holder_type, span)
        for index in indices:
            self._require_type(self._expression_type(index), T.INTEGER, index.span, "array index")
        if not isinstance(resolved, ArrayType):
            self._error("SEM010", "Indexed value is not an ARRAY", span)
            return UNKNOWN
        if len(indices) != len(resolved.bounds):
            self._error("SEM010", f"ARRAY expects {len(resolved.bounds)} index(es), got {len(indices)}", span)
        return self._resolve_type(resolved.element_type, span)

    def _field_type(self, holder_type: Any, field_name: str, span: SourceSpan | None) -> Any:
        resolved = self._resolve_type(holder_type, span)
        name = self._user_type_name(resolved)
        if name is None:
            self._error("SEM010", "Field access target is not a record or object", span)
            return UNKNOWN
        declaration = self.types.get(_norm(name))
        if isinstance(declaration, TypeDeclRecord):
            for field in declaration.fields:
                if _norm(field.name) == _norm(field_name):
                    return self._resolve_type(field.type_spec, field.span or span)
            self._error("SEM010", f"Record {name!r} has no field {field_name!r}", span)
            return UNKNOWN
        field, owner = self._find_field(name, field_name)
        if field is not None and owner is not None:
            self._check_private_access(
                field.access,
                owner,
                "property",
                field.name,
                span,
            )
            return self._resolve_type(field.type_spec, field.span or span)
        self._error("SEM010", f"Class {name!r} has no property {field_name!r}", span)
        return UNKNOWN

    def _lvalue_expression_type(self, expression: Any) -> Any:
        if isinstance(expression, VariableExpr):
            return self._expression_type(expression)
        if isinstance(expression, ArrayAccessExpr):
            return self._expression_type(expression)
        if isinstance(expression, FieldAccessExpr):
            return self._expression_type(expression)
        if isinstance(expression, DerefExpr):
            return self._expression_type(expression)
        return UNKNOWN

    def _is_writable_expression(self, expression: Any) -> bool:
        if isinstance(expression, VariableExpr):
            symbol = self.scope.resolve(expression.name)
            return symbol is not None and not symbol.constant
        if isinstance(expression, ArrayAccessExpr):
            return self._is_writable_expression(expression.array_expr)
        if isinstance(expression, FieldAccessExpr):
            return self._is_writable_expression(expression.record_expr)
        if isinstance(expression, DerefExpr):
            return True
        return False

    def _mark_initialized(self, target: Any) -> None:
        if isinstance(target, VarTarget):
            symbol = self.scope.resolve(target.name)
            if symbol is not None:
                symbol.initialized = True

    def _define_symbol(
        self,
        scope: _Scope,
        name: str,
        type_spec: Any,
        *,
        initialized: bool,
        span: SourceSpan | None,
        constant: bool = False,
        access: str | None = None,
        owner: str | None = None,
    ) -> None:
        key = _norm(name)
        if key in scope.symbols:
            self._error("SEM002", f"Identifier {name!r} is already declared", span)
            return
        scope.symbols[key] = _Symbol(
            name,
            self._resolve_type(type_spec, span),
            initialized,
            constant,
            access,
            owner,
        )

    def _resolve_type(self, type_spec: Any, span: SourceSpan | None) -> Any:
        if type_spec is UNKNOWN or type_spec is None:
            return UNKNOWN
        if isinstance(type_spec, str):
            return type_spec
        if isinstance(type_spec, ArrayType):
            return ArrayType(type_spec.bounds, self._resolve_type(type_spec.element_type, span))
        if isinstance(type_spec, PointerType):
            return PointerType(self._resolve_type(type_spec.target_type, span))
        if isinstance(type_spec, SetTypeSpec):
            return SetTypeSpec(self._resolve_type(type_spec.element_type, span))
        if isinstance(type_spec, UserTypeRef):
            key = _norm(type_spec.name)
            declaration = self.types.get(key)
            class_info = self.classes.get(key)
            if declaration is None and class_info is None:
                self._error("SEM015", f"Unknown TYPE {type_spec.name!r}", span)
                return UNKNOWN
            canonical = declaration.name if declaration is not None else class_info.decl.name
            return UserTypeRef(canonical)
        return type_spec

    def _require_assignable(self, source: Any, target: Any, span: SourceSpan | None, *, code: str, context: str) -> None:
        source = self._resolve_type(source, span)
        target = self._resolve_type(target, span)
        if source is UNKNOWN or target is UNKNOWN:
            return
        if self._types_equal(source, target, span):
            return
        if _same_type(source, T.INTEGER) and _same_type(target, T.REAL):
            return
        source_class = self._class_name(source)
        target_class = self._class_name(target)
        if source_class and target_class and self._class_inherits(source_class, target_class):
            return
        self._error(code, f"Incompatible {context}: {_type_name(source)} cannot be used as {_type_name(target)}", span)

    def _require_type(self, actual: Any, expected: Any, span: SourceSpan | None, context: str) -> None:
        actual = self._resolve_type(actual, span)
        expected = self._resolve_type(expected, span)
        if actual is UNKNOWN or expected is UNKNOWN or _same_type(actual, expected):
            return
        self._error("SEM005", f"{context} must be {_type_name(expected)}, got {_type_name(actual)}", span)

    def _require_numeric(self, actual: Any, span: SourceSpan | None, context: str) -> None:
        if actual is UNKNOWN or _same_type(actual, T.INTEGER) or _same_type(actual, T.REAL):
            return
        self._error("SEM005", f"{context} must be numeric, got {_type_name(actual)}", span)

    def _require_boolean(self, expression: Any) -> None:
        self._require_type(self._expression_type(expression), T.BOOLEAN, expression.span, "condition")

    def _require_comparable(
        self,
        left: Any,
        right: Any,
        span: SourceSpan | None,
        *,
        ordered: bool = False,
    ) -> None:
        if left is UNKNOWN or right is UNKNOWN:
            return
        if {_type_name(left), _type_name(right)} <= {T.INTEGER, T.REAL}:
            return
        if not self._types_equal(left, right, span):
            self._error(
                "SEM005",
                f"Cannot compare {_type_name(left)} with {_type_name(right)}",
                span,
            )
            return

        resolved = self._underlying_type(left, span)
        scalar_ordered = {T.CHAR, T.STRING, T.DATE}
        scalar_equal = scalar_ordered | {T.BOOLEAN}
        valid = _type_name(resolved) in (
            scalar_ordered if ordered else scalar_equal
        )
        valid = valid or self._is_enum_type(left)
        if not ordered:
            valid = valid or isinstance(resolved, (PointerType, SetTypeSpec))
            valid = valid or self._class_name(left) is not None
            valid = valid or self._set_element_type(left) is not UNKNOWN
        if not valid:
            qualifier = "order" if ordered else "compare"
            self._error(
                "SEM005",
                f"Cannot {qualifier} values of type {_type_name(left)}",
                span,
            )

    def _underlying_type(
        self,
        type_spec: Any,
        span: SourceSpan | None,
    ) -> Any:
        resolved = self._resolve_type(type_spec, span)
        name = self._user_type_name(resolved)
        declaration = self.types.get(_norm(name)) if name else None
        if isinstance(declaration, TypeDeclPointer):
            return PointerType(
                self._resolve_type(
                    declaration.target_type,
                    declaration.span or span,
                )
            )
        if isinstance(declaration, TypeDeclSet):
            return SetTypeSpec(
                self._resolve_type(
                    declaration.element_type,
                    declaration.span or span,
                )
            )
        return resolved

    def _types_equal(
        self,
        left: Any,
        right: Any,
        span: SourceSpan | None,
    ) -> bool:
        left = self._resolve_type(left, span)
        right = self._resolve_type(right, span)
        if _same_type(left, right):
            return True
        left_underlying = self._underlying_type(left, span)
        right_underlying = self._underlying_type(right, span)
        if isinstance(left_underlying, PointerType) and isinstance(
            right_underlying,
            PointerType,
        ):
            return _same_type(left_underlying, right_underlying)
        return False

    def _set_element_type(self, type_spec: Any) -> Any:
        resolved = self._resolve_type(type_spec, None)
        if isinstance(resolved, SetTypeSpec):
            return resolved.element_type
        name = self._user_type_name(resolved)
        declaration = self.types.get(_norm(name)) if name else None
        if isinstance(declaration, TypeDeclSet):
            return self._resolve_type(declaration.element_type, declaration.span)
        return UNKNOWN

    def _valid_set_element_type(self, type_spec: Any) -> bool:
        resolved = self._resolve_type(type_spec, None)
        if resolved is UNKNOWN:
            return True
        if isinstance(resolved, (ArrayType, PointerType, SetTypeSpec)):
            return False
        name = self._user_type_name(resolved)
        if name is None:
            return True
        declaration = self.types.get(_norm(name))
        return isinstance(declaration, TypeDeclEnum)

    def _record_contains(
        self,
        type_spec: Any,
        target_name: str,
        seen: set[str],
    ) -> bool:
        if isinstance(type_spec, ArrayType):
            return self._record_contains(
                type_spec.element_type,
                target_name,
                seen,
            )
        if isinstance(type_spec, PointerType):
            return False
        if not isinstance(type_spec, UserTypeRef):
            return False
        key = _norm(type_spec.name)
        if key == _norm(target_name):
            return True
        if key in seen:
            return False
        declaration = self.types.get(key)
        if isinstance(declaration, TypeDeclPointer):
            return False
        if not isinstance(declaration, TypeDeclRecord):
            return False
        next_seen = seen | {key}
        return any(
            self._record_contains(field.type_spec, target_name, next_seen)
            for field in declaration.fields
        )

    def _is_enum_type(self, type_spec: Any) -> bool:
        name = self._user_type_name(type_spec)
        return isinstance(self.types.get(_norm(name)) if name else None, TypeDeclEnum)

    def _user_type_name(self, type_spec: Any) -> str | None:
        return type_spec.name if isinstance(type_spec, UserTypeRef) else None

    def _class_name(self, type_spec: Any) -> str | None:
        name = self._user_type_name(self._resolve_type(type_spec, None))
        return name if name is not None and _norm(name) in self.classes else None

    def _all_class_fields(
        self,
        class_name: str,
        seen: set[str] | None = None,
    ) -> dict[str, ClassFieldDecl]:
        seen = set() if seen is None else seen
        key = _norm(class_name)
        if key in seen:
            return {}
        seen.add(key)
        info = self.classes.get(key)
        if info is None:
            return {}
        fields: dict[str, ClassFieldDecl] = {}
        if info.decl.parent_name is not None:
            fields.update(self._all_class_fields(info.decl.parent_name, seen))
        fields.update(info.fields)
        return fields

    def _find_field(
        self,
        class_name: str,
        field_name: str,
        seen: set[str] | None = None,
    ) -> tuple[ClassFieldDecl | None, str | None]:
        seen = set() if seen is None else seen
        key = _norm(class_name)
        if key in seen:
            return None, None
        seen.add(key)
        info = self.classes.get(key)
        if info is None:
            return None, None
        field = info.fields.get(_norm(field_name))
        if field is not None:
            return field, info.decl.name
        if info.decl.parent_name is not None:
            return self._find_field(info.decl.parent_name, field_name, seen)
        return None, None

    def _find_method(
        self,
        class_name: str,
        method_name: str,
        seen: set[str] | None = None,
    ) -> tuple[MethodDecl | None, str | None]:
        seen = set() if seen is None else seen
        key = _norm(class_name)
        if key in seen:
            return None, None
        seen.add(key)
        info = self.classes.get(key)
        if info is None:
            return None, None
        method = info.methods.get(_norm(method_name))
        if method is not None:
            return method, info.decl.name
        if info.decl.parent_name is not None:
            return self._find_method(info.decl.parent_name, method_name, seen)
        return None, None

    def _check_private_access(
        self,
        access: str,
        owner: str,
        member_kind: str,
        name: str,
        span: SourceSpan | None,
    ) -> None:
        if access != T.PRIVATE:
            return
        if (
            self.current_class is not None
            and _norm(self.current_class.name) == _norm(owner)
        ):
            return
        self._error(
            "SEM010",
            f"Cannot access PRIVATE {member_kind} {name!r} "
            f"of CLASS {owner!r}",
            span,
        )

    def _check_symbol_access(
        self,
        symbol: _Symbol,
        span: SourceSpan | None,
    ) -> None:
        if symbol.access is None or symbol.owner is None:
            return
        self._check_private_access(
            symbol.access,
            symbol.owner,
            "property",
            symbol.name,
            span,
        )

    def _class_inherits(self, source: str, target: str) -> bool:
        seen: set[str] = set()
        current = source
        while _norm(current) not in seen:
            if _norm(current) == _norm(target):
                return True
            seen.add(_norm(current))
            info = self.classes.get(_norm(current))
            if info is None or info.decl.parent_name is None:
                return False
            current = info.decl.parent_name
        return False

    def _error(self, code: str, message: str, span: SourceSpan | None) -> None:
        self._diagnostic(code, "error", message, span)

    def _warning(self, code: str, message: str, span: SourceSpan | None) -> None:
        self._diagnostic(code, "warning", message, span)

    def _diagnostic(self, code: str, severity: str, message: str, span: SourceSpan | None) -> None:
        location = span or SourceSpan(1, 1)
        self.diagnostics.append(SemanticDiagnostic(code, severity, message, location.line, location.col))


def _norm(name: str | None) -> str:
    return name.casefold() if name is not None else ""


def _literal_type(value: Any) -> Any:
    if type(value) is bool:
        return T.BOOLEAN
    if type(value) is int:
        return T.INTEGER
    if type(value) is float:
        return T.REAL
    if isinstance(value, Char):
        return T.CHAR
    if type(value) is str:
        return T.STRING
    if isinstance(value, DateValue):
        return T.DATE
    return UNKNOWN


def _same_type(left: Any, right: Any) -> bool:
    if left is UNKNOWN or right is UNKNOWN:
        return True
    if isinstance(left, str) and isinstance(right, str):
        return left.upper() == right.upper()
    if isinstance(left, UserTypeRef) and isinstance(right, UserTypeRef):
        return _norm(left.name) == _norm(right.name)
    if isinstance(left, ArrayType) and isinstance(right, ArrayType):
        return left.bounds == right.bounds and _same_type(left.element_type, right.element_type)
    if isinstance(left, PointerType) and isinstance(right, PointerType):
        return _same_type(left.target_type, right.target_type)
    if isinstance(left, SetTypeSpec) and isinstance(right, SetTypeSpec):
        return _same_type(left.element_type, right.element_type)
    return False


def _type_name(type_spec: Any) -> str:
    if type_spec is UNKNOWN:
        return "UNKNOWN"
    if isinstance(type_spec, str):
        return type_spec
    if isinstance(type_spec, UserTypeRef):
        return type_spec.name
    if isinstance(type_spec, ArrayType):
        return f"ARRAY OF {_type_name(type_spec.element_type)}"
    if isinstance(type_spec, PointerType):
        return f"^{_type_name(type_spec.target_type)}"
    if isinstance(type_spec, SetTypeSpec):
        return f"SET OF {_type_name(type_spec.element_type)}"
    return str(type_spec)


def _is_lvalue_expression(expression: Any) -> bool:
    return isinstance(
        expression,
        (VariableExpr, ArrayAccessExpr, FieldAccessExpr, DerefExpr),
    )


__all__ = [
    "SEMANTIC_CODES",
    "SemanticDiagnostic",
    "SemanticReport",
    "analyze_file",
    "analyze_program",
    "analyze_source",
]
