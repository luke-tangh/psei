#include <iostream>
#include <cassert>
#include <memory>
#include <string>

#include "ast/ast.h"
#include "ast/symbol.h"

extern FILE *yyin;
extern int yyparse(std::unique_ptr<ASTBase> &ast, std::unique_ptr<SymbolTable> &symTable);

int main(int argc, const char *argv[]) {
    if (argc < 2) {
        std::cerr << "Usage: PseI <input> [--show-ast] [--show-st]" << std::endl;
        return 1;
    }

    const char* input = argv[1];

    bool showAST = false;
    bool showST = false;

    for (int i = 2; i < argc; ++i) {
        if (std::string(argv[i]) == "--show-ast") {
            showAST = true;
        } 
        else if (std::string(argv[i]) == "--show-st") {
            showST = true;
        }
    }

    yyin = fopen(input, "r");
    assert(yyin);

    // Parse using Bison
    std::unique_ptr<ASTBase> ast;
    std::unique_ptr<SymbolTable> symTable = std::make_unique<SymbolTable>();
    auto ret = yyparse(ast, symTable);
    assert(!ret);

    if (showAST) {
        ast->dump();
        std::cout << std::endl;
    }

    if (showST) {
        symTable->dump();
        std::cout << std::endl;
    }

    return 0;
}
