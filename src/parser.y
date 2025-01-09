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
    float float_val;
    char char_val;
    bool bool_val;
    std::string *str_val;
    ASTBase *ast_val;
    std::vector<std::unique_ptr<ASTBase>> *vec_val;
}

// Data types
%token INTEGER REAL CHAR STRING BOOLEAN DATE

// Initialisation
%token DECLARE CONSTANT

// IF
%token IF THEN ELSE ENDIF

// WHILE
%token WHILE ENDWHILE

// FUNCTION
%token FUNCTION ENDFUNCTION RETURN RETURNS

// Reserved Symbols
%token PLUS MINUS NOT
%token ASSIGN LBRACE RBRACE ADD SUB MUL DIV INTDIV MOD
%token LT GT LEQ GEQ EQ NEQ AND OR COL COMMA

// Token types with semantic values
%token <int_val> INT_CONST
%token <float_val> REAL_CONST
%token <char_val> CHAR_CONST
%token <str_val> STR_CONST DATE_CONST IDENTIFIER
%token <bool_val> BOOL_CONST

// Non-terminal types
%type <ast_val> Number String Char Boolean Date
%type <ast_val> Decl BType ConstDecl ConstInitVal VarDecl
%type <ast_val> FuncDef FuncType Param Block BlockItem Stmt LVal OptionalElse
%type <ast_val> Exp PrimaryExp UnaryExp UnaryOp MulExp AddExp RelExp EqExp LAndExp LOrExp 
%type <vec_val> BlockItems ParamList

%%

CompUnit
    : /* empty */ {
        auto comp_unit = make_unique<CompUnitNode>();
        ast = move(comp_unit);
    }
    | CompUnit BlockItem {
        auto comp_unit = static_cast<CompUnitNode*>(ast.get());
        comp_unit->items.push_back(unique_ptr<ASTBase>($2));
    }
    | CompUnit FuncDef {
        auto comp_unit = static_cast<CompUnitNode*>(ast.get());
        comp_unit->items.push_back(unique_ptr<ASTBase>($2));
    }
    ;

Number
    : INT_CONST {
        auto ast = make_unique<NumberNode>((int)($1));
        $$ = ast.release();
    }
    | REAL_CONST {
        auto ast = make_unique<NumberNode>((float)($1));
        $$ = ast.release();
    }
    ;

Exp
    : LOrExp {
        auto ast = make_unique<ExpNode>();
        ast->expr = unique_ptr<ASTBase>($1);
        $$ = ast.release();
    }
    ;

String
    : STR_CONST {
        auto ast = make_unique<StringNode>();
        ast->str = *unique_ptr<string>($1);
        $$ = ast.release();
    }
    ;

Char
    : CHAR_CONST {
        auto ast = make_unique<CharNode>();
        ast->c = (char)($1);
        $$ = ast.release();
    }
    ;

Boolean
    : BOOL_CONST {
        auto ast = make_unique<BooleanNode>();
        ast->val = (bool)($1);
        $$ = ast.release();
    }
    ;

Date
    : DATE_CONST {
        auto ast = make_unique<DateNode>();
        ast->date = *unique_ptr<string>($1);
        $$ = ast.release();
    }
    ;

Decl
    : ConstDecl {
        auto ast = make_unique<DeclNode>();
        ast->decl = unique_ptr<ASTBase>($1);
        $$ = ast.release();
    }
    | VarDecl {
        auto ast = make_unique<DeclNode>();
        ast->decl = unique_ptr<ASTBase>($1);
        $$ = ast.release();
    }
    ;

BType
    : INTEGER {
        auto ast = make_unique<BTypeNode>();
        ast->type = DTYPE_INT;
        $$ = ast.release();
    }
    | REAL {
        auto ast = make_unique<BTypeNode>();
        ast->type = DTYPE_REAL;
        $$ = ast.release();
    }
    | CHAR {
        auto ast = make_unique<BTypeNode>();
        ast->type = DTYPE_CHAR;
        $$ = ast.release();
    }
    | STRING {
        auto ast = make_unique<BTypeNode>();
        ast->type = DTYPE_STR;
        $$ = ast.release();
    }
    | BOOLEAN {
        auto ast = make_unique<BTypeNode>();
        ast->type = DTYPE_BOOL;
        $$ = ast.release();
    }
    | DATE {
        auto ast = make_unique<BTypeNode>();
        ast->type = DTYPE_DATE;
        $$ = ast.release();
    }
    ;

ConstDecl
    : CONSTANT IDENTIFIER EQ ConstInitVal {
        auto ast = make_unique<ConstDeclNode>();
        ast->identifier = *unique_ptr<string>($2);
        ast->val = unique_ptr<ASTBase>($4);

        Symbol sym = Symbol(
            ast->identifier,
            STYPE_CONST,
            yylineno
        );
        if (!symTable->insert(sym.name, sym)) {
            yyerror(("Identifier already defined: " + sym.type + " \"" + sym.name + "\"").c_str());
        }

        $$ = ast.release();
    }
    ;

ConstInitVal
    : Exp {
        auto ast = make_unique<ConstInitValNode>();
        ast->val = unique_ptr<ASTBase>($1);
        $$ = ast.release();
    }
    | String {
        auto ast = make_unique<ConstInitValNode>();
        ast->val = unique_ptr<ASTBase>($1);
        $$ = ast.release();
    }
    | Char {
        auto ast = make_unique<ConstInitValNode>();
        ast->val = unique_ptr<ASTBase>($1);
        $$ = ast.release();
    }
    | Boolean {
        auto ast = make_unique<ConstInitValNode>();
        ast->val = unique_ptr<ASTBase>($1);
        $$ = ast.release();
    }
    | Date {
        auto ast = make_unique<ConstInitValNode>();
        ast->val = unique_ptr<ASTBase>($1);
        $$ = ast.release();
    }
    ;

VarDecl
    : DECLARE IDENTIFIER COL BType {
        auto ast = make_unique<VarDeclNode>();
        ast->identifier = *unique_ptr<string>($2);
        ast->btype = unique_ptr<ASTBase>($4);

        Symbol sym = Symbol(
            ast->identifier,
            STYPE_VAR,
            yylineno
        );
        if (!symTable->insert(sym.name, sym)) {
            yyerror(("Identifier already defined: " + sym.type + " \"" + sym.name + "\"").c_str());
        }

        $$ = ast.release();
    }
    ;

FuncDef
    : FUNCTION IDENTIFIER LBRACE ParamList RBRACE RETURNS FuncType Block ENDFUNCTION {
        auto ast = std::make_unique<FuncDefNode>();
        ast->identifier = *$2;
        ast->params = std::move(*$4);
        ast->func_type = std::unique_ptr<ASTBase>($7);
        ast->block = std::unique_ptr<ASTBase>($8);

        Symbol sym = Symbol(
            ast->identifier,
            STYPE_FUNC,
            yylineno
        );
        if (!symTable->insert(sym.name, sym)) {
            yyerror(("Identifier already defined: " + sym.name).c_str());
        }

        $$ = ast.release();
    }
    ;

ParamList
    : Param {
        $$ = new std::vector<std::unique_ptr<ASTBase>>();
        $$->push_back(std::unique_ptr<ASTBase>($1));
    }
    | ParamList COMMA Param {
        $$ = $1;
        $1->push_back(std::unique_ptr<ASTBase>($3));
    }
    ;

Param
    : IDENTIFIER COL BType {
        auto param = make_unique<ParamNode>();
        param->name = *unique_ptr<string>($1);
        param->type = unique_ptr<ASTBase>($3);
        $$ = param.release();
    }
    ;

FuncType
    : INTEGER {
        auto ast = make_unique<FuncTypeNode>();
        ast->type = DTYPE_INT;
        $$ = ast.release();
    }
    | REAL {
        auto ast = make_unique<FuncTypeNode>();
        ast->type = DTYPE_REAL;
        $$ = ast.release();
    }
    ;

Block
    : /* Empty */ {
        auto ast = make_unique<BlockNode>();
        $$ = ast.release();
    }
    | /* Empty */  {
        symTable->enterScope();
    } 
    BlockItems 
    {     
        auto ast = make_unique<BlockNode>();
        ast->items = move(*$2);
        $$ = ast.release();

        symTable->exitScope();
    }
    ;

BlockItems
    : BlockItem {
        $$ = new vector<unique_ptr<ASTBase>>();
        $$->push_back(unique_ptr<ASTBase>($1));
    }
    | BlockItems BlockItem {
        $$ = $1;
        $$->push_back(unique_ptr<ASTBase>($2));
    }
    ;

BlockItem
    : Decl {
        auto ast = make_unique<BlockItemNode>();
        ast->stmt = unique_ptr<ASTBase>($1);
        $$ = ast.release();
    }
    | Stmt {
        auto ast = make_unique<BlockItemNode>();
        ast->stmt = unique_ptr<ASTBase>($1);
        $$ = ast.release();
    }
    ;

Stmt
    : LVal ASSIGN Exp {
        auto ast = make_unique<StmtNodeAssign>();
        ast->lval = unique_ptr<ASTBase>($1);
        ast->expr = unique_ptr<ASTBase>($3);
        $$ = ast.release();
    }
    | IF Exp THEN Block OptionalElse ENDIF {
        auto ast = make_unique<StmtNodeIf>();
        ast->cond = unique_ptr<ASTBase>($2);
        ast->ifs = unique_ptr<ASTBase>($4);
        ast->elses = unique_ptr<ASTBase>($5);
        $$ = ast.release();
    }
    | WHILE Exp Block ENDWHILE {
        auto ast = make_unique<StmtNodeWhile>();
        ast->cond = unique_ptr<ASTBase>($2);
        ast->stmt = unique_ptr<ASTBase>($3);
        $$ = ast.release();
    }
    | RETURN Exp {
        auto ast = make_unique<StmtNodeReturn>();
        ast->ret = unique_ptr<ASTBase>($2);
        $$ = ast.release();
    }
    ;

OptionalElse
    : ELSE Block { 
        $$ = $2; 
    }
    | /* Empty */ {
        $$ = nullptr; 
    }
    ;

LVal
    : IDENTIFIER {
        auto ast = make_unique<LValNode>();
        ast->identifier = *unique_ptr<string>($1);
        $$ = ast.release();
    }
    ;

PrimaryExp
    : LBRACE Exp RBRACE {
        auto ast = make_unique<PrimaryExpNode>();
        ast->expr = unique_ptr<ASTBase>($2);
        $$ = ast.release();
    }
    | Number {
        auto ast = make_unique<PrimaryExpNode>();
        ast->expr = unique_ptr<ASTBase>($1);
        $$ = ast.release();
    }
    | LVal {
        auto ast = make_unique<PrimaryExpNode>();
        ast->expr = unique_ptr<ASTBase>($1);
        $$ = ast.release();
    }
    ;

UnaryExp
    : PrimaryExp {
        auto ast = make_unique<UnaryExpNodeReduce>();
        ast->expr = unique_ptr<ASTBase>($1);
        $$ = ast.release();
    }
    | UnaryOp UnaryExp {
        auto ast = make_unique<UnaryExpNodeOp>();
        ast->op = unique_ptr<ASTBase>($1);
        ast->expr = unique_ptr<ASTBase>($2);
        $$ = ast.release();
    }
    ;

UnaryOp
    : ADD {
        auto ast = make_unique<UnaryOpNode>();
        ast->op = OP_ADD;
        $$ = ast.release();
    }
    | SUB {
        auto ast = make_unique<UnaryOpNode>();
        ast->op = OP_SUB;
        $$ = ast.release();
    }
    | NOT {
        auto ast = make_unique<UnaryOpNode>();
        ast->op = OP_NOT;
        $$ = ast.release();
    }
    ;

MulExp
    : UnaryExp {
        auto ast = make_unique<MulExpNodeReduce>();
        ast->expr = unique_ptr<ASTBase>($1);
        $$ = ast.release();
    }
    | MulExp MUL UnaryExp {
        auto ast = make_unique<MulExpNodeOp>();
        ast->op = OP_MUL;
        ast->left = unique_ptr<ASTBase>($1);
        ast->right = unique_ptr<ASTBase>($3);
        $$ = ast.release();
    }
    | MulExp DIV UnaryExp {
        auto ast = make_unique<MulExpNodeOp>();
        ast->op = OP_DIV;
        ast->left = unique_ptr<ASTBase>($1);
        ast->right = unique_ptr<ASTBase>($3);
        $$ = ast.release();
    }
    | MulExp INTDIV UnaryExp {
        auto ast = make_unique<MulExpNodeOp>();
        ast->op = OP_INTDIV;
        ast->left = unique_ptr<ASTBase>($1);
        ast->right = unique_ptr<ASTBase>($3);
        $$ = ast.release();
    }
    | MulExp MOD UnaryExp {
        auto ast = make_unique<MulExpNodeOp>();
        ast->op = OP_MOD;
        ast->left = unique_ptr<ASTBase>($1);
        ast->right = unique_ptr<ASTBase>($3);
        $$ = ast.release();
    }
    ;

AddExp
    : MulExp {
        auto ast = make_unique<AddExpNodeReduce>();
        ast->expr = unique_ptr<ASTBase>($1);
        $$ = ast.release();
    }
    | AddExp ADD MulExp {
        auto ast = make_unique<AddExpNodeOp>();
        ast->op = OP_ADD;
        ast->left = unique_ptr<ASTBase>($1);
        ast->right = unique_ptr<ASTBase>($3);
        $$ = ast.release();
    }
    | AddExp SUB MulExp {
        auto ast = make_unique<AddExpNodeOp>();
        ast->op = OP_SUB;
        ast->left = unique_ptr<ASTBase>($1);
        ast->right = unique_ptr<ASTBase>($3);
        $$ = ast.release();
    }
    ;

RelExp
    : AddExp {
        auto ast = make_unique<RelExpNodeReduce>();
        ast->expr = unique_ptr<ASTBase>($1);
        $$ = ast.release();
    }
    | RelExp LT AddExp {
        auto ast = make_unique<RelExpNodeCompare>();
        ast->op = OP_LT;
        ast->left = unique_ptr<ASTBase>($1);
        ast->right = unique_ptr<ASTBase>($3);
        $$ = ast.release();
    }
    | RelExp GT AddExp {
        auto ast = make_unique<RelExpNodeCompare>();
        ast->op = OP_GT;
        ast->left = unique_ptr<ASTBase>($1);
        ast->right = unique_ptr<ASTBase>($3);
        $$ = ast.release();
    }
    | RelExp LEQ AddExp {
        auto ast = make_unique<RelExpNodeCompare>();
        ast->op = OP_LEQ;
        ast->left = unique_ptr<ASTBase>($1);
        ast->right = unique_ptr<ASTBase>($3);
        $$ = ast.release();
    }
    | RelExp GEQ AddExp {
        auto ast = make_unique<RelExpNodeCompare>();
        ast->op = OP_GEQ;
        ast->left = unique_ptr<ASTBase>($1);
        ast->right = unique_ptr<ASTBase>($3);
        $$ = ast.release();
    }
    ;

EqExp
    : RelExp {
        auto ast = make_unique<EqExpNodeReduce>();
        ast->expr = unique_ptr<ASTBase>($1);
        $$ = ast.release();
    }
    | EqExp EQ RelExp {
        auto ast = make_unique<EqExpNodeCompare>();
        ast->op = OP_EQ;
        ast->left = unique_ptr<ASTBase>($1);
        ast->right = unique_ptr<ASTBase>($3);
        $$ = ast.release();
    }
    | EqExp NEQ RelExp {
        auto ast = make_unique<EqExpNodeCompare>();
        ast->op = OP_NEQ;
        ast->left = unique_ptr<ASTBase>($1);
        ast->right = unique_ptr<ASTBase>($3);
        $$ = ast.release();
    }
    ;

LAndExp
    : EqExp {
        auto ast = make_unique<LAndExpNodeReduce>();
        ast->expr = unique_ptr<ASTBase>($1);
        $$ = ast.release();
    }
    | LAndExp AND EqExp {
        auto ast = make_unique<LAndExpNodeLogic>();
        ast->op = OP_AND;
        ast->left = unique_ptr<ASTBase>($1);
        ast->right = unique_ptr<ASTBase>($3);
        $$ = ast.release();
    }
    ;

LOrExp
    : LAndExp {
        auto ast = make_unique<LOrExpNodeReduce>();
        ast->expr = unique_ptr<ASTBase>($1);
        $$ = ast.release();
    }
    | LOrExp OR LAndExp {
        auto ast = make_unique<LOrExpNodeLogic>();
        ast->op = OP_OR;
        ast->left = unique_ptr<ASTBase>($1);
        ast->right = unique_ptr<ASTBase>($3);
        $$ = ast.release();
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
