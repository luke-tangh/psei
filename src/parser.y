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
void yyerror(std::unique_ptr<ASTBase> &ast, const char *s);

using namespace std;

%}

%parse-param { std::unique_ptr<ASTBase> &ast }

%union {
    int int_val;
    std::string *str_val;
    ASTBase *ast_val;
}

%token INTEGER
%token RETURN RETURNS FUNCTION ENDFUNCTION
%token PLUS MINUS NOT
%token ADD SUB MUL DIV INTDIV MOD
%token LT GT LEQ GEQ EQ NEQ AND OR

%token <str_val> IDENTIFIER
%token <int_val> INT_CONST

%type <ast_val> FuncDef FuncType Block Stmt
%type <ast_val> Exp PrimaryExp Number UnaryExp UnaryOp MulExp AddExp RelExp EqExp LAndExp LOrExp

%%

CompUnit
    : FuncDef {
        auto comp_unit = make_unique<CompUnitNode>();
        comp_unit->func_def = unique_ptr<ASTBase>($1);
        ast = move(comp_unit);
    }
    ;

FuncDef
    : FUNCTION IDENTIFIER '(' ')' RETURNS FuncType Block ENDFUNCTION {
        auto ast = new FuncDefNode();
        ast->identifier = *unique_ptr<string>($2);
        ast->func_type = unique_ptr<ASTBase>($6);
        ast->block = unique_ptr<ASTBase>($7);
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
        ast->block = unique_ptr<ASTBase>($1);
        $$ = ast;
    }
    ;

Stmt
    : RETURN Exp {
        auto ast = new StmtNode();
        ast->stmt = unique_ptr<ASTBase>($2);
        $$ = ast;
    }
    ;

Exp
    : LOrExp {
        auto ast = new ExpNode();
        ast->expr = unique_ptr<ASTBase>($1);
        $$ = ast;
    }
    ;

PrimaryExp
    : '(' Exp ')' {
        auto ast = new PrimaryExpNodeA();
        ast->expr = unique_ptr<ASTBase>($2);
        $$ = ast;
    }
    | Number {
        auto ast = new PrimaryExpNodeB();
        ast->number = unique_ptr<ASTBase>($1);
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

UnaryExp
    : PrimaryExp {
        auto ast = new UnaryExpNodeA();
        ast->expr = unique_ptr<ASTBase>($1);
        $$ = ast;
    }
    | UnaryOp UnaryExp {
        auto ast = new UnaryExpNodeB();
        ast->op = unique_ptr<ASTBase>($1);
        ast->expr = unique_ptr<ASTBase>($2);
        $$ = ast;
    }
    ;

UnaryOp
    : ADD {
        auto ast = new UnaryOpNode();
        ast->op = "ADD";
        $$ = ast;
    }
    | SUB {
        auto ast = new UnaryOpNode();
        ast->op = "SUB";
        $$ = ast;
    }
    | NOT {
        auto ast = new UnaryOpNode();
        ast->op = "NOT";
        $$ = ast;
    }
    ;

MulExp
    : UnaryExp {
        auto ast = new MulExpNodeA();
        ast->expr = unique_ptr<ASTBase>($1);
        $$ = ast;
    }
    | MulExp MUL UnaryExp {
        auto ast = new MulExpNodeB();
        ast->op = "MUL";
        ast->left = unique_ptr<ASTBase>($1);
        ast->right = unique_ptr<ASTBase>($3);
        $$ = ast;
    }
    | MulExp DIV UnaryExp {
        auto ast = new MulExpNodeB();
        ast->op = "DIV";
        ast->left = unique_ptr<ASTBase>($1);
        ast->right = unique_ptr<ASTBase>($3);
        $$ = ast;
    }
    | MulExp INTDIV UnaryExp {
        auto ast = new MulExpNodeB();
        ast->op = "INTDIV";
        ast->left = unique_ptr<ASTBase>($1);
        ast->right = unique_ptr<ASTBase>($3);
        $$ = ast;
    }
    | MulExp MOD UnaryExp {
        auto ast = new MulExpNodeB();
        ast->op = "MOD";
        ast->left = unique_ptr<ASTBase>($1);
        ast->right = unique_ptr<ASTBase>($3);
        $$ = ast;
    }
    ;

AddExp
    : MulExp {
        auto ast = new AddExpNodeA();
        ast->expr = unique_ptr<ASTBase>($1);
        $$ = ast;
    }
    | AddExp ADD MulExp {
        auto ast = new AddExpNodeB();
        ast->op = "ADD";
        ast->left = unique_ptr<ASTBase>($1);
        ast->right = unique_ptr<ASTBase>($3);
        $$ = ast;
    }
    | AddExp SUB MulExp {
        auto ast = new AddExpNodeB();
        ast->op = "SUB";
        ast->left = unique_ptr<ASTBase>($1);
        ast->right = unique_ptr<ASTBase>($3);
        $$ = ast;
    }
    ;

RelExp
    : AddExp {
        auto ast = new RelExpNodeA();
        ast->expr = unique_ptr<ASTBase>($1);
        $$ = ast;
    }
    | RelExp LT AddExp {
        auto ast = new RelExpNodeB();
        ast->op = "LT";
        ast->left = unique_ptr<ASTBase>($1);
        ast->right = unique_ptr<ASTBase>($3);
        $$ = ast;
    }
    | RelExp GT AddExp {
        auto ast = new RelExpNodeB();
        ast->op = "GT";
        ast->left = unique_ptr<ASTBase>($1);
        ast->right = unique_ptr<ASTBase>($3);
        $$ = ast;
    }
    | RelExp LEQ AddExp {
        auto ast = new RelExpNodeB();
        ast->op = "LEQ";
        ast->left = unique_ptr<ASTBase>($1);
        ast->right = unique_ptr<ASTBase>($3);
        $$ = ast;
    }
    | RelExp GEQ AddExp {
        auto ast = new RelExpNodeB();
        ast->op = "GEQ";
        ast->left = unique_ptr<ASTBase>($1);
        ast->right = unique_ptr<ASTBase>($3);
        $$ = ast;
    }
    ;

EqExp
    : RelExp {
        auto ast = new EqExpNodeA();
        ast->expr = unique_ptr<ASTBase>($1);
        $$ = ast;
    }
    | EqExp EQ RelExp {
        auto ast = new EqExpNodeB();
        ast->op = "EQ";
        ast->left = unique_ptr<ASTBase>($1);
        ast->right = unique_ptr<ASTBase>($3);
        $$ = ast;
    }
    | EqExp NEQ RelExp {
        auto ast = new EqExpNodeB();
        ast->op = "NEQ";
        ast->left = unique_ptr<ASTBase>($1);
        ast->right = unique_ptr<ASTBase>($3);
        $$ = ast;
    }
    ;

LAndExp
    : EqExp {
        auto ast = new LAndExpNodeA();
        ast->expr = unique_ptr<ASTBase>($1);
        $$ = ast;
    }
    | LAndExp AND EqExp {
        auto ast = new LAndExpNodeB();
        ast->op = "AND";
        ast->left = unique_ptr<ASTBase>($1);
        ast->right = unique_ptr<ASTBase>($3);
        $$ = ast;
    }
    ;

LOrExp
    : LAndExp {
        auto ast = new LOrExpNodeA();
        ast->expr = unique_ptr<ASTBase>($1);
        $$ = ast;
    }
    | LOrExp OR LAndExp {
        auto ast = new LOrExpNodeB();
        ast->op = "OR";
        ast->left = unique_ptr<ASTBase>($1);
        ast->right = unique_ptr<ASTBase>($3);
        $$ = ast;
    }
    ;

%%

void yyerror(unique_ptr<ASTBase> &ast, const char *s) {
    cerr << "error: " << s << endl;
}
