#include "serrors.h"
#include <iostream>
#include <string>

void semanticError(ErrorType errorType, const std::string& name, int lineNumber) {
    std::string message;
    switch (errorType) {
        case ErrorType::IdentifierAlreadyDefined:
            message = "Identifier already defined: " + name;
            break;
        case ErrorType::IdentifiersDontMatch:
            message = "Identifiers in 'FOR' and 'NEXT' do not match: " + name;
            break;
    }
    std::cerr << "Error at line " << lineNumber << ": semantic error, " << message << std::endl;
}
