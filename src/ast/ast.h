#ifndef AST_H
#define AST_H

#include <string>
#include <memory>

// Base class for all AST nodes
class ASTNode {
public:
    virtual ~ASTNode() = default;
    virtual int evaluate() = 0;
};

// Node for integer literals
class IntegerNode : public ASTNode {
    int value;
public:
    explicit IntegerNode(int value) : value(value) {}
    int evaluate() override { return value; }
};

// Node for binary operations
class BinaryOpNode : public ASTNode {
    std::string op;
    std::unique_ptr<ASTNode> left;
    std::unique_ptr<ASTNode> right;
public:
    BinaryOpNode(
        const std::string& op, 
        std::unique_ptr<ASTNode> left, 
        std::unique_ptr<ASTNode> right
    ) : op(op), left(std::move(left)), right(std::move(right)) {}

    int evaluate() override;
};

#endif
