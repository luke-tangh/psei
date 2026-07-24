from __future__ import annotations

from dataclasses import dataclass
from typing import Any


class T:
    EOF = "EOF"
    NEWLINE = "NEWLINE"

    IDENT = "IDENT"
    INT_LIT = "INT_LIT"
    REAL_LIT = "REAL_LIT"
    STRING_LIT = "STRING_LIT"
    CHAR_LIT = "CHAR_LIT"
    DATE_LIT = "DATE_LIT"
    BOOL_LIT = "BOOL_LIT"

    DECLARE = "DECLARE"
    CONSTANT = "CONSTANT"
    ARRAY = "ARRAY"
    OF = "OF"

    INTEGER = "INTEGER"
    REAL = "REAL"
    CHAR = "CHAR"
    STRING = "STRING"
    BOOLEAN = "BOOLEAN"
    DATE = "DATE"

    IF = "IF"
    THEN = "THEN"
    ELSE = "ELSE"
    ENDIF = "ENDIF"

    CASE = "CASE"
    OTHERWISE = "OTHERWISE"
    ENDCASE = "ENDCASE"

    WHILE = "WHILE"
    ENDWHILE = "ENDWHILE"

    REPEAT = "REPEAT"
    UNTIL = "UNTIL"

    FOR = "FOR"
    TO = "TO"
    STEP = "STEP"
    NEXT = "NEXT"

    INPUT = "INPUT"
    OUTPUT = "OUTPUT"

    OPENFILE = "OPENFILE"
    READFILE = "READFILE"
    WRITEFILE = "WRITEFILE"
    CLOSEFILE = "CLOSEFILE"

    READ = "READ"
    WRITE = "WRITE"
    APPEND = "APPEND"
    RANDOM = "RANDOM"

    SEEK = "SEEK"
    GETRECORD = "GETRECORD"
    PUTRECORD = "PUTRECORD"

    CALL = "CALL"
    PROCEDURE = "PROCEDURE"
    ENDPROCEDURE = "ENDPROCEDURE"
    FUNCTION = "FUNCTION"
    RETURNS = "RETURNS"
    ENDFUNCTION = "ENDFUNCTION"
    RETURN = "RETURN"
    BYVAL = "BYVAL"
    BYREF = "BYREF"

    TYPE = "TYPE"
    ENDTYPE = "ENDTYPE"

    CLASS = "CLASS"
    ENDCLASS = "ENDCLASS"

    ASSIGN = "ASSIGN"       # ← or <-
    PLUS = "PLUS"
    MINUS = "MINUS"
    STAR = "STAR"
    SLASH = "SLASH"
    DIV = "DIV"
    MOD = "MOD"
    AMP = "AMP"             # &

    EQUAL = "EQUAL"
    NOT_EQUAL = "NOT_EQUAL"
    LESS = "LESS"
    LESS_EQUAL = "LESS_EQUAL"
    GREATER = "GREATER"
    GREATER_EQUAL = "GREATER_EQUAL"

    AND = "AND"
    OR = "OR"
    NOT = "NOT"

    LPAREN = "LPAREN"
    RPAREN = "RPAREN"
    LBRACKET = "LBRACKET"
    RBRACKET = "RBRACKET"
    COMMA = "COMMA"
    COLON = "COLON"
    DOT = "DOT"


KEYWORDS = {
    "DECLARE": T.DECLARE,
    "CONSTANT": T.CONSTANT,
    "ARRAY": T.ARRAY,
    "OF": T.OF,

    "INTEGER": T.INTEGER,
    "REAL": T.REAL,
    "CHAR": T.CHAR,
    "STRING": T.STRING,
    "BOOLEAN": T.BOOLEAN,
    "DATE": T.DATE,

    "IF": T.IF,
    "THEN": T.THEN,
    "ELSE": T.ELSE,
    "ENDIF": T.ENDIF,

    "CASE": T.CASE,
    "OTHERWISE": T.OTHERWISE,
    "ENDCASE": T.ENDCASE,

    "WHILE": T.WHILE,
    "ENDWHILE": T.ENDWHILE,

    "REPEAT": T.REPEAT,
    "UNTIL": T.UNTIL,

    "FOR": T.FOR,
    "TO": T.TO,
    "STEP": T.STEP,
    "NEXT": T.NEXT,

    "INPUT": T.INPUT,
    "OUTPUT": T.OUTPUT,

    "OPENFILE": T.OPENFILE,
    "READFILE": T.READFILE,
    "WRITEFILE": T.WRITEFILE,
    "CLOSEFILE": T.CLOSEFILE,

    "READ": T.READ,
    "WRITE": T.WRITE,
    "APPEND": T.APPEND,
    "RANDOM": T.RANDOM,

    "SEEK": T.SEEK,
    "GETRECORD": T.GETRECORD,
    "PUTRECORD": T.PUTRECORD,

    "DIV": T.DIV,
    "MOD": T.MOD,
    "AND": T.AND,
    "OR": T.OR,
    "NOT": T.NOT,

    "CALL": T.CALL,
    "PROCEDURE": T.PROCEDURE,
    "ENDPROCEDURE": T.ENDPROCEDURE,
    "FUNCTION": T.FUNCTION,
    "RETURNS": T.RETURNS,
    "ENDFUNCTION": T.ENDFUNCTION,
    "RETURN": T.RETURN,
    "BYVAL": T.BYVAL,
    "BYREF": T.BYREF,

    "TYPE": T.TYPE,
    "ENDTYPE": T.ENDTYPE,

    "CLASS": T.CLASS,
    "ENDCLASS": T.ENDCLASS,
}


@dataclass
class Token:
    type: str
    lexeme: str
    literal: Any
    line: int
    col: int

    def __repr__(self):
        return (
            f"Token({self.type}, {self.lexeme!r}, "
            f"{self.literal!r}, {self.line}:{self.col})"
        )
