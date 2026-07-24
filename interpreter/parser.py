from __future__ import annotations

from .ast_nodes import (
    ArrayAccessExpr,
    ArrayTarget,
    ArrayType,
    AssignStmt,
    BinaryExpr,
    CallExpr,
    CallStmt,
    CaseClause,
    CaseStmt,
    ConstantStmt,
    DeclareStmt,
    FieldAccessExpr,
    FieldTarget,
    ForStmt,
    FunctionDecl,
    IfStmt,
    IndexTarget,
    InputStmt,
    LiteralExpr,
    OutputStmt,
    Param,
    ProcedureDecl,
    Program,
    RecordField,
    RepeatStmt,
    ReturnStmt,
    SourceSpan,
    TypeDeclEnum,
    TypeDeclRecord,
    UnaryExpr,
    UserTypeRef,
    VariableExpr,
    VarTarget,
    WhileStmt,
)
from .errors import IncompleteInput, ParseError
from .tokens import T, Token


class Parser:
    BASIC_TYPE_TOKENS = {
        T.INTEGER,
        T.REAL,
        T.CHAR,
        T.STRING,
        T.BOOLEAN,
        T.DATE,
    }

    BLOCK_TERMINATORS = {
        T.ELSE,
        T.ENDIF,
        T.OTHERWISE,
        T.ENDCASE,
        T.ENDWHILE,
        T.UNTIL,
        T.NEXT,
        T.ENDPROCEDURE,
        T.ENDFUNCTION,
        T.ENDTYPE,
        T.ENDCLASS,
    }

    CASE_LABEL_STARTERS = {
        T.IDENT,
        T.INT_LIT,
        T.REAL_LIT,
        T.STRING_LIT,
        T.CHAR_LIT,
        T.DATE_LIT,
        T.BOOL_LIT,
        T.MINUS,
    }

    PRECEDENCE = {
        T.OR: 1,
        T.AND: 2,

        T.EQUAL: 3,
        T.NOT_EQUAL: 3,
        T.LESS: 3,
        T.LESS_EQUAL: 3,
        T.GREATER: 3,
        T.GREATER_EQUAL: 3,

        T.PLUS: 4,
        T.MINUS: 4,
        T.AMP: 4,

        T.STAR: 5,
        T.SLASH: 5,
        T.DIV: 5,
        T.MOD: 5,
    }

    def __init__(self, tokens: list[Token]):
        self.tokens = tokens
        self.current = 0

    def parse_program(self) -> Program:
        statements = []
        self.skip_newlines()

        while not self.check(T.EOF):
            if self.check_any(self.BLOCK_TERMINATORS):
                tok = self.peek()
                raise self.err(tok, f"Unexpected block terminator {tok.lexeme!r}")

            statements.append(self.parse_statement())
            self.skip_newlines()

        return Program(statements)

    def parse_block(self, terminators: set[str]) -> list:
        statements = []
        self.skip_newlines()

        while not self.check(T.EOF) and not self.check_any(terminators):
            statements.append(self.parse_statement())
            self.skip_newlines()

        if self.check(T.EOF):
            names = ", ".join(sorted(terminators))
            raise IncompleteInput(f"Unexpected EOF: expected one of {names}")

        return statements

    def parse_statement(self):
        start_tok = self.peek()

        if self.match(T.DECLARE):
            return self.with_span(self.parse_declare(), start_tok)

        if self.match(T.CONSTANT):
            return self.with_span(self.parse_constant(), start_tok)

        if self.match(T.TYPE):
            return self.with_span(self.parse_type_decl(), start_tok)

        if self.match(T.INPUT):
            target = self.parse_lvalue()
            return self.with_span(InputStmt(target), start_tok)

        if self.match(T.OUTPUT):
            exprs = []

            if (
                not self.check(T.NEWLINE)
                and not self.check(T.EOF)
                and not self.check_any(self.BLOCK_TERMINATORS)
            ):
                exprs.append(self.parse_expression())

                while self.match(T.COMMA):
                    exprs.append(self.parse_expression())

            return self.with_span(OutputStmt(exprs), start_tok)

        if self.match(T.IF):
            condition = self.parse_expression()
            self.consume(T.THEN, "Expected THEN after IF condition")

            then_body = self.parse_block({T.ELSE, T.ENDIF})

            else_body = []
            if self.match(T.ELSE):
                else_body = self.parse_block({T.ENDIF})

            self.consume(T.ENDIF, "Expected ENDIF")
            return self.with_span(IfStmt(condition, then_body, else_body), start_tok)

        if self.match(T.CASE):
            return self.with_span(self.parse_case(), start_tok)

        if self.match(T.WHILE):
            condition = self.parse_expression()
            body = self.parse_block({T.ENDWHILE})
            self.consume(T.ENDWHILE, "Expected ENDWHILE")
            return self.with_span(WhileStmt(condition, body), start_tok)

        if self.match(T.REPEAT):
            body = self.parse_block({T.UNTIL})
            self.consume(T.UNTIL, "Expected UNTIL")
            condition = self.parse_expression()
            return self.with_span(RepeatStmt(body, condition), start_tok)

        if self.match(T.FOR):
            name_tok = self.consume(T.IDENT, "Expected loop variable after FOR")
            self.consume(T.ASSIGN, "Expected ← after loop variable")

            start = self.parse_expression()

            self.consume(T.TO, "Expected TO in FOR statement")

            end = self.parse_expression()

            step = None
            if self.match(T.STEP):
                step = self.parse_expression()

            body = self.parse_block({T.NEXT})
            self.consume(T.NEXT, "Expected NEXT")

            if self.check(T.IDENT):
                next_tok = self.advance()

                if next_tok.lexeme.lower() != name_tok.lexeme.lower():
                    raise self.err(
                        next_tok,
                        f"NEXT variable {next_tok.lexeme!r} does not match "
                        f"FOR variable {name_tok.lexeme!r}",
                    )

            return self.with_span(
                ForStmt(name_tok.lexeme, start, end, step, body),
                start_tok,
            )

        if self.match(T.PROCEDURE):
            return self.with_span(self.parse_procedure_decl(), start_tok)

        if self.match(T.FUNCTION):
            return self.with_span(self.parse_function_decl(), start_tok)

        if self.match(T.CALL):
            name = self.consume(T.IDENT, "Expected procedure name after CALL").lexeme
            self.consume(T.LPAREN, "Expected '(' after procedure name")
            args = self.parse_arguments_after_lparen()
            return self.with_span(CallStmt(name, args), start_tok)

        if self.match(T.RETURN):
            expr = self.parse_expression()
            return self.with_span(ReturnStmt(expr), start_tok)

        if self.check(T.CLASS):
            raise self.err(
                self.peek(),
                "CLASS is not implemented in this minimal prototype",
            )

        if self.check(T.IDENT):
            save = self.current
            target = self.parse_lvalue()

            if self.match(T.ASSIGN):
                expr = self.parse_expression()
                return self.with_span(AssignStmt(target, expr), start_tok)

            self.current = save

        tok = self.peek()
        raise self.err(tok, f"Expected statement, got {tok.lexeme!r}")

    def parse_declare(self):
        name = self.consume(T.IDENT, "Expected identifier after DECLARE").lexeme
        self.consume(T.COLON, "Expected ':' after identifier in DECLARE")
        type_spec = self.parse_type()
        return DeclareStmt(name, type_spec)

    def parse_constant(self):
        name = self.consume(T.IDENT, "Expected identifier after CONSTANT").lexeme
        self.consume(T.EQUAL, "Expected '=' after constant name")
        expr = self.parse_literal_only()
        return ConstantStmt(name, expr)

    def parse_type_decl(self):
        name = self.consume(T.IDENT, "Expected type name after TYPE").lexeme

        if self.match(T.EQUAL):
            self.consume(T.LPAREN, "Expected '(' before enumerated values")

            values = [
                self.consume(
                    T.IDENT,
                    "Expected enumerated value name",
                ).lexeme
            ]

            while self.match(T.COMMA):
                values.append(
                    self.consume(
                        T.IDENT,
                        "Expected enumerated value name",
                    ).lexeme
                )

            self.consume(T.RPAREN, "Expected ')' after enumerated values")
            return TypeDeclEnum(name, values)

        fields = []
        self.skip_newlines()

        while not self.check(T.ENDTYPE):
            if self.check(T.EOF):
                raise IncompleteInput("Unexpected EOF: expected ENDTYPE")

            self.consume(T.DECLARE, "Expected DECLARE in record TYPE")
            field_name = self.consume(
                T.IDENT,
                "Expected field name in record TYPE",
            ).lexeme
            self.consume(T.COLON, "Expected ':' after record field name")
            field_type = self.parse_type()

            fields.append(RecordField(field_name, field_type))
            self.skip_newlines()

        self.consume(T.ENDTYPE, "Expected ENDTYPE")
        return TypeDeclRecord(name, fields)

    def parse_procedure_decl(self):
        name = self.consume(T.IDENT, "Expected procedure name").lexeme
        self.consume(T.LPAREN, "Expected '(' after procedure name")
        params = self.parse_params()
        self.consume(T.RPAREN, "Expected ')' after procedure parameters")

        body = self.parse_block({T.ENDPROCEDURE})
        self.consume(T.ENDPROCEDURE, "Expected ENDPROCEDURE")

        return ProcedureDecl(name, params, body)

    def parse_function_decl(self):
        name_tok = self.consume(T.IDENT, "Expected function name")
        self.consume(T.LPAREN, "Expected '(' after function name")
        params = self.parse_params()
        self.consume(T.RPAREN, "Expected ')' after function parameters")

        self.consume(T.RETURNS, "Expected RETURNS after function parameters")
        return_type = self.parse_type()

        for param in params:
            if param.passing == T.BYREF:
                raise self.err(
                    name_tok,
                    "FUNCTION parameters cannot be passed BYREF",
                )

        body = self.parse_block({T.ENDFUNCTION})
        self.consume(T.ENDFUNCTION, "Expected ENDFUNCTION")

        return FunctionDecl(name_tok.lexeme, params, return_type, body)

    def parse_params(self) -> list[Param]:
        params = []

        if self.check(T.RPAREN):
            return params

        passing = T.BYVAL

        while True:
            if self.match(T.BYVAL):
                passing = T.BYVAL
            elif self.match(T.BYREF):
                passing = T.BYREF

            name = self.consume(T.IDENT, "Expected parameter name").lexeme
            self.consume(T.COLON, "Expected ':' after parameter name")
            type_spec = self.parse_type()

            params.append(Param(name, type_spec, passing))

            if not self.match(T.COMMA):
                break

        return params

    def parse_case(self):
        self.consume(T.OF, "Expected OF after CASE")
        selector = self.parse_expression()

        clauses = []
        otherwise_body = []

        self.skip_newlines()

        while not self.check(T.EOF) and not self.check(T.ENDCASE):
            if self.match(T.OTHERWISE):
                self.consume(T.COLON, "Expected ':' after OTHERWISE")
                otherwise_body = self.parse_block({T.ENDCASE})
                break

            start = self.parse_expression()

            end = None
            if self.match(T.TO):
                end = self.parse_expression()

            self.consume(T.COLON, "Expected ':' after CASE value")

            body = self.parse_case_clause_body()
            clauses.append(CaseClause(start, end, body))

            self.skip_newlines()

        self.consume(T.ENDCASE, "Expected ENDCASE")
        return CaseStmt(selector, clauses, otherwise_body)

    def parse_case_clause_body(self) -> list:
        statements = []

        while True:
            self.skip_newlines()

            if self.check(T.EOF):
                raise IncompleteInput("Unexpected EOF: expected ENDCASE")

            if self.check(T.ENDCASE) or self.check(T.OTHERWISE):
                break

            if self.is_case_clause_start():
                break

            statements.append(self.parse_statement())

        return statements

    def is_case_clause_start(self) -> bool:
        if self.peek().type not in self.CASE_LABEL_STARTERS:
            return False

        i = self.current
        depth = 0

        while True:
            tok = self.tokens[i]

            if tok.type in {T.EOF, T.NEWLINE, T.ENDCASE, T.OTHERWISE}:
                return False

            if tok.type in {T.LPAREN, T.LBRACKET}:
                depth += 1

            elif tok.type in {T.RPAREN, T.RBRACKET}:
                depth = max(0, depth - 1)

            elif tok.type == T.COLON and depth == 0:
                return True

            i += 1

    def parse_type(self):
        if self.match(T.ARRAY):
            self.consume(T.LBRACKET, "Expected '[' after ARRAY")
            bounds = []

            while True:
                lower = self.parse_const_int()
                self.consume(T.COLON, "Expected ':' in array bounds")
                upper = self.parse_const_int()

                if lower > upper:
                    raise self.err(
                        self.previous(),
                        "Array lower bound cannot be greater than upper bound",
                    )

                bounds.append((lower, upper))

                if not self.match(T.COMMA):
                    break

            self.consume(T.RBRACKET, "Expected ']' after array bounds")
            self.consume(T.OF, "Expected OF after ARRAY[...]")

            element_type = self.parse_type()
            return ArrayType(tuple(bounds), element_type)

        if self.check_any(self.BASIC_TYPE_TOKENS):
            return self.advance().type

        if self.match(T.IDENT):
            return UserTypeRef(self.previous().lexeme)

        tok = self.peek()
        raise self.err(tok, "Expected data type")

    def parse_const_int(self) -> int:
        sign = 1

        if self.match(T.MINUS):
            sign = -1

        tok = self.consume(T.INT_LIT, "Expected integer literal")
        return sign * tok.literal

    def parse_literal_only(self):
        if self.match(T.MINUS):
            if self.match(T.INT_LIT):
                return LiteralExpr(-self.previous().literal)

            if self.match(T.REAL_LIT):
                return LiteralExpr(-self.previous().literal)

            raise self.err(self.peek(), "Expected numeric literal after '-'")

        if self.match(T.INT_LIT):
            return LiteralExpr(self.previous().literal)

        if self.match(T.REAL_LIT):
            return LiteralExpr(self.previous().literal)

        if self.match(T.STRING_LIT):
            return LiteralExpr(self.previous().literal)

        if self.match(T.CHAR_LIT):
            return LiteralExpr(self.previous().literal)

        if self.match(T.DATE_LIT):
            return LiteralExpr(self.previous().literal)

        if self.match(T.BOOL_LIT):
            return LiteralExpr(self.previous().literal)

        raise self.err(self.peek(), "CONSTANT value must be a literal")

    def parse_lvalue(self):
        name_tok = self.consume(T.IDENT, "Expected variable name")
        expr = VariableExpr(name_tok.lexeme)
        target = VarTarget(name_tok.lexeme)

        while True:
            if self.match(T.LBRACKET):
                indices = self.parse_index_list_after_lbracket()

                if isinstance(expr, VariableExpr) and isinstance(target, VarTarget):
                    target = ArrayTarget(expr.name, indices)
                else:
                    target = IndexTarget(expr, indices)

                expr = ArrayAccessExpr(expr, indices)
                continue

            if self.match(T.DOT):
                field_name = self.consume(
                    T.IDENT,
                    "Expected field name after '.'",
                ).lexeme
                target = FieldTarget(expr, field_name)
                expr = FieldAccessExpr(expr, field_name)
                continue

            break

        return target

    def parse_expression(self, min_prec: int = 1):
        left = self.parse_unary()

        while True:
            tok = self.peek()
            prec = self.PRECEDENCE.get(tok.type)

            if prec is None or prec < min_prec:
                break

            op = self.advance()
            right = self.parse_expression(prec + 1)
            left = BinaryExpr(left, op, right)

        return left

    def parse_unary(self):
        if self.match(T.MINUS) or self.match(T.NOT):
            op = self.previous()
            right = self.parse_unary()
            return UnaryExpr(op, right)

        return self.parse_primary()

    def parse_primary(self):
        if self.match(T.INT_LIT):
            return LiteralExpr(self.previous().literal)

        if self.match(T.REAL_LIT):
            return LiteralExpr(self.previous().literal)

        if self.match(T.STRING_LIT):
            return LiteralExpr(self.previous().literal)

        if self.match(T.CHAR_LIT):
            return LiteralExpr(self.previous().literal)

        if self.match(T.DATE_LIT):
            return LiteralExpr(self.previous().literal)

        if self.match(T.BOOL_LIT):
            return LiteralExpr(self.previous().literal)

        if self.match(T.IDENT):
            name = self.previous().lexeme

            if self.match(T.LPAREN):
                args = self.parse_arguments_after_lparen()
                expr = CallExpr(name, args)
            else:
                expr = VariableExpr(name)

            while True:
                if self.match(T.LBRACKET):
                    indices = self.parse_index_list_after_lbracket()
                    expr = ArrayAccessExpr(expr, indices)
                    continue

                if self.match(T.DOT):
                    field_name = self.consume(
                        T.IDENT,
                        "Expected field name after '.'",
                    ).lexeme
                    expr = FieldAccessExpr(expr, field_name)
                    continue

                break

            return expr

        if self.match(T.LPAREN):
            expr = self.parse_expression()
            self.consume(T.RPAREN, "Expected ')' after expression")
            return expr

        tok = self.peek()

        if tok.type == T.EOF:
            raise IncompleteInput("Unexpected EOF: expected expression")

        raise self.err(tok, f"Expected expression, got {tok.lexeme!r}")

    def parse_arguments_after_lparen(self) -> list:
        args = []

        if not self.check(T.RPAREN):
            args.append(self.parse_expression())

            while self.match(T.COMMA):
                args.append(self.parse_expression())

        self.consume(T.RPAREN, "Expected ')' after arguments")
        return args

    def parse_index_list_after_lbracket(self) -> list:
        indices = [self.parse_expression()]

        while self.match(T.COMMA):
            indices.append(self.parse_expression())

        self.consume(T.RBRACKET, "Expected ']' after array index")
        return indices

    def skip_newlines(self):
        while self.match(T.NEWLINE):
            pass

    def match(self, *types: str) -> bool:
        for type_ in types:
            if self.check(type_):
                self.advance()
                return True

        return False

    def consume(self, type_: str, message: str) -> Token:
        if self.check(type_):
            return self.advance()

        if self.check(T.EOF):
            raise IncompleteInput(message)

        raise self.err(self.peek(), message)

    def check(self, type_: str) -> bool:
        if self.is_at_end() and type_ != T.EOF:
            return False

        return self.peek().type == type_

    def check_any(self, types: set[str]) -> bool:
        return self.peek().type in types

    def advance(self) -> Token:
        if not self.is_at_end():
            self.current += 1

        return self.previous()

    def is_at_end(self) -> bool:
        return self.peek().type == T.EOF

    def peek(self) -> Token:
        return self.tokens[self.current]

    def previous(self) -> Token:
        return self.tokens[self.current - 1]

    @staticmethod
    def with_span(stmt, tok: Token):
        if hasattr(stmt, "span"):
            stmt.span = SourceSpan(tok.line, tok.col)

        return stmt

    @staticmethod
    def err(tok: Token, message: str) -> ParseError:
        return ParseError(
            f"ParseError at line {tok.line}, column {tok.col}: {message}"
        )
