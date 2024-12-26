#include <cassert>
#include <cstdio>
#include <iostream>
#include <memory>
#include <string>

#include "ast/ast.h"

extern FILE *yyin;
extern int yyparse(std::unique_ptr<ASTBase> &ast);

int main(int argc, const char *argv[]) {
    // compiler mode input -o output
    assert(argc == 5);
    //auto mode = argv[1];
    auto input = argv[2];
    //auto output = argv[4];

    yyin = fopen(input, "r");
    assert(yyin);

    std::unique_ptr<ASTBase> ast;
    auto ret = yyparse(ast);
    assert(!ret);

    ast->dump();
    std::cout << std::endl;

    return 0;
}
