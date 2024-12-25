%code requires {
  #include <memory>
  #include <string>
}

%{

#include <iostream>
#include <memory>
#include <string>

#include "ast/ast.h"

int yylex();
void yyerror(std::unique_ptr<ASTNode> &ast, const char *s);

using namespace std;

%}

%parse-param { std::unique_ptr<ASTNode> &ast }

%union {
  int int_val;
  std::string *str_val;
  ASTNode *ast_val;
}

%token RETURN RETURNS FUNCTION ENDFUNCTION
%token INTEGER 

%token <str_val> IDENTIFIER
%token <int_val> INT_CONST

%type <ast_val> FuncDef FuncType Block Stmt Number

%%

CompUnit
  : FuncDef {
    auto comp_unit = make_unique<CompUnitNode>();
    comp_unit->func_def = unique_ptr<ASTNode>($1);
    ast = move(comp_unit);
  }
  ;

FuncDef
  : FUNCTION IDENTIFIER '(' ')' RETURNS FuncType Block ENDFUNCTION {
    auto ast = new FuncDefNode();
    ast->identifier = *unique_ptr<string>($2);
    ast->func_type = unique_ptr<ASTNode>($6);
    ast->block = unique_ptr<ASTNode>($7);
    $$ = ast;
  }
  ;

FuncType
  : INTEGER {
    auto ast = new FuncTypeNode();
    ast->type = "INTEGER";
    $$ = ast;
  }
  ;

Block
  : Stmt {
    auto ast = new BlockNode();
    ast->stmt = unique_ptr<ASTNode>($1);
    $$ = ast;
  }
  ;

Stmt
  : RETURN Number {
    auto ast = new StmtNode();
    ast->number = unique_ptr<ASTNode>($2);
    $$ = ast;
  }
  ;

Number
  : INT_CONST {
    auto ast = new NumberNode();
    ast->i32 = (int)($1);
    $$ = ast;
  }
  ;

%%

void yyerror(unique_ptr<ASTNode> &ast, const char *s) {
  cerr << "error: " << s << endl;
}
