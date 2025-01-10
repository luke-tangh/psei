#ifndef serrors_H
#define serrors_H

#include <string>

enum class ErrorType {
    IdentifierAlreadyDefined,
    IdentifiersDontMatch
};

void semanticError(ErrorType errorType, const std::string& name, int lineNumber);

#endif
