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
    decl->dump();
}

void BTypeNode::dump() const {
    std::cout << type;
}

void ConstDeclNode::dump() const {
    std::cout << IndentHelper::current_indent;
    std::cout << "ConstDecl { ";
    std::cout << identifier << ", ";
    val->dump();
    std::cout << " }";
}

void ConstInitValNode::dump() const {
    val->dump();
}

void VarDeclNode::dump() const {
    std::cout << IndentHelper::current_indent;
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

void UserDefTypeNodeEnum::dump() const {
    std::cout << IndentHelper::current_indent;
    std::cout << "Enum { " << identifier << ", ";
    for (const auto& s : enums) {
        std::cout << s << " ";
    }
    std::cout << "}";
}

void UserDefTypeNodePointer::dump() const {
    std::cout << IndentHelper::current_indent;
    std::cout << "Pointer { " << identifier << ", ";
    type->dump();
    std::cout << " }";
}

void UserDefTypeNodeRecord::dump() const {
    std::cout << IndentHelper::current_indent;
    std::cout << "Record { " << identifier << ", ";
    
    std::cout << std::endl;
    IndentHelper::indent();
        for (const auto& r : record) {
        r->dump();
        std::cout << std::endl;
    }
    IndentHelper::dedent();

    std::cout << IndentHelper::current_indent << "}";
}

void UserDefTypeNodeSet::dump() const {
    std::cout << IndentHelper::current_indent;
    std::cout << "Set { " << identifier << ", ";
    type->dump();
    std::cout << " }";
}

void UserDefTypeNodeSetDef::dump() const {
    std::cout << IndentHelper::current_indent;
    std::cout << "SetDef { " << identifier << ", ";
    type->dump();
    std::cout << ", ";
    for (const auto& val : vals) {
        val->dump();
        std::cout << " ";
    }
    std::cout << "}";
}

void PointerOpNode::dump() const {
    std::cout << "PtrOp { " << op << ", ";
    lval->dump();
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

void ProcDefNode::dump() const {
    std::cout << IndentHelper::current_indent << "ProcDef { ";
    std::cout << identifier << ", ";
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
    std::cout << "Param { ";
    std::cout << pass_by << ", "; 
    std::cout << name << ", ";
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

void StmtNodeOpenFile::dump() const {
    std::cout << IndentHelper::current_indent << "StmtOpenFile { ";
    filename->dump();
    std::cout << ", " << mode;
    std::cout << " }";
}

void StmtNodeReadFile::dump() const {
    std::cout << IndentHelper::current_indent << "StmtReadFile { ";
    filename->dump();
    std::cout << ", " << identifier;
    std::cout << " }";
}

void StmtNodeWriteFile::dump() const {
    std::cout << IndentHelper::current_indent << "StmtWriteFile { ";
    filename->dump();
    std::cout << ", ";
    expr->dump();
    std::cout << " }";
}

void StmtNodeCloseFile::dump() const {
    std::cout << IndentHelper::current_indent << "StmtCloseFile { ";
    filename->dump();
    std::cout << " }";
}

void StmtNodeSeek::dump() const {
    std::cout << IndentHelper::current_indent << "StmtSeek { ";
    filename->dump();
    std::cout << ", ";
    pos->dump();
    std::cout << " }";
}

void StmtNodeGetRecord::dump() const {
    std::cout << IndentHelper::current_indent << "StmtGetRecord { ";
    filename->dump();
    std::cout << ", " << identifier;
    std::cout << " }";
}

void StmtNodePutRecord::dump() const {
    std::cout << IndentHelper::current_indent << "StmtPutRecord { ";
    filename->dump();
    std::cout << ", " << identifier;
    std::cout << " }";
}

void LValNodeId::dump() const {
    std::cout << "LVal { ";
    std::cout << identifier;
    if (!member.empty()) {
        std::cout << "." << member;
    }
    std::cout << " }";
}

void LValNodeArray::dump() const {
    std::cout << "LValArr { ";
    std::cout << identifier << ", ";
    for (const auto& i : index) {
        i->dump();
        std::cout << " ";
    }
    if (!member.empty()) {
        std::cout << "." << member << " ";
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

void EOFExpNode::dump() const {
    std::cout << "EOF { ";
    filename->dump();
    std::cout << " }";
}
