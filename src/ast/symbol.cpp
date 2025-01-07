#include <iostream>
#include "symbol.h"

SymbolTable::SymbolTable() {
    // Start with a global scope
    enterScope();
}

void SymbolTable::enterScope() {
    scopes.emplace_back(); // Add a new scope
    history.push_back("Entered a new scope (Scope Level " + std::to_string(scopes.size() - 1) + ").");
}

void SymbolTable::exitScope() {
    if (!scopes.empty()) {
        history.push_back("Exited scope (Scope Level " + std::to_string(scopes.size() - 1) + ").");
        scopes.pop_back();
    } else {
        history.push_back("Attempted to exit scope, but no scopes exist.");
    }
}

bool SymbolTable::insert(const std::string& name, const Symbol& symbol) {
    if (scopes.empty()) return false;
    auto& currentScope = scopes.back();

    if (currentScope.find(name) != currentScope.end()) {
        history.push_back("Failed to insert '" + name + "' into Scope Level " +
                          std::to_string(scopes.size() - 1) + ": Symbol already exists.");
        return false; // Symbol already exists in the current scope
    }

    currentScope[name] = symbol;
    history.push_back("Inserted '" + name + "' (" + symbol.type + 
                      ") into Scope Level " + std::to_string(scopes.size() - 1) + 
                      " (line " + std::to_string(symbol.line_number) + ").");
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
    std::cout << "\nSymbol Table Changes:\n";
    for (const auto& action : history) {
        std::cout << action << "\n";
    }
    std::cout << "\nCurrent Symbol Table:\n";

    int scope_level = 0;
    for (const auto& scope : scopes) {
        std::cout << "Scope Level " << scope_level++ << ":\n";
        for (const auto& [name, symbol] : scope) {
            std::cout << "  " << name << " -> " << symbol.type
                      << " (line " << symbol.line_number << ")\n";
        }
    }
}
