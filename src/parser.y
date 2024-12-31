%code requires {
    #include <memory>
    #include <string>
    #include "ast/ast.h"
    #include "ast/symbol.h"
}

%{

#include <iostream>
#include <memory>
#include <string>
#include "ast/ast.h"
#include "ast/symbol.h"

extern int yylineno;
extern char* yytext;

int yylex();
void yyerror(const char* s);
void yyerror(
    std::unique_ptr<ASTBase> &ast, 
    std::unique_ptr<SymbolTable> &symTable, 
    const char *s
);

using namespace std;

%}

%define parse.error verbose

%parse-param { std::unique_ptr<ASTBase> &ast }
%parse-param { std::unique_ptr<SymbolTable> &symTable }

%union {
    int int_val;
    std::string *str_val;
    ASTBase *ast_val;
    std::vector<std::unique_ptr<ASTBase>> *vec_val;
}

%token INTEGER
%token DECLARE CONSTANT
%token IF THEN ELSE ENDIF
%token RETURN RETURNS FUNCTION ENDFUNCTION
%token PLUS MINUS NOT
%token LBRACE RBRACE ADD SUB MUL DIV INTDIV MOD
%token LT GT LEQ GEQ EQ NEQ AND OR COL

%token <str_val> STR_CONST IDENTIFIER
%token <int_val> INT_CONST

%type <ast_val> Number String
%type <ast_val> Decl BType ConstDecl ConstInitVal VarDecl ConstExp ConstStr
%type <ast_val> FuncDef FuncType Block BlockItem Stmt LVal OptionalElse
%type <ast_val> Exp PrimaryExp UnaryExp UnaryOp MulExp AddExp RelExp EqExp LAndExp LOrExp 

%type <vec_val> BlockItems

%%

CompUnit
    : FuncDef {
        auto comp_unit = make_unique<CompUnitNode>();
        comp_unit->func_def = unique_ptr<ASTBase>($1);
        ast = move(comp_unit);
    }
    ;

Number
    : INT_CONST {
        auto ast = new NumberNode();
        ast->i32 = (int)($1);
        $$ = ast;
    }
    ;

String
    : STR_CONST {
        auto ast = new StringNode();
        ast->str = *unique_ptr<string>($1);
        $$ = ast;
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

        Symbol sym = Symbol(
            ast->identifier,
            STYPE_CONST,
            yylineno
        );
        if (!symTable->insert(sym.name, sym)) {
            yyerror(("Identifier already defined: " + sym.type + " \"" + sym.name + "\"").c_str());
        }
    }
    ;

ConstInitVal
    : ConstExp {
        auto ast = new ConstInitValNode();
        ast->val = unique_ptr<ASTBase>($1);
        $$ = ast;
    }
    | ConstStr {
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

        Symbol sym = Symbol(
            ast->identifier,
            STYPE_VAR,
            yylineno
        );
        if (!symTable->insert(sym.name, sym)) {
            yyerror(("Identifier already defined: " + sym.type + " \"" + sym.name + "\"").c_str());
        }
    }
    ;

ConstExp
    : Exp {
        auto ast = new ConstExpNode();
        ast->expr = unique_ptr<ASTBase>($1);
        $$ = ast;
    }
    ;

ConstStr
    : String {
        auto ast = new ConstExpNode();
        ast->expr = unique_ptr<ASTBase>($1);
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

        Symbol sym = Symbol(
            ast->identifier,
            STYPE_FUNC,
            yylineno
        );
        if (!symTable->insert(sym.name, sym)) {
            yyerror(("Identifier already defined: " + sym.type + " \"" + sym.name + "\"").c_str());
        }
    }
    ;

FuncType
    : INTEGER {
        auto ast = new FuncTypeNode();
        ast->type = DTYPE_INT;
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
        auto ast = new StmtNodeAssign();
        ast->lval = unique_ptr<ASTBase>($1);
        ast->expr = unique_ptr<ASTBase>($3);
        $$ = ast;
    }
    | IF Exp THEN Block OptionalElse ENDIF {
        auto ast = new StmtNodeIf();
        ast->cond = unique_ptr<ASTBase>($2);
        ast->ifs = unique_ptr<ASTBase>($4);
        ast->elses = unique_ptr<ASTBase>($5);
        $$ = ast;
    }
    | RETURN Exp {
        auto ast = new StmtNodeReturn();
        ast->ret = unique_ptr<ASTBase>($2);
        $$ = ast;
    }
    ;

OptionalElse
    : ELSE Block { 
        $$ = $2; 
    }
    | {
        $$ = nullptr; 
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
        ast->op = OP_ADD;
        $$ = ast;
    }
    | SUB {
        auto ast = new UnaryOpNode();
        ast->op = OP_SUB;
        $$ = ast;
    }
    | NOT {
        auto ast = new UnaryOpNode();
        ast->op = OP_NOT;
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
        ast->op = OP_MUL;
        ast->left = unique_ptr<ASTBase>($1);
        ast->right = unique_ptr<ASTBase>($3);
        $$ = ast;
    }
    | MulExp DIV UnaryExp {
        auto ast = new MulExpNodeB();
        ast->op = OP_DIV;
        ast->left = unique_ptr<ASTBase>($1);
        ast->right = unique_ptr<ASTBase>($3);
        $$ = ast;
    }
    | MulExp INTDIV UnaryExp {
        auto ast = new MulExpNodeB();
        ast->op = OP_INTDIV;
        ast->left = unique_ptr<ASTBase>($1);
        ast->right = unique_ptr<ASTBase>($3);
        $$ = ast;
    }
    | MulExp MOD UnaryExp {
        auto ast = new MulExpNodeB();
        ast->op = OP_MOD;
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
        ast->op = OP_ADD;
        ast->left = unique_ptr<ASTBase>($1);
        ast->right = unique_ptr<ASTBase>($3);
        $$ = ast;
    }
    | AddExp SUB MulExp {
        auto ast = new AddExpNodeB();
        ast->op = OP_SUB;
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
        ast->op = OP_LT;
        ast->left = unique_ptr<ASTBase>($1);
        ast->right = unique_ptr<ASTBase>($3);
        $$ = ast;
    }
    | RelExp GT AddExp {
        auto ast = new RelExpNodeB();
        ast->op = OP_GT;
        ast->left = unique_ptr<ASTBase>($1);
        ast->right = unique_ptr<ASTBase>($3);
        $$ = ast;
    }
    | RelExp LEQ AddExp {
        auto ast = new RelExpNodeB();
        ast->op = OP_LEQ;
        ast->left = unique_ptr<ASTBase>($1);
        ast->right = unique_ptr<ASTBase>($3);
        $$ = ast;
    }
    | RelExp GEQ AddExp {
        auto ast = new RelExpNodeB();
        ast->op = OP_GEQ;
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
        ast->op = OP_EQ;
        ast->left = unique_ptr<ASTBase>($1);
        ast->right = unique_ptr<ASTBase>($3);
        $$ = ast;
    }
    | EqExp NEQ RelExp {
        auto ast = new EqExpNodeB();
        ast->op = OP_NEQ;
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
        ast->op = OP_AND;
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
        ast->op = OP_OR;
        ast->left = unique_ptr<ASTBase>($1);
        ast->right = unique_ptr<ASTBase>($3);
        $$ = ast;
    }
    ;

%%

void yyerror(const char* s) {
    cerr << "Error at line " << yylineno << ": " << s
         << " near '" << yytext << "'" << endl;
}

void yyerror(unique_ptr<ASTBase> &ast, unique_ptr<SymbolTable> &symTable, const char *s) {
    cerr << "Error at line " << yylineno << ": " << s
         << " near '" << yytext << "'" << endl;
}
