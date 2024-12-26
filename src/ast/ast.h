#ifndef AST_H
#define AST_H

#include <iostream>
#include <string>
#include <memory>

// Base class for all AST nodes
class ASTBase {
public:
    virtual ~ASTBase() = default;
    virtual void dump() const = 0;
    //virtual int evaluate() = 0;
};

class BinaryOpBase : public ASTBase {
public:
    std::string op;
    std::unique_ptr<ASTBase> left;
    std::unique_ptr<ASTBase> right;
};

class CompUnitNode : public ASTBase {
public:
    std::unique_ptr<ASTBase> func_def;

    void dump() const override {
        std::cout << "CompUnitNode { ";
        func_def->dump();
        std::cout << " }";
    }
};

class FuncDefNode : public ASTBase {
public:
    std::string identifier;
    std::unique_ptr<ASTBase> func_type;
    std::unique_ptr<ASTBase> block;

    void dump() const override {
        std::cout << "FuncDefNode { ";
        func_type->dump();
        std::cout << ", " << identifier << ", ";
        block->dump();
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
    std::unique_ptr<ASTBase> block;

    void dump() const override {
        std::cout << "BlockNode { ";
        block->dump();
        std::cout << " }";
    }
};

class StmtNode : public ASTBase {
public:
    std::unique_ptr<ASTBase> stmt;

    void dump() const override {
        std::cout << "StmtNode { ";
        stmt->dump();
        std::cout << " }";
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

class PrimaryExpNodeA : public ASTBase {
public:
    std::unique_ptr<ASTBase> expr;

    void dump() const override {
        std::cout << "PrimaryExpNodeA { ";
        expr->dump();
        std::cout << " }";
    }
};

class PrimaryExpNodeB : public ASTBase {
public:
    std::unique_ptr<ASTBase> number;

    void dump() const override {
        std::cout << "PrimaryExpNodeB { ";
        number->dump();
        std::cout << " }";
    }
};

class NumberNode : public ASTBase {
public:
    int32_t i32;

    void dump() const override {
        std::cout << "NumberNode { ";
        std::cout << i32;
        std::cout << " }";
    }
};

class UnaryExpNodeA : public ASTBase {
public:
    std::unique_ptr<ASTBase> expr;

    void dump() const override {
        std::cout << "UnaryExpNodeA { ";
        expr->dump();
        std::cout << " }";
    }
};

class UnaryExpNodeB : public ASTBase {
public:
    std::unique_ptr<ASTBase> op;
    std::unique_ptr<ASTBase> expr;

    void dump() const override {
        std::cout << "UnaryExpNodeB { ";
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

class MulExpNodeA : public ASTBase {
public:
    std::unique_ptr<ASTBase> expr;

    void dump() const override {
        std::cout << "MulExpNodeA { ";
        expr->dump();
        std::cout << " }";
    }
};

class MulExpNodeB : public BinaryOpBase {
public:
    void dump() const override {
        std::cout << "MulExpNodeB { " << op << ", ";
        left->dump();
        std::cout << ", ";
        right->dump();
        std::cout << " }";
    }
};

class AddExpNodeA : public ASTBase {
public:
    std::unique_ptr<ASTBase> expr;

    void dump() const override {
        std::cout << "AddExpNodeA { ";
        expr->dump();
        std::cout << " }";
    }
};

class AddExpNodeB : public BinaryOpBase {
public:
    void dump() const override {
        std::cout << "AddExpNodeB { " << op << ", ";
        left->dump();
        std::cout << ", ";
        right->dump();
        std::cout << " }";
    }
};

class RelExpNodeA : public ASTBase {
public:
    std::unique_ptr<ASTBase> expr;

    void dump() const override {
        std::cout << "RelExpNodeA { ";
        expr->dump();
        std::cout << " }";
    }
};

class RelExpNodeB : public BinaryOpBase {
public:
    void dump() const override {
        std::cout << "RelExpNodeB { " << op << ", ";
        left->dump();
        std::cout << ", ";
        right->dump();
        std::cout << " }";
    }
};

class EqExpNodeA : public ASTBase {
public:
    std::unique_ptr<ASTBase> expr;

    void dump() const override {
        std::cout << "EqExpNodeA { ";
        expr->dump();
        std::cout << " }";
    }
};

class EqExpNodeB : public BinaryOpBase {
public:
    void dump() const override {
        std::cout << "EqExpNodeB { " << op << ", ";
        left->dump();
        std::cout << ", ";
        right->dump();
        std::cout << " }";
    }
};

class LAndExpNodeA : public ASTBase {
public:
    std::unique_ptr<ASTBase> expr;

    void dump() const override {
        std::cout << "LAndExpNodeA { ";
        expr->dump();
        std::cout << " }";
    }
};

class LAndExpNodeB : public BinaryOpBase {
public:
    void dump() const override {
        std::cout << "LAndExpNodeB { " << op << ", ";
        left->dump();
        std::cout << ", ";
        right->dump();
        std::cout << " }";
    }
};

class LOrExpNodeA : public ASTBase {
public:
    std::unique_ptr<ASTBase> expr;

    void dump() const override {
        std::cout << "LOrExpNodeA { ";
        expr->dump();
        std::cout << " }";
    }
};

class LOrExpNodeB : public BinaryOpBase {
public:
    void dump() const override {
        std::cout << "LOrExpNodeB { " << op << ", ";
        left->dump();
        std::cout << ", ";
        right->dump();
        std::cout << " }";
    }
};

#endif
