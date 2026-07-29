from __future__ import annotations

import re
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
    NewExpr,
    OpenFileStmt,
    OutputStmt,
    PointerType,
    ProcedureDecl,
    Program,
    PutRecordStmt,
    ReadFileStmt,
    RepeatStmt,
    ReturnStmt,
    SeekStmt,
    SuperExpr,
    TypeDeclEnum,
    TypeDeclPointer,
    TypeDeclRecord,
    TypeDeclSet,
    UnaryExpr,
    VariableExpr,
    VarTarget,
    WhileStmt,
    WriteFileStmt,
)
from .errors import PseudoRuntimeError
from .runtime import (
    ArrayValue,
    ClassType,
    EnumValue,
    NullObjectValue,
    ObjectValue,
    PointerValue,
    RecordValue,
    Reference,
    SetType,
    SetValue,
    SuperProxy,
    Runtime,
    coerce_value,
    make_set_value,
    norm_identifier,
    output_value,
    runtime_type_name,
    same_type,
    type_to_str,
)
from .tokens import T
from .values import Char, DateValue, make_date


class ReturnSignal(Exception):
    def __init__(self, value: Any, span: Any = None):
        super().__init__()
        self.value = value
        self.span = span


class Interpreter:
    SET_BUILTIN_PROCEDURES = {
        "SETADD",
        "SETREMOVE",
        "SETDISCARD",
        "SETCLEAR",
    }

    def __init__(self, runtime: Runtime):
        self.runtime = runtime
        self.method_context: list[tuple[ObjectValue, Any]] = []

    @property
    def env(self):
        return self.runtime.env

    def execute_program(self, program: Program):
        for stmt in program.statements:
            if isinstance(stmt, TypeDeclRecord):
                self.runtime.reserve_record_type(stmt.name)

        for stmt in program.statements:
            if isinstance(stmt, ClassDecl):
                self.runtime.reserve_class_type(stmt.name, stmt.parent_name)

        for stmt in program.statements:
            if isinstance(stmt, TypeDeclEnum):
                self.execute(stmt)

        for stmt in program.statements:
            if isinstance(stmt, (TypeDeclPointer, TypeDeclSet)):
                self.execute(stmt)

        for stmt in program.statements:
            if isinstance(stmt, TypeDeclRecord):
                self.execute(stmt)

        self.execute_class_declarations(
            [
                stmt
                for stmt in program.statements
                if isinstance(stmt, ClassDecl)
            ]
        )

        for stmt in program.statements:
            if isinstance(stmt, (ProcedureDecl, FunctionDecl)):
                self.execute(stmt)

        declaration_types = (
            TypeDeclEnum,
            TypeDeclPointer,
            TypeDeclRecord,
            TypeDeclSet,
            ClassDecl,
            ProcedureDecl,
            FunctionDecl,
        )

        for stmt in program.statements:
            if isinstance(stmt, declaration_types):
                continue

            try:
                self.execute(stmt)

            except ReturnSignal as signal:
                err = PseudoRuntimeError("RETURN can only be used inside FUNCTION")

                if signal.span is not None:
                    raise err.with_location(signal.span.line, signal.span.col) from None

                raise err from None

    def execute_class_declarations(self, declarations: list[ClassDecl]):
        pending = {
            norm_identifier(decl.name): decl
            for decl in declarations
        }

        while pending:
            progressed = False

            for key, decl in list(pending.items()):
                parent_name = decl.parent_name

                if (
                    parent_name is None
                    or norm_identifier(parent_name) not in pending
                ):
                    self.execute(decl)
                    del pending[key]
                    progressed = True

            if progressed:
                continue

            # If every remaining class depends on another remaining class, the
            # declarations contain an inheritance cycle. Register one of them so
            # Runtime can report a deterministic error.
            key, decl = next(iter(pending.items()))
            self.execute(decl)
            del pending[key]

    def execute_block(self, statements: list[Any]):
        for stmt in statements:
            self.execute(stmt)

    def execute(self, stmt: Any):
        try:
            self.runtime.tick()
            return self._execute(stmt)

        except PseudoRuntimeError as err:
            if err.line is None:
                span = getattr(stmt, "span", None)

                if span is not None:
                    raise err.with_location(span.line, span.col) from None

            raise

    def _execute(self, stmt: Any):
        if isinstance(stmt, TypeDeclEnum):
            self.runtime.register_enum_type(stmt.name, stmt.values)
            return

        if isinstance(stmt, TypeDeclPointer):
            self.runtime.register_pointer_type(stmt.name, stmt.target_type)
            return

        if isinstance(stmt, TypeDeclSet):
            self.runtime.register_set_type(stmt.name, stmt.element_type)
            return

        if isinstance(stmt, TypeDeclRecord):
            self.runtime.register_record_type(stmt.name, stmt.fields)
            return

        if isinstance(stmt, ClassDecl):
            self.runtime.register_class_type(stmt)
            return

        if isinstance(stmt, DeclareStmt):
            type_spec = self.runtime.resolve_type_spec(stmt.type_spec)
            self.env.define(stmt.name, type_spec)
            return

        if isinstance(stmt, ConstantStmt):
            value = self.eval(stmt.expr)
            self.env.define_constant(stmt.name, value)
            return

        if isinstance(stmt, DefineSetStmt):
            type_spec = self.runtime.resolve_type_spec(stmt.type_spec)

            if not isinstance(type_spec, SetType):
                raise PseudoRuntimeError(
                    f"DEFINE target type must be SET, got {type_to_str(type_spec)}"
                )

            values = [
                self.eval(expr)
                for expr in stmt.values
            ]
            self.env.define(
                stmt.name,
                type_spec,
                make_set_value(type_spec, values),
                constant=True,
            )
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

            self.runtime.output("".join(values))
            return

        if isinstance(stmt, OpenFileStmt):
            file_id = self.eval_file_identifier(stmt.file_expr)
            self.runtime.file_system.open_file(file_id, stmt.mode)
            return

        if isinstance(stmt, ReadFileStmt):
            file_id = self.eval_file_identifier(stmt.file_expr)
            type_spec = self.target_type(stmt.target)

            if not same_type(type_spec, T.STRING):
                raise PseudoRuntimeError(
                    f"READFILE target must be STRING, got {type_to_str(type_spec)}"
                )

            line = self.runtime.file_system.read_file(file_id)
            self.assign_target(stmt.target, line)
            return

        if isinstance(stmt, WriteFileStmt):
            file_id = self.eval_file_identifier(stmt.file_expr)
            data = output_value(self.eval(stmt.data_expr))
            self.runtime.file_system.write_file(file_id, data)
            return

        if isinstance(stmt, CloseFileStmt):
            file_id = self.eval_file_identifier(stmt.file_expr)
            self.runtime.file_system.close_file(file_id)
            return

        if isinstance(stmt, SeekStmt):
            file_id = self.eval_file_identifier(stmt.file_expr)
            address = self.require_int(self.eval(stmt.address_expr))
            self.runtime.file_system.seek(file_id, address)
            return

        if isinstance(stmt, GetRecordStmt):
            file_id = self.eval_file_identifier(stmt.file_expr)
            value = self.runtime.file_system.get_record(file_id)
            self.assign_target(stmt.target, value)
            return

        if isinstance(stmt, PutRecordStmt):
            file_id = self.eval_file_identifier(stmt.file_expr)
            value = self.eval(stmt.value_expr)
            self.runtime.file_system.put_record(file_id, value)
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
                self.runtime.tick()
                self.execute_block(stmt.body)

            return

        if isinstance(stmt, RepeatStmt):
            while True:
                self.runtime.tick()
                self.execute_block(stmt.body)

                if self.require_bool(self.eval(stmt.condition)):
                    break

            return

        if isinstance(stmt, ForStmt):
            self.execute_for(stmt)
            return

        if isinstance(stmt, ProcedureDecl):
            self.runtime.register_procedure(stmt)
            return

        if isinstance(stmt, FunctionDecl):
            self.runtime.register_function(stmt)
            return

        if isinstance(stmt, CallStmt):
            self.call_procedure(stmt.name, stmt.args)
            return

        if isinstance(stmt, MethodCallStmt):
            self.call_method_expression(stmt.call, expression_context=False)
            return

        if isinstance(stmt, ReturnStmt):
            value = self.eval(stmt.expr)
            raise ReturnSignal(value, stmt.span)

        raise PseudoRuntimeError(f"Unknown statement type: {stmt!r}")

    def eval_file_identifier(self, expr: Any) -> str:
        return self.require_string(self.eval(expr))

    def create_object(self, class_name: str, arg_exprs: list[Any]) -> ObjectValue:
        class_type = self.runtime.get_class(class_name)
        constructor = class_type.methods.get(norm_identifier("NEW"))
        prepared_constructor = None

        if constructor is None:
            if arg_exprs:
                raise PseudoRuntimeError(
                    f"CLASS {class_name!r} has no constructor accepting arguments"
                )
        else:
            if constructor.kind != T.PROCEDURE:
                raise PseudoRuntimeError("Constructor NEW must be a PROCEDURE")

            self.ensure_method_access(class_type, constructor)

            prepared_constructor = self.prepare_arguments(
                constructor.params,
                arg_exprs,
                f"CONSTRUCTOR {class_name}.NEW",
            )

        obj = ObjectValue.create(
            class_type,
            max_array_elements=self.runtime.max_array_elements,
        )
        self.run_class_initializers(obj, class_type)

        if constructor is not None:
            self.call_method(
                obj,
                "NEW",
                [],
                start_class=class_type,
                context=f"CONSTRUCTOR {class_name}.NEW",
                prepared=prepared_constructor,
            )

        return obj

    def run_class_initializers(self, obj: ObjectValue, class_type: Any):
        if class_type.parent is not None:
            self.run_class_initializers(obj, class_type.parent)

        if not class_type.initializers:
            return

        with self.runtime.scope(f"CLASS {class_type.name} initializers"):
            self.bind_object_fields(obj)

            self.method_context.append((obj, class_type))

            try:
                self.execute_block(class_type.initializers)

            except ReturnSignal as signal:
                err = PseudoRuntimeError(
                    "RETURN cannot be used in CLASS property initializers"
                )

                if signal.span is not None:
                    raise err.with_location(signal.span.line, signal.span.col) from None

                raise err from None

            finally:
                self.method_context.pop()

    def bind_object_fields(self, obj: ObjectValue):
        for _key, spec in obj.type_spec.all_fields().items():
            if self.env.exists_local(spec.original_name):
                continue

            self.env.define_reference(
                spec.original_name,
                spec.type_spec,
                Reference(
                    type_spec=spec.type_spec,
                    getter=lambda obj=obj, name=spec.original_name: (
                        self.get_object_field(obj, name)
                    ),
                    setter=lambda value, obj=obj, name=spec.original_name: (
                        self.set_object_field(obj, name, value)
                    ),
                    description=f"{obj.type_spec.name}.{spec.original_name}",
                ),
            )

    def private_access_allowed(self, owner_name: str) -> bool:
        if not self.method_context:
            return False

        _obj, current_class = self.method_context[-1]
        return norm_identifier(current_class.name) == norm_identifier(owner_name)

    def ensure_member_access(
        self,
        access: str,
        owner_name: str,
        description: str,
    ):
        if access != T.PRIVATE:
            return

        if owner_name and self.private_access_allowed(owner_name):
            return

        raise PseudoRuntimeError(f"Cannot access PRIVATE {description}")

    def get_object_field(self, obj: ObjectValue, field_name: str) -> Any:
        spec = obj.type_spec.get_field(field_name)
        owner_name = spec.owner_name or obj.type_spec.name

        self.ensure_member_access(
            spec.access,
            owner_name,
            f"property {field_name!r} of CLASS {owner_name!r}",
        )

        return obj.get(field_name)

    def set_object_field(self, obj: ObjectValue, field_name: str, value: Any):
        spec = obj.type_spec.get_field(field_name)
        owner_name = spec.owner_name or obj.type_spec.name

        self.ensure_member_access(
            spec.access,
            owner_name,
            f"property {field_name!r} of CLASS {owner_name!r}",
        )

        obj.set(field_name, value)

    def object_field_type(self, obj: ObjectValue, field_name: str) -> Any:
        spec = obj.type_spec.get_field(field_name)
        owner_name = spec.owner_name or obj.type_spec.name

        self.ensure_member_access(
            spec.access,
            owner_name,
            f"property {field_name!r} of CLASS {owner_name!r}",
        )

        return spec.type_spec

    def ensure_method_access(self, owner_class: ClassType, method: Any):
        self.ensure_member_access(
            method.access,
            owner_class.name,
            f"method {method.name!r} of CLASS {owner_class.name!r}",
        )

    def eval_super(self) -> SuperProxy:
        if not self.method_context:
            raise PseudoRuntimeError("SUPER can only be used inside a method")

        obj, current_class = self.method_context[-1]

        if current_class.parent is None:
            raise PseudoRuntimeError(
                f"CLASS {current_class.name!r} has no superclass"
            )

        return SuperProxy(obj, current_class.parent)

    def call_method_expression(
        self,
        expr: Any,
        *,
        expression_context: bool,
    ) -> Any:
        target = self.eval(expr.object_expr)

        if isinstance(target, SuperProxy):
            obj = target.object_value
            start_class = target.start_class

        elif isinstance(target, ObjectValue):
            obj = target
            start_class = obj.type_spec

        elif isinstance(target, NullObjectValue):
            raise PseudoRuntimeError(
                f"Object reference of type {target.type_spec.name!r} "
                "is not initialised"
            )

        else:
            raise PseudoRuntimeError(
                f"Method call target must be an object, got {runtime_type_name(target)}"
            )

        method, owner_class = start_class.find_method(expr.method_name)

        if method is None or owner_class is None:
            raise PseudoRuntimeError(
                f"CLASS {start_class.name!r} has no method {expr.method_name!r}"
            )

        if method.kind == T.PROCEDURE and expression_context:
            raise PseudoRuntimeError(
                f"PROCEDURE method {expr.method_name!r} cannot be used as a FUNCTION"
            )

        if method.kind == T.FUNCTION and not expression_context:
            raise PseudoRuntimeError(
                f"FUNCTION method {expr.method_name!r} cannot be used as a statement"
            )

        value, _kind = self.call_method(
            obj,
            expr.method_name,
            expr.args,
            start_class=start_class,
            context=f"METHOD {start_class.name}.{expr.method_name}",
        )

        return value

    def call_method(
        self,
        obj: ObjectValue,
        method_name: str,
        arg_exprs: list[Any],
        *,
        start_class: Any,
        context: str,
        prepared: list[tuple[str, str, Any, Any]] | None = None,
    ) -> tuple[Any, str]:
        method, owner_class = start_class.find_method(method_name)

        if method is None or owner_class is None:
            raise PseudoRuntimeError(
                f"CLASS {start_class.name!r} has no method {method_name!r}"
            )

        self.ensure_method_access(owner_class, method)

        if prepared is None:
            prepared = self.prepare_arguments(
                method.params,
                arg_exprs,
                context,
            )

        return_type = (
            self.runtime.resolve_type_spec(method.return_type)
            if method.return_type is not None
            else None
        )

        with self.runtime.call_frame(context):
            with self.runtime.scope(context):
                self.bind_prepared_arguments(prepared)
                self.bind_object_fields(obj)

                self.method_context.append((obj, owner_class))

                try:
                    self.execute_block(method.body)

                except ReturnSignal as signal:
                    if method.kind != T.FUNCTION:
                        err = PseudoRuntimeError(
                            "RETURN cannot be used in a PROCEDURE method"
                        )

                        if signal.span is not None:
                            raise err.with_location(
                                signal.span.line,
                                signal.span.col,
                            ) from None

                        raise err from None

                    return coerce_value(signal.value, return_type), method.kind

                finally:
                    self.method_context.pop()

        if method.kind == T.FUNCTION:
            raise PseudoRuntimeError(
                f"FUNCTION method {method.name!r} did not RETURN a value"
            )

        return None, method.kind

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
            return self.equal_values(selector, start)

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
            self.runtime.tick()
            self.env.assign(stmt.var_name, i)
            self.execute_block(stmt.body)
            i += step

    def call_procedure(self, name: str, arg_exprs: list[Any]):
        upper = name.upper()

        if (
            not self.runtime.has_procedure(name)
            and upper in self.SET_BUILTIN_PROCEDURES
        ):
            self.call_set_builtin_procedure(upper, arg_exprs)
            return

        decl = self.runtime.get_procedure(name)
        context = f"PROCEDURE {decl.name}"
        prepared = self.prepare_arguments(
            decl.params,
            arg_exprs,
            context,
        )

        with self.runtime.call_frame(context):
            with self.runtime.scope(context):
                self.bind_prepared_arguments(prepared)

                try:
                    self.execute_block(decl.body)

                except ReturnSignal as signal:
                    err = PseudoRuntimeError("RETURN cannot be used in a PROCEDURE")

                    if signal.span is not None:
                        raise err.with_location(
                            signal.span.line,
                            signal.span.col,
                        ) from None

                    raise err from None

    def call_function(self, name: str, arg_exprs: list[Any]) -> Any:
        decl = self.runtime.get_function(name)
        context = f"FUNCTION {decl.name}"
        prepared = self.prepare_arguments(
            decl.params,
            arg_exprs,
            context,
        )
        return_type = self.runtime.resolve_type_spec(decl.return_type)

        with self.runtime.call_frame(context):
            with self.runtime.scope(context):
                self.bind_prepared_arguments(prepared)

                try:
                    self.execute_block(decl.body)

                except ReturnSignal as signal:
                    return coerce_value(signal.value, return_type)

        raise PseudoRuntimeError(f"FUNCTION {decl.name!r} did not RETURN a value")

    def call_set_builtin_procedure(self, name: str, arg_exprs: list[Any]):
        expected = 1 if name == "SETCLEAR" else 2
        self.require_arg_count(name, arg_exprs, expected)

        reference = self.make_reference(arg_exprs[0])
        current = self.require_set(reference.get())

        if name == "SETCLEAR":
            reference.set(SetValue.create(current.type_spec))
            return

        singleton = make_set_value(
            current.type_spec,
            [self.eval(arg_exprs[1])],
        )
        key = next(iter(singleton.elements))

        if name == "SETADD":
            values = list(current.elements.values())

            if key not in current.elements:
                values.append(singleton.elements[key])

            reference.set(make_set_value(current.type_spec, values))
            return

        if name == "SETREMOVE" and key not in current.elements:
            raise PseudoRuntimeError("SETREMOVE element is not present in SET")

        values = [
            value
            for element_key, value in current.elements.items()
            if element_key != key
        ]
        reference.set(make_set_value(current.type_spec, values))

    def prepare_arguments(
        self,
        params: list[Any],
        arg_exprs: list[Any],
        context: str,
    ) -> list[tuple[str, str, Any, Any]]:
        if len(arg_exprs) != len(params):
            raise PseudoRuntimeError(
                f"{context} expects {len(params)} argument(s), "
                f"got {len(arg_exprs)}"
            )

        prepared = []

        for param, arg_expr in zip(params, arg_exprs):
            param_type = self.runtime.resolve_type_spec(param.type_spec)

            if param.passing == T.BYREF:
                reference = self.make_reference(arg_expr)

                if not same_type(reference.type_spec, param_type):
                    raise PseudoRuntimeError(
                        f"BYREF parameter {param.name!r} expects "
                        f"{type_to_str(param_type)}, "
                        f"got {type_to_str(reference.type_spec)}"
                    )

                prepared.append((param.name, T.BYREF, param_type, reference))

            else:
                value = self.eval(arg_expr)
                value = coerce_value(value, param_type)
                prepared.append((param.name, T.BYVAL, param_type, value))

        return prepared

    def bind_prepared_arguments(self, prepared: list[tuple[str, str, Any, Any]]):
        for name, passing, type_spec, payload in prepared:
            if passing == T.BYREF:
                self.env.define_reference(name, type_spec, payload)
            else:
                self.env.define(name, type_spec, payload)

    def pointer_reference(self, pointer: Any) -> Reference:
        if not isinstance(pointer, PointerValue):
            raise PseudoRuntimeError(
                f"Expected POINTER, got {runtime_type_name(pointer)}"
            )

        if pointer.reference is None:
            raise PseudoRuntimeError("Cannot dereference an uninitialised POINTER")

        return Reference(
            type_spec=pointer.type_spec.target_type,
            getter=pointer.reference.get,
            setter=pointer.reference.set,
            description="POINTER dereference",
        )

    def make_reference(self, expr: Any) -> Reference:
        if isinstance(expr, VariableExpr):
            binding = self.env.get_binding(expr.name)

            if binding.constant:
                raise PseudoRuntimeError(
                    f"Cannot pass constant {binding.original_name!r} BYREF"
                )

            return Reference(
                type_spec=binding.type_spec,
                getter=binding.read,
                setter=binding.write,
                description=expr.name,
            )

        if isinstance(expr, ArrayAccessExpr):
            arr = self.eval(expr.array_expr)

            if not isinstance(arr, ArrayValue):
                raise PseudoRuntimeError("BYREF indexed argument is not an ARRAY")

            indices = [
                self.require_int(self.eval(e))
                for e in expr.indices
            ]

            arr.validate_indices(indices)

            return Reference(
                type_spec=arr.type_spec.element_type,
                getter=lambda arr=arr, indices=indices: arr.get(indices),
                setter=lambda value, arr=arr, indices=indices: arr.set(indices, value),
                description="ARRAY element",
            )

        if isinstance(expr, FieldAccessExpr):
            holder = self.eval(expr.record_expr)

            if isinstance(holder, RecordValue):
                field_type = holder.field_type(expr.field_name)

                return Reference(
                    type_spec=field_type,
                    getter=lambda record=holder, name=expr.field_name: record.get(name),
                    setter=lambda value, record=holder, name=expr.field_name: record.set(
                        name,
                        value,
                    ),
                    description="record field",
                )

            if isinstance(holder, ObjectValue):
                field_type = self.object_field_type(holder, expr.field_name)

                return Reference(
                    type_spec=field_type,
                    getter=lambda obj=holder, name=expr.field_name: (
                        self.get_object_field(obj, name)
                    ),
                    setter=lambda value, obj=holder, name=expr.field_name: (
                        self.set_object_field(obj, name, value)
                    ),
                    description="object property",
                )

            if isinstance(holder, NullObjectValue):
                raise PseudoRuntimeError(
                    f"Object reference of type {holder.type_spec.name!r} "
                    "is not initialised"
                )

            raise PseudoRuntimeError(
                "BYREF field argument is not a record or object"
            )

        if isinstance(expr, DerefExpr):
            pointer = self.eval(expr.pointer_expr)
            return self.pointer_reference(pointer)

        raise PseudoRuntimeError(
            "BYREF argument must be a variable, ARRAY element, "
            "record field or POINTER dereference"
        )

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

        if isinstance(target, IndexTarget):
            arr = self.eval(target.array_expr)

            if not isinstance(arr, ArrayValue):
                raise PseudoRuntimeError("Indexed assignment target is not an ARRAY")

            indices = [
                self.require_int(self.eval(expr))
                for expr in target.indices
            ]

            arr.set(indices, value)
            return

        if isinstance(target, FieldTarget):
            holder = self.eval(target.record_expr)

            if isinstance(holder, RecordValue):
                holder.set(target.field_name, value)
                return

            if isinstance(holder, ObjectValue):
                self.set_object_field(holder, target.field_name, value)
                return

            if isinstance(holder, NullObjectValue):
                raise PseudoRuntimeError(
                    f"Object reference of type {holder.type_spec.name!r} "
                    "is not initialised"
                )

            raise PseudoRuntimeError(
                "Field assignment target is not a record or object"
            )

        if isinstance(target, DerefTarget):
            pointer = self.eval(target.pointer_expr)
            self.pointer_reference(pointer).set(value)
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

        if isinstance(target, IndexTarget):
            arr = self.eval(target.array_expr)

            if not isinstance(arr, ArrayValue):
                raise PseudoRuntimeError("Indexed target is not an ARRAY")

            return arr.type_spec.element_type

        if isinstance(target, FieldTarget):
            holder = self.eval(target.record_expr)

            if isinstance(holder, RecordValue):
                return holder.field_type(target.field_name)

            if isinstance(holder, ObjectValue):
                return self.object_field_type(holder, target.field_name)

            if isinstance(holder, NullObjectValue):
                raise PseudoRuntimeError(
                    f"Object reference of type {holder.type_spec.name!r} "
                    "is not initialised"
                )

            raise PseudoRuntimeError("Field target is not a record or object")

        if isinstance(target, DerefTarget):
            pointer = self.eval(target.pointer_expr)
            return self.pointer_reference(pointer).type_spec

        raise PseudoRuntimeError(f"Invalid target {target!r}")

    def eval(self, expr: Any) -> Any:
        if isinstance(expr, LiteralExpr):
            return expr.value

        if isinstance(expr, AddressOfExpr):
            reference = self.make_reference(expr.target_expr)
            return PointerValue(PointerType(reference.type_spec), reference)

        if isinstance(expr, DerefExpr):
            pointer = self.eval(expr.pointer_expr)
            return self.pointer_reference(pointer).get()

        if isinstance(expr, NewExpr):
            return self.create_object(expr.class_name, expr.args)

        if isinstance(expr, SuperExpr):
            return self.eval_super()

        if isinstance(expr, VariableExpr):
            if self.env.exists(expr.name):
                return self.env.get(expr.name)

            if self.runtime.has_enum_value(expr.name):
                return self.runtime.get_enum_value(expr.name)

            raise PseudoRuntimeError(f"Undefined variable {expr.name!r}")

        if isinstance(expr, ArrayAccessExpr):
            arr = self.eval(expr.array_expr)

            if not isinstance(arr, ArrayValue):
                raise PseudoRuntimeError("Indexed value is not an ARRAY")

            indices = [
                self.require_int(self.eval(e))
                for e in expr.indices
            ]

            return arr.get(indices)

        if isinstance(expr, FieldAccessExpr):
            holder = self.eval(expr.record_expr)

            if isinstance(holder, RecordValue):
                return holder.get(expr.field_name)

            if isinstance(holder, ObjectValue):
                return self.get_object_field(holder, expr.field_name)

            if isinstance(holder, NullObjectValue):
                raise PseudoRuntimeError(
                    f"Object reference of type {holder.type_spec.name!r} "
                    "is not initialised"
                )

            raise PseudoRuntimeError("Field access target is not a record or object")

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

        if isinstance(expr, MethodCallExpr):
            return self.call_method_expression(expr, expression_context=True)

        if isinstance(expr, CallExpr):
            if self.runtime.has_function(expr.name):
                return self.call_function(expr.name, expr.args)

            if self.runtime.has_procedure(expr.name):
                raise PseudoRuntimeError(
                    f"PROCEDURE {expr.name!r} cannot be used as a FUNCTION"
                )

            args = [
                self.eval(arg)
                for arg in expr.args
            ]

            return self.call_builtin(expr.name, args)

        raise PseudoRuntimeError(f"Unknown expression type: {expr!r}")

    def eval_binary(self, left: Any, op: Any, right: Any):
        t = op.type

        if t == T.PLUS:
            if isinstance(left, EnumValue) and type(right) is int:
                return self.offset_enum(left, right)

            self.require_number(left)
            self.require_number(right)
            return left + right

        if t == T.MINUS:
            if isinstance(left, EnumValue) and type(right) is int:
                return self.offset_enum(left, -right)

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

            return self.integer_div(left_i, right_i)

        if t == T.MOD:
            left_i = self.require_int(left)
            right_i = self.require_int(right)

            if right_i == 0:
                raise PseudoRuntimeError("Modulo by zero")

            return left_i - self.integer_div(left_i, right_i) * right_i

        if t == T.AMP:
            if type(left) is not str or type(right) is not str:
                raise PseudoRuntimeError("& requires STRING operands")

            return left + right

        if t == T.EQUAL:
            return self.equal_values(left, right)

        if t == T.NOT_EQUAL:
            return not self.equal_values(left, right)

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

    def equal_values(self, left: Any, right: Any) -> bool:
        if self.is_number(left) and self.is_number(right):
            return left == right

        if type(left) is bool and type(right) is bool:
            return left == right

        if isinstance(left, Char) and isinstance(right, Char):
            return str(left) == str(right)

        if type(left) is str and type(right) is str:
            return left == right

        if isinstance(left, DateValue) and isinstance(right, DateValue):
            return left.key() == right.key()

        if isinstance(left, SetValue) and isinstance(right, SetValue):
            if not same_type(left.type_spec, right.type_spec):
                raise PseudoRuntimeError(
                    f"Cannot compare {runtime_type_name(left)} "
                    f"with {runtime_type_name(right)}"
                )

            return set(left.elements.keys()) == set(right.elements.keys())

        if isinstance(left, PointerValue) and isinstance(right, PointerValue):
            if not same_type(left.type_spec, right.type_spec):
                raise PseudoRuntimeError(
                    f"Cannot compare {runtime_type_name(left)} "
                    f"with {runtime_type_name(right)}"
                )

            return left.reference is right.reference

        if isinstance(left, EnumValue) and isinstance(right, EnumValue):
            if not same_type(left.type_spec, right.type_spec):
                raise PseudoRuntimeError(
                    f"Cannot compare {runtime_type_name(left)} "
                    f"with {runtime_type_name(right)}"
                )

            return left.ordinal == right.ordinal

        if isinstance(left, NullObjectValue) and isinstance(right, NullObjectValue):
            if not same_type(left.type_spec, right.type_spec):
                raise PseudoRuntimeError(
                    f"Cannot compare {runtime_type_name(left)} "
                    f"with {runtime_type_name(right)}"
                )

            return True

        if isinstance(left, ObjectValue) and isinstance(right, ObjectValue):
            if not same_type(left.type_spec, right.type_spec):
                raise PseudoRuntimeError(
                    f"Cannot compare {runtime_type_name(left)} "
                    f"with {runtime_type_name(right)}"
                )

            return left is right

        if isinstance(left, (NullObjectValue, ObjectValue)) and isinstance(
            right,
            (NullObjectValue, ObjectValue),
        ):
            if not same_type(left.type_spec, right.type_spec):
                raise PseudoRuntimeError(
                    f"Cannot compare {runtime_type_name(left)} "
                    f"with {runtime_type_name(right)}"
                )

            return False

        raise PseudoRuntimeError(
            f"Cannot compare {runtime_type_name(left)} "
            f"with {runtime_type_name(right)}"
        )

    @staticmethod
    def offset_enum(value: EnumValue, offset: int) -> EnumValue:
        ordinal = value.ordinal + offset

        if ordinal < 0 or ordinal >= len(value.type_spec.values):
            raise PseudoRuntimeError(
                f"Enumerated value offset is out of range for "
                f"{value.type_spec.name}"
            )

        name = value.type_spec.values[ordinal]
        return EnumValue(value.type_spec, name, ordinal)

    def compare_values(self, left: Any, op_type: str, right: Any) -> bool:
        if self.is_number(left) and self.is_number(right):
            a, b = left, right

        elif isinstance(left, Char) and isinstance(right, Char):
            a, b = str(left), str(right)

        elif type(left) is str and type(right) is str:
            a, b = left, right

        elif isinstance(left, DateValue) and isinstance(right, DateValue):
            a, b = left.key(), right.key()

        elif (
            isinstance(left, EnumValue)
            and isinstance(right, EnumValue)
            and same_type(left.type_spec, right.type_spec)
        ):
            a, b = left.ordinal, right.ordinal

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

        if upper == "EOF":
            self.require_arg_count(upper, args, 1)
            file_id = self.require_string(args[0])
            return self.runtime.file_system.eof(file_id)

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
            return self.ascii_lower_char(c)

        if upper == "UCASE":
            self.require_arg_count(upper, args, 1)
            c = self.require_char(args[0])
            return self.ascii_upper_char(c)

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

        if upper in {
            "UNION",
            "INTERSECTION",
            "DIFFERENCE",
            "SYMMETRICDIFFERENCE",
        }:
            self.require_arg_count(upper, args, 2)
            left, right = self.require_compatible_sets(upper, args[0], args[1])
            left_keys = set(left.elements)
            right_keys = set(right.elements)

            if upper == "UNION":
                keys = left_keys | right_keys
            elif upper == "INTERSECTION":
                keys = left_keys & right_keys
            elif upper == "DIFFERENCE":
                keys = left_keys - right_keys
            else:
                keys = left_keys ^ right_keys

            values = [
                value
                for key, value in left.elements.items()
                if key in keys
            ]
            values.extend(
                value
                for key, value in right.elements.items()
                if key in keys and key not in left.elements
            )
            return make_set_value(left.type_spec, values)

        if upper == "CONTAINS":
            self.require_arg_count(upper, args, 2)
            set_value = self.require_set(args[0])
            singleton = make_set_value(set_value.type_spec, [args[1]])
            key = next(iter(singleton.elements))
            return key in set_value.elements

        if upper == "CARDINALITY":
            self.require_arg_count(upper, args, 1)
            return len(self.require_set(args[0]).elements)

        if upper == "ISEMPTY":
            self.require_arg_count(upper, args, 1)
            return not self.require_set(args[0]).elements

        if upper in {
            "ISSUBSET",
            "ISPROPERSUBSET",
            "ISSUPERSET",
            "ISPROPERSUPERSET",
            "ISDISJOINT",
        }:
            self.require_arg_count(upper, args, 2)
            left, right = self.require_compatible_sets(upper, args[0], args[1])
            left_keys = set(left.elements)
            right_keys = set(right.elements)

            if upper == "ISSUBSET":
                return left_keys <= right_keys

            if upper == "ISPROPERSUBSET":
                return left_keys < right_keys

            if upper == "ISSUPERSET":
                return left_keys >= right_keys

            if upper == "ISPROPERSUPERSET":
                return left_keys > right_keys

            return left_keys.isdisjoint(right_keys)

        raise PseudoRuntimeError(f"Unknown function {name!r}")

    @staticmethod
    def require_set(value: Any) -> SetValue:
        if isinstance(value, SetValue):
            return value

        raise PseudoRuntimeError(
            f"Expected SET, got {runtime_type_name(value)}"
        )

    def require_compatible_sets(
        self,
        operation: str,
        left: Any,
        right: Any,
    ) -> tuple[SetValue, SetValue]:
        left_set = self.require_set(left)
        right_set = self.require_set(right)

        if not same_type(left_set.type_spec, right_set.type_spec):
            raise PseudoRuntimeError(
                f"{operation} requires SET operands of the same type, got "
                f"{type_to_str(left_set.type_spec)} and "
                f"{type_to_str(right_set.type_spec)}"
            )

        return left_set, right_set

    @staticmethod
    def integer_div(left_i: int, right_i: int) -> int:
        quotient = abs(left_i) // abs(right_i)

        if (left_i >= 0) == (right_i >= 0):
            return quotient

        return -quotient

    @staticmethod
    def ascii_lower_char(c: Char) -> Char:
        s = str(c)

        if "A" <= s <= "Z":
            return Char(chr(ord(s) + 32))

        return Char(s)

    @staticmethod
    def ascii_upper_char(c: Char) -> Char:
        s = str(c)

        if "a" <= s <= "z":
            return Char(chr(ord(s) - 32))

        return Char(s)

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
        if type(value) is str:
            return value

        raise PseudoRuntimeError(
            f"Expected STRING, got {runtime_type_name(value)}"
        )

    @staticmethod
    def require_char(value: Any) -> Char:
        if isinstance(value, Char):
            return value

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

    raise PseudoRuntimeError(f"Unsupported INPUT type {type_to_str(type_spec)}")
