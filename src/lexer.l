%option noyywrap
%option nounput
%option noinput
%option yylineno
%option nounistd
%option never-interactive

%{

#include <cstdlib>
#include <string>

#include "ast/ast.h"
#include "parser.tab.hpp"

%}

/* space & comment */
WhiteSpace    [ \t\n\r]*
LineComment   "//".*

/* identifier */
String        \"([^\"]*)\"
Identifier    [a-zA-Z_][a-zA-Z0-9_]*

/* data type repr */
Decimal       [1-9][0-9]*
Octal         0[0-7]*
Hexadecimal   0[xX][0-9a-fA-F]+
Char          \'.\'
Float         [+-]?([0-9]*\.[0-9]+)
Boolean       (TRUE|FALSE)
Date          [0-9]{2}[-/.][0-9]{2}[-/.][0-9]{4}

%%

{WhiteSpace}    { /* Ignore */ }
{LineComment}   { /* Ignore */ }

    /* Reserved symbols */
"<-"            { return ASSIGN; }
"("             { return LBRAC; }
")"             { return RBRAC; }
"["             { return LSBRAC; }
"]"             { return RSBRAC; }
"+"             { return ADD; }
"-"             { return SUB; }
"NOT"           { return NOT; }
"*"             { return MUL; }
"/"             { return DIV; }
"DIV"           { return INTDIV; }
"MOD"           { return MOD; }
"<"             { return LT; }
">"             { return GT; }
"<="            { return LEQ; }
">="            { return GEQ; }
"="             { return EQ; }
"<>"            { return NEQ; }
"AND"           { return AND; }
"OR"            { return OR; }
":"             { return COL; }
","             { return COMMA; }
"^"             { return HAT; }
"."             { return DOT; }

    /* Data types */
"INTEGER"       { return INTEGER; }
"REAL"          { return REAL; }
"CHAR"          { return CHAR; }
"STRING"        { return STRING; }
"BOOLEAN"       { return BOOLEAN; }
"DATE"          { return DATE; }

    /* IO */
"INPUT"         { return INPUT; }
"OUTPUT"        { return OUTPUT; }

    /* File operations */
"OPENFILE"      { return OPENFILE; }
"READ"          { return READ; }
"WRITE"         { return WRITE; }
"APPEND"        { return APPEND; }
"RANDOM"        { return RANDOM; }
"READFILE"      { return READFILE; }
"WRITEFILE"     { return WRITEFILE; }
"CLOSEFILE"     { return CLOSEFILE; }
"EOF"           { return END_OF_FILE; }
"SEEK"          { return SEEK; }
"GETRECORD"     { return GETRECORD; }
"PUTRECORD"     { return PUTRECORD; }

    /* Constant & Declare */
"CONSTANT"      { return CONSTANT; }
"DECLARE"       { return DECLARE; }
"ARRAY"         { return ARRAY; }
"OF"            { return OF; }

    /* User-defined datatypes */
"TYPE"          { return TYPE; }
"ENDTYPE"       { return ENDTYPE; }
"SET"           { return SET; }
"DEFINE"        { return DEFINE; }

    /* Selections */
"IF"            { return IF; }
"THEN"          { return THEN; }
"ELSE"          { return ELSE; }
"ENDIF"         { return ENDIF; }
"CASE"          { return CASE; }
"OTHERWISE"     { return OTHERWISE; }
"ENDCASE"       { return ENDCASE; } 

    /* Loops */
"FOR"           { return FOR; }
"TO"            { return TO; }
"STEP"          { return STEP; }
"NEXT"          { return NEXT; }
"REPEAT"        { return REPEAT; }
"UNTIL"         { return UNTIL; }
"WHILE"         { return WHILE; }
"ENDWHILE"      { return ENDWHILE; }

    /* Function & Procedure */
"FUNCTION"      { return FUNCTION; }
"RETURNS"       { return RETURNS; }
"RETURN"        { return RETURN; }
"ENDFUNCTION"   { return ENDFUNCTION; }
"PROCEDURE"     { return PROCEDURE; }
"ENDPROCEDURE"  { return ENDPROCEDURE; }
"BYREF"         { return BYREF; }
"BYVAL"         { return BYVAL; }

    /* Object-oriented Programming */
"CLASS"         { return CLASS; }
"ENDCLASS"      { return ENDCLASS; }
"INHERITS"      { return INHERITS; }
"PUBLIC"        { return PUBLIC; }
"PRIVATE"       { return PRIVATE; }
"SUPER"         { return SUPER; }
"NEW"           { return NEW; }

{Decimal}       { yylval.int_val = strtol(yytext, nullptr, 0); return INT_CONST; }
{Octal}         { yylval.int_val = strtol(yytext, nullptr, 0); return INT_CONST; }
{Hexadecimal}   { yylval.int_val = strtol(yytext, nullptr, 0); return INT_CONST; }

{Float}         { yylval.float_val = strtof(yytext, nullptr); return REAL_CONST; }
{Char}          { yylval.int_val = yytext[1]; return CHAR_CONST; }
{String}        { yylval.str_val = new std::string(yytext + 1, yyleng - 2); return STR_CONST; }
{Boolean}       { yylval.int_val = (std::string(yytext) == "TRUE") ? true : false; return BOOL_CONST; }
{Date}          { yylval.str_val = new std::string(yytext); return DATE_CONST; }

{Identifier}    { yylval.str_val = new std::string(yytext); return IDENTIFIER; }

.               { return yytext[0]; }

%%
