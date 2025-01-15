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
    std::vector<std::string> *vec_str_val;
    std::vector<std::unique_ptr<ASTBase>> *vec_ast_val;
}

// Data types
%token INTEGER REAL CHAR STRING BOOLEAN DATE

// Reserved keywords
%token INPUT OUTPUT

// Initialisation
%token DECLARE CONSTANT
%token ARRAY OF

// User-defined datatype
%token TYPE ENDTYPE SET DEFINE

// Selection
%token IF THEN ELSE ENDIF
%token CASE OTHERWISE ENDCASE

// Loops
%token FOR TO STEP NEXT
%token REPEAT UNTIL
%token WHILE ENDWHILE

// Function & Procedure
%token FUNCTION ENDFUNCTION RETURN RETURNS
%token PROCEDURE ENDPROCEDURE
%token BYREF BYVAL

// Reserved Symbols
%token NOT
%token ASSIGN LBRAC RBRAC LSBRAC RSBRAC ADD SUB MUL DIV INTDIV MOD HAT DOT
%token LT GT LEQ GEQ EQ NEQ AND OR COL COMMA

// Token types with semantic values
%token <int_val> INT_CONST
%token <float_val> REAL_CONST
%token <char_val> CHAR_CONST
%token <str_val> STR_CONST DATE_CONST IDENTIFIER
%token <bool_val> BOOL_CONST

// Non-terminal types
%type <str_val> OptionalPassBy OptionalMember
%type <vec_str_val> Enum
%type <ast_val> Number String Char Boolean Date Literial
%type <ast_val> Decl BType ConstDecl VarDecl ArrRange
%type <ast_val> UserDefType PointerOp
%type <ast_val> FuncDef ProcDef ParamList Param
%type <ast_val> Block BlockItem Stmt
%type <ast_val> LVal Case FuncCall
%type <ast_val> OptionalElse OptionalStep OptionalOtherwise
%type <ast_val> Exp PrimaryExp UnaryExp UnaryOp MulExp AddExp RelExp EqExp LAndExp LOrExp
%type <vec_ast_val> ArrRangeList BlockItems Params ArgList CaseItems OptStream Record SetVals

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
    | CompUnit ProcDef {
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

Literial
    : Number | String | Char | Boolean | Date
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
    | IDENTIFIER {
        auto ast = std::make_unique<BTypeNode>();
        ast->type = *std::unique_ptr<std::string>($1);
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
        ast->ranges = std::move(*$6); delete $6;

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

UserDefType
    : TYPE IDENTIFIER EQ LBRAC Enum RBRAC {
        auto ast = std::make_unique<UserDefTypeNodeEnum>();
        ast->identifier = *std::unique_ptr<std::string>($2);
        ast->enums = std::move(*$5); delete $5;

        Symbol sym = Symbol(
            ast->identifier,
            STYPE_ENUM,
            yylineno
        );
        if (!symTable->insert(sym.name, sym)) {
            semanticError(ErrorType::IdentifierAlreadyDefined, sym.name, yylineno);
        }

        $$ = ast.release();
    }
    | TYPE IDENTIFIER EQ HAT BType {
        auto ast = std::make_unique<UserDefTypeNodePointer>();
        ast->identifier = *std::unique_ptr<std::string>($2);
        ast->type = std::unique_ptr<ASTBase>($5);

        Symbol sym = Symbol(
            ast->identifier,
            STYPE_POINTER,
            yylineno
        );
        if (!symTable->insert(sym.name, sym)) {
            semanticError(ErrorType::IdentifierAlreadyDefined, sym.name, yylineno);
        }

        $$ = ast.release();
    }
    | TYPE IDENTIFIER {
        symTable->enterScope();
    } Record {
        symTable->exitScope();
    } ENDTYPE {
        auto ast = std::make_unique<UserDefTypeNodeRecord>();
        ast->identifier = *std::unique_ptr<std::string>($2);
        ast->record = std::move(*$4); delete $4;

        Symbol sym = Symbol(
            ast->identifier,
            STYPE_RECORD,
            yylineno
        );
        if (!symTable->insert(sym.name, sym)) {
            semanticError(ErrorType::IdentifierAlreadyDefined, sym.name, yylineno);
        }

        $$ = ast.release();
    }
    | TYPE IDENTIFIER EQ SET OF BType {
        auto ast = std::make_unique<UserDefTypeNodeSet>();
        ast->identifier = *std::unique_ptr<std::string>($2);
        ast->type = std::unique_ptr<ASTBase>($6);

        Symbol sym = Symbol(
            ast->identifier,
            STYPE_SET,
            yylineno
        );
        if (!symTable->insert(sym.name, sym)) {
            semanticError(ErrorType::IdentifierAlreadyDefined, sym.name, yylineno);
        }

        $$ = ast.release();
    }
    | DEFINE IDENTIFIER LBRAC SetVals RBRAC COL BType {
        auto ast = std::make_unique<UserDefTypeNodeSetDef>();
        ast->identifier = *std::unique_ptr<std::string>($2);
        ast->vals = std::move(*$4); delete $4;
        ast->type = std::unique_ptr<ASTBase>($7);

        Symbol sym = Symbol(
            ast->identifier,
            STYPE_SET_DEF,
            yylineno
        );
        if (!symTable->insert(sym.name, sym)) {
            semanticError(ErrorType::IdentifierAlreadyDefined, sym.name, yylineno);
        }

        $$ = ast.release();
    }
    ;

Enum
    : IDENTIFIER {
        $$ = new std::vector<std::string>();
        $$->push_back(*std::unique_ptr<std::string>($1));
    }
    | Enum COMMA IDENTIFIER {
        $$ = $1;
        $1->push_back(*std::unique_ptr<std::string>($3));
    }
    ;

Record
    : VarDecl {
        $$ = new std::vector<std::unique_ptr<ASTBase>>();
        $$->push_back(std::unique_ptr<ASTBase>($1));
    }
    | Record VarDecl {
        $$ = $1;
        $1->push_back(std::unique_ptr<ASTBase>($2));
    }
    ;

SetVals
    : Literial {
        $$ = new std::vector<std::unique_ptr<ASTBase>>();
        $$->push_back(std::unique_ptr<ASTBase>($1));
    }
    | SetVals COMMA Literial {
        $$ = $1;
        $1->push_back(std::unique_ptr<ASTBase>($3));
    }

PointerOp
    : HAT LVal {
        auto ast = std::make_unique<PointerOpNode>();
        ast->op = PTR_DEREF;
        ast->lval = std::unique_ptr<ASTBase>($2);
        $$ = ast.release();
    }
    | LVal HAT {
        auto ast = std::make_unique<PointerOpNode>();
        ast->op = PTR_GET_ADDR;
        ast->lval = std::unique_ptr<ASTBase>($1);
        $$ = ast.release();
    }
    ;

FuncDef
    : FUNCTION IDENTIFIER LBRAC ParamList RBRAC RETURNS BType Block ENDFUNCTION {
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

ProcDef
    : PROCEDURE IDENTIFIER LBRAC ParamList RBRAC Block ENDPROCEDURE {
        auto ast = std::make_unique<ProcDefNode>();
        ast->identifier = *std::unique_ptr<std::string>($2);
        ast->param = std::unique_ptr<ASTBase>($4);
        ast->block = std::unique_ptr<ASTBase>($6);

        Symbol sym = Symbol(
            ast->identifier,
            STYPE_PROC,
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
        ast->params = std::move(*$1); delete $1;
        $$ = ast.release();
    }
    ;

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
    : OptionalPassBy IDENTIFIER COL BType {
        auto ast = std::make_unique<ParamNode>();
        ast->pass_by = *std::unique_ptr<std::string>($1);
        ast->name = *std::unique_ptr<std::string>($2);
        ast->type = std::unique_ptr<ASTBase>($4);
        $$ = ast.release();
    }
    ;

OptionalPassBy
    : /* empty */ { $$ = new std::string(PASS_BY_DEFAULT); }
    | BYVAL { $$ = new std::string(PASS_BY_VAL); }
    | BYREF { $$ = new std::string(PASS_BY_REF); }
    ;

FuncCall
    : IDENTIFIER LBRAC RBRAC {
        auto ast = std::make_unique<FuncCallNode>();
        ast->identifier = *std::unique_ptr<std::string>($1);
        $$ = ast.release();
    }
    | IDENTIFIER LBRAC ArgList RBRAC {
        auto ast = std::make_unique<FuncCallNode>();
        ast->identifier = *std::unique_ptr<std::string>($1);
        ast->args = std::move(*$3); delete $3;
        $$ = ast.release();
    }

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
        ast->items = std::move(*$2); delete $2;
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
    | UserDefType {
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
    | CASE OF IDENTIFIER CaseItems OptionalOtherwise ENDCASE {
        auto ast = std::make_unique<StmtNodeCase>();
        ast->identifier = *std::unique_ptr<std::string>($3);
        ast->cases = std::move(*$4); delete $4;
        ast->otherwise = std::unique_ptr<ASTBase>($5);
        $$ = ast.release();
    }
    | FOR IDENTIFIER ASSIGN Exp TO Exp OptionalStep Block NEXT IDENTIFIER {
        if (*$2 != *$10) {
            semanticError(ErrorType::IdentifiersDontMatch, (*$2), yylineno);
        }

        auto ast = std::make_unique<StmtNodeFor>();
        ast->identifier = *std::unique_ptr<std::string>($2);
        ast->start = std::unique_ptr<ASTBase>($4);
        ast->end = std::unique_ptr<ASTBase>($6);
        ast->step = std::unique_ptr<ASTBase>($7);
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
    | INPUT IDENTIFIER {
        auto ast = std::make_unique<StmtNodeInput>();
        ast->identifier = *std::unique_ptr<std::string>($2);
        $$ = ast.release();
    }
    | OUTPUT OptStream {
        auto ast = std::make_unique<StmtNodeOutput>();
        ast->stream = std::move(*$2); delete $2;
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

CaseItems
    : Case {
        $$ = new std::vector<std::unique_ptr<ASTBase>>();
        $$->push_back(std::unique_ptr<ASTBase>($1));
    }
    | CaseItems Case {
        $$ = $1;
        $1->push_back(std::unique_ptr<ASTBase>($2));
    }
    ;

Case
    : Literial COL Block {
        auto ast = std::make_unique<CaseNode>();
        ast->from = std::unique_ptr<ASTBase>($1);
        ast->to = nullptr;
        ast->block = std::unique_ptr<ASTBase>($3);
        $$ = ast.release();
    }
    | Literial TO Literial COL Block {
        auto ast = std::make_unique<CaseNode>();
        ast->from = std::unique_ptr<ASTBase>($1);
        ast->to = std::unique_ptr<ASTBase>($3);
        ast->block = std::unique_ptr<ASTBase>($5);
        $$ = ast.release();
    }
    ;

OptionalOtherwise
    : OTHERWISE COL Block {
        $$ = $3;
    }
    | /* Empty */ {
        $$ = nullptr; 
    }
    ;

OptStream
    : Exp {
        $$ = new std::vector<std::unique_ptr<ASTBase>>();
        $$->push_back(std::unique_ptr<ASTBase>($1));
    }
    | OptStream COMMA Exp {
        $$ = $1;
        $1->push_back(std::unique_ptr<ASTBase>($3));
    }
    ;

LVal
    : IDENTIFIER OptionalMember {
        auto ast = std::make_unique<LValNodeId>();
        ast->identifier = *std::unique_ptr<std::string>($1);
        ast->member = *std::unique_ptr<std::string>($2);
        $$ = ast.release();
    }
    | IDENTIFIER LSBRAC ArgList RSBRAC OptionalMember {
        auto ast = std::make_unique<LValNodeArray>();
        ast->identifier = *std::unique_ptr<std::string>($1);
        ast->index = std::move(*$3); delete $3;
        ast->member = *std::unique_ptr<std::string>($5);
        $$ = ast.release();
    }
    ;

OptionalMember
    : /* Empty */ {
        $$ = new std::string();
    }
    | DOT IDENTIFIER {
        $$ = $2;
    }

ArgList
    : Exp {
        $$ = new std::vector<std::unique_ptr<ASTBase>>();
        $$->push_back(std::unique_ptr<ASTBase>($1));
    } 
    | ArgList COMMA Exp {
        $$ = $1;
        $1->push_back(std::unique_ptr<ASTBase>($3));
    }
    ;

PrimaryExp
    : LBRAC Exp RBRAC {
        auto ast = std::make_unique<PrimaryExpNode>();
        ast->expr = std::unique_ptr<ASTBase>($2);
        $$ = ast.release();
    }
    | Literial {
        auto ast = std::make_unique<PrimaryExpNode>();
        ast->expr = std::unique_ptr<ASTBase>($1);
        $$ = ast.release();
    }
    | LVal {
        auto ast = std::make_unique<PrimaryExpNode>();
        ast->expr = std::unique_ptr<ASTBase>($1);
        $$ = ast.release();
    }
    | PointerOp {
        auto ast = std::make_unique<PrimaryExpNode>();
        ast->expr = std::unique_ptr<ASTBase>($1);
        $$ = ast.release();
    }
    | FuncCall {
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
        auto ast = std::make_unique<LAndExpNodeOp>();
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
        auto ast = std::make_unique<LOrExpNodeOp>();
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
