%option noyywrap
%option nounput
%option noinput
%option yylineno

%{

#include <cstdlib>
#include <string>

#include "ast/ast.h"
#include "parser.tab.hpp"

using namespace std;

%}

/* space & comment */
WhiteSpace    [ \t\n\r]*
LineComment   "//".*

/* identifier */
String        \"([^\"]*)\"
Identifier    [a-zA-Z_][a-zA-Z0-9_]*

/* int repr */
Decimal       [1-9][0-9]*
Octal         0[0-7]*
Hexadecimal   0[xX][0-9a-fA-F]+

%%

{WhiteSpace}    { /* Ignore */ }
{LineComment}   { /* Ignore */ }

"<-"            { return ASSIGN; }
"("             { return LBRACE; }
")"             { return RBRACE; }
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

"INTEGER"       { return INTEGER; }

"CONSTANT"      { return CONSTANT; }
"DECLARE"       { return DECLARE; }

"IF"            { return IF; }
"THEN"          { return THEN; }
"ELSE"          { return ELSE; }
"ENDIF"         { return ENDIF; }

"RETURN"        { return RETURN; }
"RETURNS"       { return RETURNS; }
"FUNCTION"      { return FUNCTION; }
"ENDFUNCTION"   { return ENDFUNCTION; }

{Identifier}    { yylval.str_val = new string(yytext); return IDENTIFIER; }

{String}        { yylval.str_val = new std::string(yytext + 1, yyleng - 2); return STR_CONST; }

{Decimal}       { yylval.int_val = strtol(yytext, nullptr, 0); return INT_CONST; }
{Octal}         { yylval.int_val = strtol(yytext, nullptr, 0); return INT_CONST; }
{Hexadecimal}   { yylval.int_val = strtol(yytext, nullptr, 0); return INT_CONST; }

.               { return yytext[0]; }

%%
