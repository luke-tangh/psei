#include <cassert>
#include <cstdio>
#include <iostream>
#include <memory>
#include <string>

#include "ast/ast.h"
#include "ast/symbol.h"

extern FILE *yyin;
extern int yyparse(std::unique_ptr<ASTBase> &ast, std::unique_ptr<SymbolTable> &symTable);

int main(int argc, const char *argv[]) {
    // compiler mode input -o output
    assert(argc == 5);
    //auto mode = argv[1];
    auto input = argv[2];
    //auto output = argv[4];

    yyin = fopen(input, "r");
    assert(yyin);

    std::unique_ptr<ASTBase> ast;
    std::unique_ptr<SymbolTable> symTable = std::make_unique<SymbolTable>();
    auto ret = yyparse(ast, symTable);
    assert(!ret);

    ast->dump();
    symTable->dump();
    std::cout << std::endl;

    return 0;
}
