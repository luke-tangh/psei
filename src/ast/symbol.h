#ifndef SYMBOL_H
#define SYMBOL_H

#include <string>
#include <unordered_map>
#include <vector>
#include <variant>

struct Symbol {
    std::string name;
    std::string type;
    int scope_level;
    int line_number;
    bool is_function;
    std::variant<int, double, char, std::string> value;
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
