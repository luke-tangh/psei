%code requires {
  #include <memory>
  #include <string>
}

%{

#include <iostream>
#include <memory>
#include <string>

int yylex();
void yyerror(std::unique_ptr<std::string> &ast, const char *s);

using namespace std;

%}

%parse-param { std::unique_ptr<std::string> &ast }

%union {
  std::string *str_val;
  int int_val;
}

%token INTEGER RETURN RETURNS FUNCTION ENDFUNCTION
%token <str_val> IDENT
%token <int_val> INT_CONST

%type <str_val> FuncDef FuncType Block Stmt Number

%%

CompUnit
  : FuncDef {
    ast = unique_ptr<string>($1);
  }
  ;

FuncDef
  : FUNCTION IDENT '(' ')' RETURNS FuncType Block ENDFUNCTION {
    auto ident = unique_ptr<string>($2);
    auto type = unique_ptr<string>($6);
    auto block = unique_ptr<string>($7);
    $$ = new string("FUNCTION " + *ident + "()" + " RETURENS " + *type + "\n" + *block + "\nENDFUNCTION");
  }
  ;

FuncType
  : INTEGER {
    $$ = new string("INTEGER");
  }
  ;

Block
  : Stmt {
    auto stmt = unique_ptr<string>($1);
    $$ = new string(*stmt);
  }
  ;

Stmt
  : RETURN Number {
    auto number = unique_ptr<string>($2);
    $$ = new string("RETURN " + *number);
  }
  ;

Number
  : INT_CONST {
    $$ = new string(to_string($1));
  }
  ;

%%

void yyerror(unique_ptr<string> &ast, const char *s) {
  cerr << "error: " << s << endl;
}
