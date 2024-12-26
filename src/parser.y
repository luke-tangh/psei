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
    std::vector<std::unique_ptr<ASTBase>> *vec_val;
}

%token INTEGER
%token DECLARE CONSTANT
%token RETURN RETURNS FUNCTION ENDFUNCTION
%token PLUS MINUS NOT
%token LBRACE RBRACE ADD SUB MUL DIV INTDIV MOD
%token LT GT LEQ GEQ EQ NEQ AND OR COL

%token <str_val> IDENTIFIER
%token <int_val> INT_CONST

%type <ast_val> Number
%type <ast_val> Decl BType ConstDecl ConstInitVal VarDecl
%type <ast_val> FuncDef FuncType Block BlockItem Stmt LVal 
%type <ast_val> Exp PrimaryExp UnaryExp UnaryOp MulExp AddExp RelExp EqExp LAndExp LOrExp ConstExp

%type <vec_val> BlockItems

%%

CompUnit
    : FuncDef {
        auto comp_unit = make_unique<CompUnitNode>();
        comp_unit->func_def = unique_ptr<ASTBase>($1);
        ast = move(comp_unit);
    }
    ;

Decl
    : ConstDecl {
        auto ast = new DeclNode();
        ast->decl = unique_ptr<ASTBase>($1);
        $$ = ast;
    }
    | VarDecl {
        auto ast = new DeclNode();
        ast->decl = unique_ptr<ASTBase>($1);
        $$ = ast;
    }
    ;

BType
    : INTEGER {
        auto ast = new BTypeNode();
        ast->type = "INTEGER";
        $$ = ast;
    }
    ;

ConstDecl
    : CONSTANT IDENTIFIER EQ ConstInitVal {
        auto ast = new ConstDeclNode();
        ast->identifier = *unique_ptr<string>($2);
        ast->val = unique_ptr<ASTBase>($4);
        $$ = ast;
    }
    ;

ConstInitVal
    : ConstExp {
        auto ast = new ConstInitValNode();
        ast->val = unique_ptr<ASTBase>($1);
        $$ = ast;
    }
    ;

VarDecl
    : DECLARE IDENTIFIER COL BType {
        auto ast = new VarDeclNode();
        ast->identifier = *unique_ptr<string>($2);
        ast->btype = unique_ptr<ASTBase>($4);
        $$ = ast;
    }
    ;

FuncDef
    : FUNCTION IDENTIFIER LBRACE RBRACE RETURNS FuncType Block ENDFUNCTION {
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
    : /* Empty */ { 
        $$ = new BlockNode(); 
    }
    | BlockItems {
        auto ast = new BlockNode();
        ast->items = std::move(*$1);
        delete $1;
        $$ = ast;
    }
    ;

BlockItems
    : BlockItem {
        $$ = new std::vector<std::unique_ptr<ASTBase>>();
        $$->push_back(std::unique_ptr<ASTBase>($1));
    }
    | BlockItems BlockItem {
        $$ = $1;
        $$->push_back(std::unique_ptr<ASTBase>($2));
    }
    ;

BlockItem
    : Decl {
        auto ast = new BlockItemNode();
        ast->stmt = unique_ptr<ASTBase>($1);
        $$ = ast;
    }
    | Stmt {
        auto ast = new BlockItemNode();
        ast->stmt = unique_ptr<ASTBase>($1);
        $$ = ast;
    }
    ;

Stmt
    : LVal EQ Exp {
        auto ast = new StmtNodeA();
        ast->lval = unique_ptr<ASTBase>($1);
        ast->expr = unique_ptr<ASTBase>($3);
        $$ = ast;
    }
    | RETURN Exp {
        auto ast = new StmtNodeB();
        ast->ret = unique_ptr<ASTBase>($2);
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

LVal
    : IDENTIFIER {
        auto ast = new LValNode();
        ast->identifier = *unique_ptr<string>($1);
        $$ = ast;
    }
    ;

PrimaryExp
    : LBRACE Exp RBRACE {
        auto ast = new PrimaryExpNode();
        ast->expr = unique_ptr<ASTBase>($2);
        $$ = ast;
    }
    | Number {
        auto ast = new PrimaryExpNode();
        ast->expr = unique_ptr<ASTBase>($1);
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

ConstExp
    : Exp {
        auto ast = new ConstExpNode();
        ast->expr = unique_ptr<ASTBase>($1);
        $$ = ast;
    }
    ;

%%

void yyerror(unique_ptr<ASTBase> &ast, const char *s) {
    cerr << "error: " << s << endl;
}
