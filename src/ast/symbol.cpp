#include <iostream>
#include "symbol.h"

SymbolTable::SymbolTable() {
    // Start with a global scope
    enterScope();
}

void SymbolTable::enterScope() {
    scopes.emplace_back(); // Add a new scope
}

void SymbolTable::exitScope() {
    if (!scopes.empty()) {
        scopes.pop_back(); // Remove the current scope
    }
}

bool SymbolTable::insert(const std::string& name, const Symbol& symbol) {
    if (scopes.empty()) return false;
    auto& currentScope = scopes.back();

    if (currentScope.find(name) != currentScope.end()) {
        return false; // Symbol already exists in the current scope
    }

    currentScope[name] = symbol;
    return true;
}

Symbol* SymbolTable::lookup(const std::string& name) {
    // Search from the innermost scope outward
    for (auto it = scopes.rbegin(); it != scopes.rend(); ++it) {
        auto found = it->find(name);
        if (found != it->end()) {
            return &found->second;
        }
    }
    return nullptr; // Not found
}

void SymbolTable::dump() const {
    int scope_level = 0;
    for (const auto& scope : scopes) {
        std::cout << "Scope Level " << scope_level++ << ":\n";
        for (const auto& [name, symbol] : scope) {
            std::cout << "  " << name << " -> " << symbol.type
                        << " (line " << symbol.line_number << ")\n";
        }
    }
}
