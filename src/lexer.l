%option noyywrap
%option nounput
%option noinput

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
Identifier    [a-zA-Z_][a-zA-Z0-9_]*

/* int repr */
Decimal       [1-9][0-9]*
Octal         0[0-7]*
Hexadecimal   0[xX][0-9a-fA-F]+

%%

{WhiteSpace}    { /* Ignore */ }
{LineComment}   { /* Ignore */ }

"INTEGER"       { return INTEGER; }

"RETURN"        { return RETURN; }
"RETURNS"       { return RETURNS; }
"FUNCTION"      { return FUNCTION; }
"ENDFUNCTION"   { return ENDFUNCTION; }

{Identifier}    { yylval.str_val = new string(yytext); return IDENTIFIER; }

{Decimal}       { yylval.int_val = strtol(yytext, nullptr, 0); return INT_CONST; }
{Octal}         { yylval.int_val = strtol(yytext, nullptr, 0); return INT_CONST; }
{Hexadecimal}   { yylval.int_val = strtol(yytext, nullptr, 0); return INT_CONST; }

.               { return yytext[0]; }

%%
