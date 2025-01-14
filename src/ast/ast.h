#ifndef AST_H
#define AST_H

#include <iostream>
#include <string>
#include <memory>
#include <vector>
#include <variant>

#define DTYPE_INT       "INTEGER"
#define DTYPE_REAL      "REAL"
#define DTYPE_CHAR      "CHAR"
#define DTYPE_STR       "STRING"
#define DTYPE_BOOL      "BOOLEAN"
#define DTYPE_DATE      "DATE"

#define STYPE_VAR       "VARIABLE"
#define STYPE_CONST     "CONSTANT"
#define STYPE_FUNC      "FUNCTION"
#define STYPE_PROC      "PROCEDURE"

#define PASS_BY_DEFAULT "BY_DEFAULT"
#define PASS_BY_REF     "BY_REF"
#define PASS_BY_VAL     "BY_VAL"

#define OP_ADD    "ADD"
#define OP_SUB    "SUB"
#define OP_NOT    "NOT"
#define OP_MUL    "MUL"
#define OP_DIV    "DIV"
#define OP_INTDIV "INTDIV"
#define OP_MOD    "MOD"
#define OP_LT     "LT"
#define OP_GT     "GT"
#define OP_LEQ    "LEQ"
#define OP_GEQ    "GEQ"
#define OP_EQ     "EQ"
#define OP_NEQ    "NEQ"
#define OP_AND    "AND"
#define OP_OR     "OR"
#define OP_COL    "COL"

class IndentHelper {
public:
    static std::string current_indent;
    
    static void indent() {
        current_indent += "  ";
    }
    
    static void dedent() {
        if (current_indent.size() >= 2) {
            current_indent.resize(current_indent.size() - 2);
        }
    }
};

// Base class for all AST nodes
class ASTBase {
public:
    virtual ~ASTBase() = default;
    virtual void dump() const = 0;
    //virtual int eval() = 0;
};

class BinaryOpBase : public ASTBase {
public:
    std::string op;
    std::unique_ptr<ASTBase> left;
    std::unique_ptr<ASTBase> right;
};

class CompUnitNode : public ASTBase {
public:
    std::vector<std::unique_ptr<ASTBase>> items;
    void dump() const override;
};

class NumberNode : public ASTBase {
public:
    std::variant<int32_t, float> value;

    explicit NumberNode(int32_t int_val) : value(int_val) {}
    explicit NumberNode(float float_val) : value(float_val) {}

    void dump() const override;
};

class ExpNode : public ASTBase {
public:
    std::unique_ptr<ASTBase> expr;
    void dump() const override;
};

class StringNode : public ASTBase {
public:
    std::string str;
    void dump() const override;
};

class CharNode : public ASTBase {
public:
    char c;
    void dump() const override;
};

class BooleanNode : public ASTBase {
public:
    bool val;
    void dump() const override;
};

class DateNode : public ASTBase {
public:
    std::string date;
    void dump() const override;
};

class DeclNode : public ASTBase {
public:
    std::unique_ptr<ASTBase> decl;
    void dump() const override;
};

class BTypeNode : public ASTBase {
public:
    std::string type;
    void dump() const override;
};

class ConstDeclNode : public ASTBase {
public:
    std::string identifier;
    std::unique_ptr<ASTBase> val;

    void dump() const override;
};

class ConstInitValNode : public ASTBase {
public:
    std::unique_ptr<ASTBase> val;
    void dump() const override;
};

class VarDeclNode : public ASTBase {
public:
    std::string identifier;
    std::unique_ptr<ASTBase> btype;

    void dump() const override;
};

class VarDeclNodeArray : public ASTBase {
public:
    std::string identifier;
    std::unique_ptr<ASTBase> btype;
    std::vector<std::unique_ptr<ASTBase>> ranges;

    void dump() const override;
};

class ArrRangeNode : public ASTBase {
public:
    std::unique_ptr<ASTBase> start;
    std::unique_ptr<ASTBase> end;

    void dump() const override;
};

class FuncDefNode : public ASTBase {
public:
    std::string identifier;
    std::unique_ptr<ASTBase> func_type;
    std::unique_ptr<ASTBase> param;
    std::unique_ptr<ASTBase> block;

    void dump() const override;
};

class ProcDefNode : public ASTBase {
public:
    std::string identifier;
    std::unique_ptr<ASTBase> param;
    std::unique_ptr<ASTBase> block;

    void dump() const override;
};

class ParamListNode : public ASTBase {
public:
    std::vector<std::unique_ptr<ASTBase>> params;
    void dump() const override;
};

class ParamNode : public ASTBase {
public:
    std::string pass_by;
    std::string name;
    std::unique_ptr<ASTBase> type;

    void dump() const override;
};

class FuncCallNode : public ASTBase {
public:
    std::string identifier;
    std::vector<std::unique_ptr<ASTBase>> args;
    void dump() const override;
};

class BlockNode : public ASTBase {
public:
    std::vector<std::unique_ptr<ASTBase>> items;
    void dump() const override;
};

class BlockItemNode : public ASTBase {
public:
    std::unique_ptr<ASTBase> stmt;
    void dump() const override;
};

class StmtNodeAssign : public ASTBase {
public:
    std::unique_ptr<ASTBase> lval;
    std::unique_ptr<ASTBase> expr;

    void dump() const override;
};

class StmtNodeIf : public ASTBase {
public:
    std::unique_ptr<ASTBase> cond;
    std::unique_ptr<ASTBase> ifs;
    std::unique_ptr<ASTBase> elses;

    void dump() const override;
};

class StmtNodeCase : public ASTBase {
public:
    std::string identifier;
    std::vector<std::unique_ptr<ASTBase>> cases;
    std::unique_ptr<ASTBase> otherwise;

    void dump() const override;
};

class CaseNode : public ASTBase {
public:
    std::unique_ptr<ASTBase> from;
    std::unique_ptr<ASTBase> to;
    std::unique_ptr<ASTBase> block;

    void dump() const override;
};

class StmtNodeFor : public ASTBase {
public:
    std::string identifier;
    std::unique_ptr<ASTBase> start;
    std::unique_ptr<ASTBase> end;
    std::unique_ptr<ASTBase> step;
    std::unique_ptr<ASTBase> block;

    void dump() const override;
};

class StmtNodeRepeat : public ASTBase {
public:
    std::unique_ptr<ASTBase> cond;
    std::unique_ptr<ASTBase> block;

    void dump() const override;
};

class StmtNodeWhile : public ASTBase {
public:
    std::unique_ptr<ASTBase> cond;
    std::unique_ptr<ASTBase> block;

    void dump() const override;
};

class StmtNodeReturn : public ASTBase {
public:
    std::unique_ptr<ASTBase> ret;
    void dump() const override;
};

class StmtNodeInput : public ASTBase {
public:
    std::string identifier;
    void dump() const override;
};

class StmtNodeOutput : public ASTBase {
public:
    std::vector<std::unique_ptr<ASTBase>> stream;
    void dump() const override;
};

class LValNodeId : public ASTBase {
public:
    std::string identifier;
    void dump() const override;
};

class LValNodeArray : public ASTBase {
public:
    std::string identifier;
    std::vector<std::unique_ptr<ASTBase>> index;

    void dump() const override;
};

class PrimaryExpNode : public ASTBase {
public:
    std::unique_ptr<ASTBase> expr;
    void dump() const override;
};

class UnaryExpNodeReduce : public ASTBase {
public:
    std::unique_ptr<ASTBase> expr;
    void dump() const override;
};

class UnaryExpNodeOp : public ASTBase {
public:
    std::unique_ptr<ASTBase> op;
    std::unique_ptr<ASTBase> expr;

    void dump() const override;
};

class UnaryOpNode : public ASTBase {
public:
    std::string op;
    void dump() const override;
};

class MulExpNodeReduce : public ASTBase {
public:
    std::unique_ptr<ASTBase> expr;
    void dump() const override;
};

class MulExpNodeOp : public BinaryOpBase {
public:
    void dump() const override;
};

class AddExpNodeReduce : public ASTBase {
public:
    std::unique_ptr<ASTBase> expr;
    void dump() const override;
};

class AddExpNodeOp : public BinaryOpBase {
public:
    void dump() const override;
};

class RelExpNodeReduce : public ASTBase {
public:
    std::unique_ptr<ASTBase> expr;
    void dump() const override;
};

class RelExpNodeCompare : public BinaryOpBase {
public:
    void dump() const override;
};

class EqExpNodeReduce : public ASTBase {
public:
    std::unique_ptr<ASTBase> expr;
    void dump() const override;
};

class EqExpNodeCompare : public BinaryOpBase {
public:
    void dump() const override;
};

class LAndExpNodeReduce : public ASTBase {
public:
    std::unique_ptr<ASTBase> expr;
    void dump() const override;
};

class LAndExpNodeOp : public BinaryOpBase {
public:
    void dump() const override;
};

class LOrExpNodeReduce : public ASTBase {
public:
    std::unique_ptr<ASTBase> expr;
    void dump() const override;
};

class LOrExpNodeOp : public BinaryOpBase {
public:
    void dump() const override;
};

#endif
