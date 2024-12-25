#ifndef AST_H
#define AST_H

#include <iostream>
#include <string>
#include <memory>

// Base class for all AST nodes
class ASTNode {
public:
    virtual ~ASTNode() = default;
    virtual void dump() const = 0;
    //virtual int evaluate() = 0;
};

class CompUnitNode : public ASTNode {
public:
    std::unique_ptr<ASTNode> func_def;

    void dump() const override {
        std::cout << "CompUnitNode { ";
        func_def->dump();
        std::cout << " }";
    }
};

class FuncDefNode : public ASTNode {
public:
    std::string identifier;
    std::unique_ptr<ASTNode> func_type;
    std::unique_ptr<ASTNode> block;

    void dump() const override {
        std::cout << "FuncDefNode { ";
        func_type->dump();
        std::cout << ", " << identifier << ", ";
        block->dump();
        std::cout << " }";
    }
};

class FuncTypeNode : public ASTNode {
public:
    std::string type;

    void dump() const override {
        std::cout << "FuncTypeNode { ";
        std::cout << type;
        std::cout << " }";
    }
};

class BlockNode : public ASTNode {
public:
    std::unique_ptr<ASTNode> stmt;

    void dump() const override {
        std::cout << "BlockNode { ";
        stmt->dump();
        std::cout << " }";
    }
};

class StmtNode : public ASTNode {
public:
    std::unique_ptr<ASTNode> number;

    void dump() const override {
        std::cout << "StmtNode { ";
        number->dump();
        std::cout << " }";
    }
};

class NumberNode : public ASTNode {
public:
    int32_t i32;

    void dump() const override {
        std::cout << i32;
    }
};

#endif
