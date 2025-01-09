#ifndef AST_H
#define AST_H

#include <iostream>
#include <string>
#include <memory>
#include <vector>
#include <variant>

#define DTYPE_INT  "INTEGER"
#define DTYPE_REAL "REAL"
#define DTYPE_CHAR "CHAR"
#define DTYPE_STR  "STRING"
#define DTYPE_BOOL "BOOLEAN"
#define DTYPE_DATE "DATE"

#define STYPE_VAR   "VARIABLE"
#define STYPE_CONST "CONSTANT"
#define STYPE_FUNC  "FUNCTION"

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

    void dump() const override {
        std::cout << "CompUnitNode {" << std::endl;
        for (const auto& item : items) {
            item->dump();
            std::cout << std::endl;
        }
        std::cout << "}";
    }
};

class NumberNode : public ASTBase {
public:
    std::variant<int32_t, float> value;

    explicit NumberNode(int32_t int_val) : value(int_val) {}
    explicit NumberNode(float float_val) : value(float_val) {}

    void dump() const override {
        std::visit([](auto&& arg) {
            std::cout << arg;
        }, value);
    }
};

class ExpNode : public ASTBase {
public:
    std::unique_ptr<ASTBase> expr;

    void dump() const override {
        std::cout << "ExpNode { ";
        expr->dump();
        std::cout << " }";
    }
};

class StringNode : public ASTBase {
public:
    std::string str;

    void dump() const override {
        //std::cout << "StringNode { ";
        std::cout << "\"" << str << "\"";
        //std::cout << " }";
    }
};

class CharNode : public ASTBase {
public:
    char c;

    void dump() const override {
        //std::cout << "CharNode { ";
        std::cout << "\'" << c << "\'";
        //std::cout << " }";
    }
};

class BooleanNode : public ASTBase {
public:
    bool val;

    void dump() const override {
        //std::cout << "BooleanNode { ";
        std::cout << val;
        //std::cout << " }";
    }
};

class DateNode : public ASTBase {
public:
    std::string date;

    void dump() const override {
        //std::cout << "DateNode { ";
        std::cout << date;
        //std::cout << " }";
    }
};

class DeclNode : public ASTBase {
public:
    std::unique_ptr<ASTBase> decl;

    void dump() const override {
        //std::cout << "DeclNode { ";
        decl->dump();
        //std::cout << " }";
    }
};

class BTypeNode : public ASTBase {
public:
    std::string type;

    void dump() const override {
        //std::cout << "BTypeNode { ";
        std::cout << type;
        //std::cout << " }";
    }
};

class ConstDeclNode : public ASTBase {
public:
    std::string identifier;
    std::unique_ptr<ASTBase> val;

    void dump() const override {
        std::cout << "ConstDeclNode { ";
        std::cout << identifier << ", ";
        val->dump();
        std::cout << " }";
    }
};

class ConstInitValNode : public ASTBase {
public:
    std::unique_ptr<ASTBase> val;

    void dump() const override {
        //std::cout << "ConstInitValNode { ";
        val->dump();
        //std::cout << " }";
    }
};

class VarDeclNode : public ASTBase {
public:
    std::string identifier;
    std::unique_ptr<ASTBase> btype;

    void dump() const override {
        std::cout << "VarDeclNode { ";
        std::cout << identifier << ", ";
        btype->dump();
        std::cout << " }";
    }
};

class FuncDefNode : public ASTBase {
public:
    std::string identifier;
    std::unique_ptr<ASTBase> func_type;
    std::vector<std::unique_ptr<ASTBase>> params;
    std::unique_ptr<ASTBase> block;

    void dump() const override {
        std::cout << "FuncDefNode { ";
        func_type->dump();
        std::cout << ", " << identifier << ", " << std::endl;
        for (const auto& param : params) {
            param->dump();
            std::cout << " ";
        }
        std::cout << std::endl;
        block->dump();
        std::cout << " }";
    }
};

class ParamNode : public ASTBase {
public:
    std::string name;
    std::unique_ptr<ASTBase> type;

    void dump() const override {
        std::cout << "ParamNode { " << name << ", ";
        type->dump();
        std::cout << " }";
    }
};

class FuncTypeNode : public ASTBase {
public:
    std::string type;

    void dump() const override {
        std::cout << "FuncTypeNode { ";
        std::cout << type;
        std::cout << " }";
    }
};

class BlockNode : public ASTBase {
public:
    std::vector<std::unique_ptr<ASTBase>> items;

    void dump() const override {
        std::cout << "BlockNode {" << std::endl;
        for (const auto& item : items) {
            item->dump();
            std::cout << std::endl;
        }
        std::cout << "}";
    }
};

class BlockItemNode : public ASTBase {
public:
    std::unique_ptr<ASTBase> stmt;

    void dump() const override {
        //std::cout << "BlockItem { ";
        stmt->dump();
        //std::cout << " }";
    }
};

class StmtNodeAssign : public ASTBase {
public:
    std::unique_ptr<ASTBase> lval;
    std::unique_ptr<ASTBase> expr;

    void dump() const override {
        std::cout << "StmtNodeAssign { ";
        lval->dump();
        std::cout << ", ";
        expr->dump();
        std::cout << " }";
    }
};

class StmtNodeIf : public ASTBase {
public:
    std::unique_ptr<ASTBase> cond;
    std::unique_ptr<ASTBase> ifs;
    std::unique_ptr<ASTBase> elses;

    void dump() const override {
        std::cout << "StmtNodeIf { " << std::endl;
        cond->dump();
        std::cout << ", " << std::endl;
        ifs->dump();
        std::cout << ", " << std::endl;
        if(elses) elses->dump();
        std::cout << " }";
    }
};

class StmtNodeWhile : public ASTBase {
public:
    std::unique_ptr<ASTBase> cond;
    std::unique_ptr<ASTBase> stmt;

    void dump() const override {
        std::cout << "StmtNodeWhile { " << std::endl;
        cond->dump();
        std::cout << ", " << std::endl;
        stmt->dump();
        std::cout << " }";
    }
};

class StmtNodeReturn : public ASTBase {
public:
    std::unique_ptr<ASTBase> ret;

    void dump() const override {
        std::cout << "StmtNodeReturn { ";
        ret->dump();
        std::cout << " }";
    }
};

class LValNode : public ASTBase {
public:
    std::string identifier;

    void dump() const override {
        //std::cout << "LVal { ";
        std::cout << identifier;
        //std::cout << " }";
    }
};

class PrimaryExpNode : public ASTBase {
public:
    std::unique_ptr<ASTBase> expr;

    void dump() const override {
        //std::cout << "PrimaryExpNode { ";
        expr->dump();
        //std::cout << " }";
    }
};

class UnaryExpNodeReduce : public ASTBase {
public:
    std::unique_ptr<ASTBase> expr;

    void dump() const override {
        //std::cout << "UnaryExpNodeReduce { ";
        expr->dump();
        //std::cout << " }";
    }
};

class UnaryExpNodeOp : public ASTBase {
public:
    std::unique_ptr<ASTBase> op;
    std::unique_ptr<ASTBase> expr;

    void dump() const override {
        std::cout << "UnaryExpNodeOp { ";
        op->dump();
        std::cout << ", ";
        expr->dump();
        std::cout << " }";
    }
};

class UnaryOpNode : public ASTBase {
public:
    std::string op;
    
    void dump() const override {
        std::cout << "UnaryOpNode { ";
        std::cout << op;
        std::cout << " }";
    }
};

class MulExpNodeReduce : public ASTBase {
public:
    std::unique_ptr<ASTBase> expr;

    void dump() const override {
        //std::cout << "MulExpNodeReduce { ";
        expr->dump();
        //std::cout << " }";
    }
};

class MulExpNodeOp : public BinaryOpBase {
public:
    void dump() const override {
        std::cout << "MulExpNodeOp { " << op << ", ";
        left->dump();
        std::cout << ", ";
        right->dump();
        std::cout << " }";
    }
};

class AddExpNodeReduce : public ASTBase {
public:
    std::unique_ptr<ASTBase> expr;

    void dump() const override {
        //std::cout << "AddExpNodeReduce { ";
        expr->dump();
        //std::cout << " }";
    }
};

class AddExpNodeOp : public BinaryOpBase {
public:
    void dump() const override {
        std::cout << "AddExpNodeOp { " << op << ", ";
        left->dump();
        std::cout << ", ";
        right->dump();
        std::cout << " }";
    }
};

class RelExpNodeReduce : public ASTBase {
public:
    std::unique_ptr<ASTBase> expr;

    void dump() const override {
        //std::cout << "RelExpNodeReduce { ";
        expr->dump();
        //std::cout << " }";
    }
};

class RelExpNodeCompare : public BinaryOpBase {
public:
    void dump() const override {
        std::cout << "RelExpNodeCompare { " << op << ", ";
        left->dump();
        std::cout << ", ";
        right->dump();
        std::cout << " }";
    }
};

class EqExpNodeReduce : public ASTBase {
public:
    std::unique_ptr<ASTBase> expr;

    void dump() const override {
        //std::cout << "EqExpNodeReduce { ";
        expr->dump();
        //std::cout << " }";
    }
};

class EqExpNodeCompare : public BinaryOpBase {
public:
    void dump() const override {
        std::cout << "EqExpNodeCompare { " << op << ", ";
        left->dump();
        std::cout << ", ";
        right->dump();
        std::cout << " }";
    }
};

class LAndExpNodeReduce : public ASTBase {
public:
    std::unique_ptr<ASTBase> expr;

    void dump() const override {
        //std::cout << "LAndExpNodeA { ";
        expr->dump();
        //std::cout << " }";
    }
};

class LAndExpNodeLogic : public BinaryOpBase {
public:
    void dump() const override {
        std::cout << "LAndExpNodeB { " << op << ", ";
        left->dump();
        std::cout << ", ";
        right->dump();
        std::cout << " }";
    }
};

class LOrExpNodeReduce : public ASTBase {
public:
    std::unique_ptr<ASTBase> expr;

    void dump() const override {
        //std::cout << "LOrExpNodeReduce { ";
        expr->dump();
        //std::cout << " }";
    }
};

class LOrExpNodeLogic : public BinaryOpBase {
public:
    void dump() const override {
        std::cout << "LOrExpNodeLogic { " << op << ", ";
        left->dump();
        std::cout << ", ";
        right->dump();
        std::cout << " }";
    }
};

#endif
