%code requires {
    #include <memory>
    #include <string>
    #include "ast/ast.h"
    #include "ast/serrors.h"
    #include "ast/symbol.h"
}

%{

#include <iostream>
#include <memory>
#include <string>
#include "ast/ast.h"
#include "ast/serrors.h"
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
%token ARRAY OF

// IF
%token IF THEN ELSE ENDIF

// LOOPS
%token FOR TO STEP NEXT
%token REPEAT UNTIL
%token WHILE ENDWHILE

// FUNCTION
%token FUNCTION ENDFUNCTION RETURN RETURNS

// Reserved Symbols
%token PLUS MINUS NOT
%token ASSIGN LBRACE RBRACE LSBRAC RSBRAC ADD SUB MUL DIV INTDIV MOD
%token LT GT LEQ GEQ EQ NEQ AND OR COL COMMA

// Token types with semantic values
%token <int_val> INT_CONST
%token <float_val> REAL_CONST
%token <char_val> CHAR_CONST
%token <str_val> STR_CONST DATE_CONST IDENTIFIER
%token <bool_val> BOOL_CONST

// Non-terminal types
%type <ast_val> Number String Char Boolean Date
%type <ast_val> Decl BType ConstDecl VarDecl ArrRange
%type <ast_val> FuncDef FuncType ParamList Param Block BlockItem Stmt LVal
%type <ast_val> OptionalElse OptionalStep
%type <ast_val> Exp PrimaryExp UnaryExp UnaryOp MulExp AddExp RelExp EqExp LAndExp LOrExp 
%type <vec_val> ArrRangeList BlockItems Params Index

%%

CompUnit
    : /* empty */ {
        auto comp_unit = std::make_unique<CompUnitNode>();
        ast = std::move(comp_unit);
    }
    | CompUnit BlockItem {
        auto comp_unit = static_cast<CompUnitNode*>(ast.get());
        comp_unit->items.push_back(std::unique_ptr<ASTBase>($2));
    }
    | CompUnit FuncDef {
        auto comp_unit = static_cast<CompUnitNode*>(ast.get());
        comp_unit->items.push_back(std::unique_ptr<ASTBase>($2));
    }
    ;

Number
    : INT_CONST {
        auto ast = std::make_unique<NumberNode>((int)($1));
        $$ = ast.release();
    }
    | REAL_CONST {
        auto ast = std::make_unique<NumberNode>((float)($1));
        $$ = ast.release();
    }
    ;

Exp
    : LOrExp {
        auto ast = std::make_unique<ExpNode>();
        ast->expr = std::unique_ptr<ASTBase>($1);
        $$ = ast.release();
    }
    ;

String
    : STR_CONST {
        auto ast = std::make_unique<StringNode>();
        ast->str = *std::unique_ptr<std::string>($1);
        $$ = ast.release();
    }
    ;

Char
    : CHAR_CONST {
        auto ast = std::make_unique<CharNode>();
        ast->c = (char)($1);
        $$ = ast.release();
    }
    ;

Boolean
    : BOOL_CONST {
        auto ast = std::make_unique<BooleanNode>();
        ast->val = (bool)($1);
        $$ = ast.release();
    }
    ;

Date
    : DATE_CONST {
        auto ast = std::make_unique<DateNode>();
        ast->date = *std::unique_ptr<std::string>($1);
        $$ = ast.release();
    }
    ;

Decl
    : ConstDecl {
        auto ast = std::make_unique<DeclNode>();
        ast->decl = std::unique_ptr<ASTBase>($1);
        $$ = ast.release();
    }
    | VarDecl {
        auto ast = std::make_unique<DeclNode>();
        ast->decl = std::unique_ptr<ASTBase>($1);
        $$ = ast.release();
    }
    ;

BType
    : INTEGER {
        auto ast = std::make_unique<BTypeNode>();
        ast->type = DTYPE_INT;
        $$ = ast.release();
    }
    | REAL {
        auto ast = std::make_unique<BTypeNode>();
        ast->type = DTYPE_REAL;
        $$ = ast.release();
    }
    | CHAR {
        auto ast = std::make_unique<BTypeNode>();
        ast->type = DTYPE_CHAR;
        $$ = ast.release();
    }
    | STRING {
        auto ast = std::make_unique<BTypeNode>();
        ast->type = DTYPE_STR;
        $$ = ast.release();
    }
    | BOOLEAN {
        auto ast = std::make_unique<BTypeNode>();
        ast->type = DTYPE_BOOL;
        $$ = ast.release();
    }
    | DATE {
        auto ast = std::make_unique<BTypeNode>();
        ast->type = DTYPE_DATE;
        $$ = ast.release();
    }
    ;

ConstDecl
    : CONSTANT IDENTIFIER EQ Exp {
        auto ast = std::make_unique<ConstDeclNode>();
        ast->identifier = *std::unique_ptr<std::string>($2);
        ast->val = std::unique_ptr<ASTBase>($4);

        Symbol sym = Symbol(
            ast->identifier,
            STYPE_CONST,
            yylineno
        );
        if (!symTable->insert(sym.name, sym)) {
            semanticError(ErrorType::IdentifierAlreadyDefined, sym.name, yylineno);
        }

        $$ = ast.release();
    }
    ;

VarDecl
    : DECLARE IDENTIFIER COL BType {
        auto ast = std::make_unique<VarDeclNode>();
        ast->identifier = *std::unique_ptr<std::string>($2);
        ast->btype = std::unique_ptr<ASTBase>($4);

        Symbol sym = Symbol(
            ast->identifier,
            STYPE_VAR,
            yylineno
        );
        if (!symTable->insert(sym.name, sym)) {
            semanticError(ErrorType::IdentifierAlreadyDefined, sym.name, yylineno);
        }

        $$ = ast.release();
    }
    | DECLARE IDENTIFIER COL ARRAY LSBRAC ArrRangeList RSBRAC OF BType {
        auto ast = std::make_unique<VarDeclNodeArray>();
        ast->identifier = *std::unique_ptr<std::string>($2);
        ast->btype = std::unique_ptr<ASTBase>($9);
        ast->ranges = std::move(*$6);

        Symbol sym = Symbol(
            ast->identifier,
            STYPE_VAR,
            yylineno
        );
        if (!symTable->insert(sym.name, sym)) {
            semanticError(ErrorType::IdentifierAlreadyDefined, sym.name, yylineno);
        }

        $$ = ast.release();
    }
    ;

ArrRangeList
    : ArrRange {
        $$ = new std::vector<std::unique_ptr<ASTBase>>();
        $$->push_back(std::unique_ptr<ASTBase>($1));
    }
    | ArrRangeList COMMA ArrRange {
        $$ = $1;
        $1->push_back(std::unique_ptr<ASTBase>($3));
    }
    ;

ArrRange
    : Exp COL Exp {
        auto ast = std::make_unique<ArrRangeNode>();
        ast->start = std::unique_ptr<ASTBase>($1);
        ast->end = std::unique_ptr<ASTBase>($3);
        $$ = ast.release();
    }
    ;

FuncDef
    : FUNCTION IDENTIFIER LBRACE ParamList RBRACE RETURNS FuncType Block ENDFUNCTION {
        auto ast = std::make_unique<FuncDefNode>();
        ast->identifier = *std::unique_ptr<std::string>($2);
        ast->param = std::unique_ptr<ASTBase>($4);
        ast->func_type = std::unique_ptr<ASTBase>($7);
        ast->block = std::unique_ptr<ASTBase>($8);

        Symbol sym = Symbol(
            ast->identifier,
            STYPE_FUNC,
            yylineno
        );
        if (!symTable->insert(sym.name, sym)) {
            semanticError(ErrorType::IdentifierAlreadyDefined, sym.name, yylineno);
        }

        $$ = ast.release();
    }
    ;

ParamList
    : /* empty */ {
        $$ = nullptr;
    }
    | Params {
        auto ast = std::make_unique<ParamListNode>();
        ast->params = std::move(*$1);
        $$ = ast.release();
    }

Params
    : Param {
        $$ = new std::vector<std::unique_ptr<ASTBase>>();
        $$->push_back(std::unique_ptr<ASTBase>($1));
    }
    | Params COMMA Param {
        $$ = $1;
        $1->push_back(std::unique_ptr<ASTBase>($3));
    }
    ;

Param
    : IDENTIFIER COL BType {
        auto param = std::make_unique<ParamNode>();
        param->name = *std::unique_ptr<std::string>($1);
        param->type = std::unique_ptr<ASTBase>($3);
        $$ = param.release();
    }
    ;

FuncType
    : INTEGER {
        auto ast = std::make_unique<FuncTypeNode>();
        ast->type = DTYPE_INT;
        $$ = ast.release();
    }
    | REAL {
        auto ast = std::make_unique<FuncTypeNode>();
        ast->type = DTYPE_REAL;
        $$ = ast.release();
    }
    ;

Block
    : /* Empty */ {
        auto ast = std::make_unique<BlockNode>();
        $$ = ast.release();
    }
    | /* Empty */  {
        symTable->enterScope();
    } 
    BlockItems 
    {     
        auto ast = std::make_unique<BlockNode>();
        ast->items = std::move(*$2);
        $$ = ast.release();

        symTable->exitScope();
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
        auto ast = std::make_unique<BlockItemNode>();
        ast->stmt = std::unique_ptr<ASTBase>($1);
        $$ = ast.release();
    }
    | Stmt {
        auto ast = std::make_unique<BlockItemNode>();
        ast->stmt = std::unique_ptr<ASTBase>($1);
        $$ = ast.release();
    }
    ;

Stmt
    : LVal ASSIGN Exp {
        auto ast = std::make_unique<StmtNodeAssign>();
        ast->lval = std::unique_ptr<ASTBase>($1);
        ast->expr = std::unique_ptr<ASTBase>($3);
        $$ = ast.release();
    }
    | IF Exp THEN Block OptionalElse ENDIF {
        auto ast = std::make_unique<StmtNodeIf>();
        ast->cond = std::unique_ptr<ASTBase>($2);
        ast->ifs = std::unique_ptr<ASTBase>($4);
        ast->elses = std::unique_ptr<ASTBase>($5);
        $$ = ast.release();
    }
    | FOR IDENTIFIER ASSIGN Exp TO Exp OptionalStep Block NEXT IDENTIFIER {
        if (*$2 != *$10) {
            semanticError(ErrorType::IdentifiersDontMatch, (*$2), yylineno);
        }

        auto ast = std::make_unique<StmtNodeFor>();
        ast->identifier = *std::unique_ptr<std::string>($2);
        ast->startExpr = std::unique_ptr<ASTBase>($4);
        ast->endExpr = std::unique_ptr<ASTBase>($6);
        ast->stepExpr = std::unique_ptr<ASTBase>($7);
        ast->block = std::unique_ptr<ASTBase>($8);
        
        $$ = ast.release();
    }
    | REPEAT Block UNTIL Exp {
        auto ast = std::make_unique<StmtNodeRepeat>();
        ast->block = std::unique_ptr<ASTBase>($2);
        ast->cond = std::unique_ptr<ASTBase>($4);
        $$ = ast.release();
    }
    | WHILE Exp Block ENDWHILE {
        auto ast = std::make_unique<StmtNodeWhile>();
        ast->cond = std::unique_ptr<ASTBase>($2);
        ast->block = std::unique_ptr<ASTBase>($3);
        $$ = ast.release();
    }
    | RETURN Exp {
        auto ast = std::make_unique<StmtNodeReturn>();
        ast->ret = std::unique_ptr<ASTBase>($2);
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

OptionalStep
    : STEP Exp {
        $$ = $2; 
    }
    | /* Empty */ {
        $$ = nullptr; 
    }
    ;

LVal
    : IDENTIFIER {
        auto ast = std::make_unique<LValNodeId>();
        ast->identifier = *std::unique_ptr<std::string>($1);
        $$ = ast.release();
    } 
    | IDENTIFIER LSBRAC Index RSBRAC {
        auto ast = std::make_unique<LValNodeArray>();
        ast->identifier = *std::unique_ptr<std::string>($1);
        ast->index = std::move(*$3);
        $$ = ast.release();
    }
    ;

Index
    : Exp {
        $$ = new std::vector<std::unique_ptr<ASTBase>>();
        $$->push_back(std::unique_ptr<ASTBase>($1));
    } 
    | Index COMMA Exp {
        $$ = $1;
        $1->push_back(std::unique_ptr<ASTBase>($3));
    }
    ;

PrimaryExp
    : LBRACE Exp RBRACE {
        auto ast = std::make_unique<PrimaryExpNode>();
        ast->expr = std::unique_ptr<ASTBase>($2);
        $$ = ast.release();
    }
    | Number {
        auto ast = std::make_unique<PrimaryExpNode>();
        ast->expr = std::unique_ptr<ASTBase>($1);
        $$ = ast.release();
    }
    | String {
        auto ast = std::make_unique<PrimaryExpNode>();
        ast->expr = std::unique_ptr<ASTBase>($1);
        $$ = ast.release();
    }
    | Char {
        auto ast = std::make_unique<PrimaryExpNode>();
        ast->expr = std::unique_ptr<ASTBase>($1);
        $$ = ast.release();
    }
    | Boolean {
        auto ast = std::make_unique<PrimaryExpNode>();
        ast->expr = std::unique_ptr<ASTBase>($1);
        $$ = ast.release();
    }
    | Date {
        auto ast = std::make_unique<PrimaryExpNode>();
        ast->expr = std::unique_ptr<ASTBase>($1);
        $$ = ast.release();
    }
    | LVal {
        auto ast = std::make_unique<PrimaryExpNode>();
        ast->expr = std::unique_ptr<ASTBase>($1);
        $$ = ast.release();
    }
    ;

UnaryExp
    : PrimaryExp {
        auto ast = std::make_unique<UnaryExpNodeReduce>();
        ast->expr = std::unique_ptr<ASTBase>($1);
        $$ = ast.release();
    }
    | UnaryOp UnaryExp {
        auto ast = std::make_unique<UnaryExpNodeOp>();
        ast->op = std::unique_ptr<ASTBase>($1);
        ast->expr = std::unique_ptr<ASTBase>($2);
        $$ = ast.release();
    }
    ;

UnaryOp
    : ADD {
        auto ast = std::make_unique<UnaryOpNode>();
        ast->op = OP_ADD;
        $$ = ast.release();
    }
    | SUB {
        auto ast = std::make_unique<UnaryOpNode>();
        ast->op = OP_SUB;
        $$ = ast.release();
    }
    | NOT {
        auto ast = std::make_unique<UnaryOpNode>();
        ast->op = OP_NOT;
        $$ = ast.release();
    }
    ;

MulExp
    : UnaryExp {
        auto ast = std::make_unique<MulExpNodeReduce>();
        ast->expr = std::unique_ptr<ASTBase>($1);
        $$ = ast.release();
    }
    | MulExp MUL UnaryExp {
        auto ast = std::make_unique<MulExpNodeOp>();
        ast->op = OP_MUL;
        ast->left = std::unique_ptr<ASTBase>($1);
        ast->right = std::unique_ptr<ASTBase>($3);
        $$ = ast.release();
    }
    | MulExp DIV UnaryExp {
        auto ast = std::make_unique<MulExpNodeOp>();
        ast->op = OP_DIV;
        ast->left = std::unique_ptr<ASTBase>($1);
        ast->right = std::unique_ptr<ASTBase>($3);
        $$ = ast.release();
    }
    | MulExp INTDIV UnaryExp {
        auto ast = std::make_unique<MulExpNodeOp>();
        ast->op = OP_INTDIV;
        ast->left = std::unique_ptr<ASTBase>($1);
        ast->right = std::unique_ptr<ASTBase>($3);
        $$ = ast.release();
    }
    | MulExp MOD UnaryExp {
        auto ast = std::make_unique<MulExpNodeOp>();
        ast->op = OP_MOD;
        ast->left = std::unique_ptr<ASTBase>($1);
        ast->right = std::unique_ptr<ASTBase>($3);
        $$ = ast.release();
    }
    ;

AddExp
    : MulExp {
        auto ast = std::make_unique<AddExpNodeReduce>();
        ast->expr = std::unique_ptr<ASTBase>($1);
        $$ = ast.release();
    }
    | AddExp ADD MulExp {
        auto ast = std::make_unique<AddExpNodeOp>();
        ast->op = OP_ADD;
        ast->left = std::unique_ptr<ASTBase>($1);
        ast->right = std::unique_ptr<ASTBase>($3);
        $$ = ast.release();
    }
    | AddExp SUB MulExp {
        auto ast = std::make_unique<AddExpNodeOp>();
        ast->op = OP_SUB;
        ast->left = std::unique_ptr<ASTBase>($1);
        ast->right = std::unique_ptr<ASTBase>($3);
        $$ = ast.release();
    }
    ;

RelExp
    : AddExp {
        auto ast = std::make_unique<RelExpNodeReduce>();
        ast->expr = std::unique_ptr<ASTBase>($1);
        $$ = ast.release();
    }
    | RelExp LT AddExp {
        auto ast = std::make_unique<RelExpNodeCompare>();
        ast->op = OP_LT;
        ast->left = std::unique_ptr<ASTBase>($1);
        ast->right = std::unique_ptr<ASTBase>($3);
        $$ = ast.release();
    }
    | RelExp GT AddExp {
        auto ast = std::make_unique<RelExpNodeCompare>();
        ast->op = OP_GT;
        ast->left = std::unique_ptr<ASTBase>($1);
        ast->right = std::unique_ptr<ASTBase>($3);
        $$ = ast.release();
    }
    | RelExp LEQ AddExp {
        auto ast = std::make_unique<RelExpNodeCompare>();
        ast->op = OP_LEQ;
        ast->left = std::unique_ptr<ASTBase>($1);
        ast->right = std::unique_ptr<ASTBase>($3);
        $$ = ast.release();
    }
    | RelExp GEQ AddExp {
        auto ast = std::make_unique<RelExpNodeCompare>();
        ast->op = OP_GEQ;
        ast->left = std::unique_ptr<ASTBase>($1);
        ast->right = std::unique_ptr<ASTBase>($3);
        $$ = ast.release();
    }
    ;

EqExp
    : RelExp {
        auto ast = std::make_unique<EqExpNodeReduce>();
        ast->expr = std::unique_ptr<ASTBase>($1);
        $$ = ast.release();
    }
    | EqExp EQ RelExp {
        auto ast = std::make_unique<EqExpNodeCompare>();
        ast->op = OP_EQ;
        ast->left = std::unique_ptr<ASTBase>($1);
        ast->right = std::unique_ptr<ASTBase>($3);
        $$ = ast.release();
    }
    | EqExp NEQ RelExp {
        auto ast = std::make_unique<EqExpNodeCompare>();
        ast->op = OP_NEQ;
        ast->left = std::unique_ptr<ASTBase>($1);
        ast->right = std::unique_ptr<ASTBase>($3);
        $$ = ast.release();
    }
    ;

LAndExp
    : EqExp {
        auto ast = std::make_unique<LAndExpNodeReduce>();
        ast->expr = std::unique_ptr<ASTBase>($1);
        $$ = ast.release();
    }
    | LAndExp AND EqExp {
        auto ast = std::make_unique<LAndExpNodeLogic>();
        ast->op = OP_AND;
        ast->left = std::unique_ptr<ASTBase>($1);
        ast->right = std::unique_ptr<ASTBase>($3);
        $$ = ast.release();
    }
    ;

LOrExp
    : LAndExp {
        auto ast = std::make_unique<LOrExpNodeReduce>();
        ast->expr = std::unique_ptr<ASTBase>($1);
        $$ = ast.release();
    }
    | LOrExp OR LAndExp {
        auto ast = std::make_unique<LOrExpNodeLogic>();
        ast->op = OP_OR;
        ast->left = std::unique_ptr<ASTBase>($1);
        ast->right = std::unique_ptr<ASTBase>($3);
        $$ = ast.release();
    }
    ;

%%

void yyerror(const char* s) {
    std::cerr << "Error at line " << yylineno << ": " << s
    << " near '" << yytext << "'" << std::endl;
}

void yyerror(std::unique_ptr<ASTBase> &ast, std::unique_ptr<SymbolTable> &symTable, const char *s) {
    std::cerr << "Error at line " << yylineno << ": " << s
    << " near '" << yytext << "'" << std::endl;
}
