#ifndef SYMBOL_H
#define SYMBOL_H

#include <string>
#include <unordered_map>
#include <vector>
#include <variant>

#define STYPE_VAR   "VARIABLE"
#define STYPE_CONST "CONSTANT"
#define STYPE_FUNC  "FUNCTION"

struct Symbol {
    std::string name;
    std::string type;
    int line_number;

    Symbol() {};
    Symbol(const std::string& name, const std::string& type, int line_number)
        : name(name), type(type), line_number(line_number) {}
};

class SymbolTable {
private:
    std::vector<std::unordered_map<std::string, Symbol>> scopes;

public:
    SymbolTable();
    void enterScope();
    void exitScope();
    bool insert(const std::string& name, const Symbol& symbol);
    Symbol* lookup(const std::string& name);
    void dump() const;
};

#endif
