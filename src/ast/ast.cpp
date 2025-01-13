#include <iostream>
#include <string>
#include "ast.h"

std::string IndentHelper::current_indent = "";

void CompUnitNode::dump() const {
    std::cout << IndentHelper::current_indent << "CompUnit {" << std::endl;
    IndentHelper::indent();
    for (const auto& item : items) {
        item->dump();
        std::cout << std::endl;
    }
    IndentHelper::dedent();
    std::cout << IndentHelper::current_indent << "}";
}

void NumberNode::dump() const {
    std::visit([](auto&& arg) {
        std::cout << arg;
    }, value);
}

void ExpNode::dump() const {
    std::cout << "Exp { ";
    expr->dump();
    std::cout << " }";
}

void StringNode::dump() const {
    std::cout << "\"" << str << "\"";
}

void CharNode::dump() const {
    std::cout << "\'" << c << "\'";
}

void BooleanNode::dump() const {
    std::cout << val;
}

void DateNode::dump() const {
    std::cout << date;
}

void DeclNode::dump() const {
    std::cout << IndentHelper::current_indent;
    decl->dump();
}

void BTypeNode::dump() const {
    std::cout << type;
}

void ConstDeclNode::dump() const {
    std::cout << "ConstDecl { ";
    std::cout << identifier << ", ";
    val->dump();
    std::cout << " }";
}

void ConstInitValNode::dump() const {
    val->dump();
}

void VarDeclNode::dump() const {
    std::cout << "VarDecl { ";
    std::cout << identifier << ", ";
    btype->dump();
    std::cout << " }";
}

void VarDeclNodeArray::dump() const {
    std::cout << "VarDeclArray { ";
    std::cout << identifier << ", ";
    for (const auto& range : ranges) {
        range->dump();
        std::cout << " ";
    }
    std::cout << ", ";
    btype->dump();
    std::cout << " }";
}

void ArrRangeNode::dump() const {
    std::cout << "ArrRange { ";
    start->dump();
    std::cout << ", ";
    end->dump();
    std::cout << " }";
}

void FuncDefNode::dump() const {
    std::cout << IndentHelper::current_indent << "FuncDef { ";
    func_type->dump();
    std::cout << ", " << identifier << ", ";
    if (param) { param->dump(); } 
    else { std::cout << "no-param"; }
    std::cout << ", ";

    std::cout << std::endl;
    IndentHelper::indent();
    block->dump();
    IndentHelper::dedent();
    std::cout << std::endl;

    std::cout << IndentHelper::current_indent << "}";
}

void ParamListNode::dump() const {
    std::cout << "ParamList { ";
    for (const auto& param : params) {
        param->dump();
        std::cout << " ";
    }
    std::cout << "}";
}

void ParamNode::dump() const {
    std::cout << "Param { " << name << ", ";
    type->dump();
    std::cout << " }";
}

void FuncCallNode::dump() const {
    std::cout << "FuncCall { " << identifier << ", ";
    for (const auto& a : args) {
        a->dump();
        std::cout << " ";
    }
    std::cout << "}";
}

void BlockNode::dump() const {
    std::cout << IndentHelper::current_indent << "Block {" << std::endl;
    IndentHelper::indent();
    for (const auto& item : items) {
        item->dump();
        std::cout << std::endl;
    }
    IndentHelper::dedent();
    std::cout << IndentHelper::current_indent << "}";
}

void BlockItemNode::dump() const {
    stmt->dump();
}

void StmtNodeAssign::dump() const {
    std::cout << IndentHelper::current_indent << "StmtAssign { ";
    lval->dump();
    std::cout << ", ";
    expr->dump();
    std::cout << " }";
}

void StmtNodeIf::dump() const {
    std::cout << IndentHelper::current_indent << "StmtIf { ";
    cond->dump();
    std::cout << ", ";
    
    std::cout << std::endl;
    IndentHelper::indent();
    ifs->dump();
    std::cout << ", ";
    std::cout << std::endl;
    if (elses) { elses->dump(); }
    else { std::cout << IndentHelper::current_indent << "no-else"; }
    IndentHelper::dedent();
    std::cout << std::endl;

    std::cout << IndentHelper::current_indent << "}";
}

void StmtNodeCase::dump() const {
    std::cout << IndentHelper::current_indent << "StmtCase { ";
    std::cout << identifier << ", " << std::endl;
    
    for (const auto& c : cases) {
        c->dump();
        std::cout << std::endl;
    }

    std::cout << IndentHelper::current_indent << "}";
}

void CaseNode::dump() const {
    std::cout << IndentHelper::current_indent << "Case { ";
    from->dump();
    std::cout << ", ";
    if (to) { to->dump(); std::cout << ", "; }
    std::cout << std::endl;
    IndentHelper::indent();
    block->dump();
    IndentHelper::dedent();
    std::cout << std::endl;
    std::cout << IndentHelper::current_indent << "}";
}

void StmtNodeFor::dump() const {
    std::cout << IndentHelper::current_indent << "StmtFor { ";
    std::cout << identifier << ", ";
    start->dump();
    std::cout << ", ";
    end->dump();
    std::cout << ", ";
    if (step) { step->dump(); }
    else { std::cout << "no-step"; }
    std::cout << ", ";

    std::cout << std::endl;
    IndentHelper::indent();
    block->dump();
    IndentHelper::dedent();
    std::cout << std::endl;

    std::cout << IndentHelper::current_indent << "}";
}

void StmtNodeRepeat::dump() const {
    std::cout << IndentHelper::current_indent << "StmtRepeat { ";
    cond->dump();
    std::cout << ", ";

    std::cout << std::endl;
    IndentHelper::indent();
    block->dump();
    IndentHelper::dedent();
    std::cout << std::endl;

    std::cout << IndentHelper::current_indent << "}";
}

void StmtNodeWhile::dump() const {
    std::cout << IndentHelper::current_indent << "StmtWhile { ";
    cond->dump();
    std::cout << ", ";

    std::cout << std::endl;
    IndentHelper::indent();
    block->dump();
    IndentHelper::dedent();
    std::cout << std::endl;
    
    std::cout << IndentHelper::current_indent << "}";
}

void StmtNodeReturn::dump() const {
    std::cout << IndentHelper::current_indent << "StmtReturn { ";
    ret->dump();
    std::cout << " }";
}

void StmtNodeInput::dump() const {
    std::cout << IndentHelper::current_indent << "StmtInput { ";
    std::cout << identifier;
    std::cout << " }";
}

void StmtNodeOutput::dump() const {
    std::cout << IndentHelper::current_indent << "StmtOutput { ";
    for (const auto& element : stream) {
        element->dump();
        std::cout << " ";
    }
    std::cout << "}";
}

void LValNodeId::dump() const {
    std::cout << "LVal { ";
    std::cout << identifier;
    std::cout << " }";
}

void LValNodeArray::dump() const {
    std::cout << "LValArr { ";
    std::cout << identifier << ", ";
    for (const auto& i : index) {
        i->dump();
        std::cout << " ";
    }
    std::cout << "}";
}

void PrimaryExpNode::dump() const {
    expr->dump();
}

void UnaryExpNodeReduce::dump() const {
    expr->dump();
}

void UnaryExpNodeOp::dump() const {
    std::cout << "UnaryExpOp { ";
    op->dump();
    std::cout << ", ";
    expr->dump();
    std::cout << " }";
}

void UnaryOpNode::dump() const {
    std::cout << "UnaryOp { ";
    std::cout << op;
    std::cout << " }";
}

void MulExpNodeReduce::dump() const {
    expr->dump();
}

void MulExpNodeOp::dump() const {
    std::cout << "MulExpOp { " << op << ", ";
    left->dump();
    std::cout << ", ";
    right->dump();
    std::cout << " }";
}

void AddExpNodeReduce::dump() const {
    expr->dump();
}

void AddExpNodeOp::dump() const {
    std::cout << "AddExpOp { " << op << ", ";
    left->dump();
    std::cout << ", ";
    right->dump();
    std::cout << " }";
}

void RelExpNodeReduce::dump() const {
    expr->dump();
}

void RelExpNodeCompare::dump() const {
    std::cout << "RelExpCompare { " << op << ", ";
    left->dump();
    std::cout << ", ";
    right->dump();
    std::cout << " }";
}

void EqExpNodeReduce::dump() const {
    expr->dump();
}

void EqExpNodeCompare::dump() const {
    std::cout << "EqExpCompare { " << op << ", ";
    left->dump();
    std::cout << ", ";
    right->dump();
    std::cout << " }";
}

void LAndExpNodeReduce::dump() const {
    expr->dump();
}

void LAndExpNodeOp::dump() const {
    std::cout << "LAndExpOp { " << op << ", ";
    left->dump();
    std::cout << ", ";
    right->dump();
    std::cout << " }";
}

void LOrExpNodeReduce::dump() const {
    expr->dump();
}

void LOrExpNodeOp::dump() const {
    std::cout << "LOrExpOp { " << op << ", ";
    left->dump();
    std::cout << ", ";
    right->dump();
    std::cout << " }";
}
