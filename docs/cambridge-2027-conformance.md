# Cambridge 2027-2029 conformance matrix

This matrix records the boundary between Cambridge pseudocode, compatibility
allowances and `psei` extensions. The primary reference is the Cambridge
International AS & A Level Computer Science 9618 *Pseudocode Guide for
Teachers* for examinations in 2027, 2028 and 2029.

The labels used here are:

- **formal**: an explicit syntax or presentation rule in the guide;
- **recommendation**: wording such as “usually” or “good practice”;
- **compatibility**: syntax deliberately accepted by normal `psei` execution
  but reported by the `cambridge-2027` profile;
- **extension**: a documented `psei` feature for which the guide defines no
  standard operation.

## Guide coverage

| Guide section | Capability | Execution | `cambridge-2027` check | Boundary |
|---|---|---|---|---|
| 1.1 | Monospaced font and consistent size | Not applicable | Not checkable from plain text | Presentation limitation |
| 1.2 | Structural indentation | Ignored by execution | Checks tabs and three-space nesting | Recommendation |
| 1.3 | Upper-case keywords | Case-insensitive | Checked | Formal |
| 1.3, 2.3 | Mixed-case ASCII identifiers and consistent spelling | Case-insensitive; non-strict mode accepts non-ASCII letters | ASCII and consistent spelling checked; naming style not yet prescribed | Partial |
| 1.4 | Examination line numbers | Preprocessed only by checker | Auto-detected; increasing order checked | Formal, continuation alignment not checkable reliably |
| 1.5 | `//` comments | Supported | Parsed without execution | Formal |
| 2.1-2.2 | Scalar types and literals | Supported, including calendar-valid dates | Parsed | Formal |
| 2.4 | Explicit declarations | Required in strict execution | Undefined reads are errors; inferred assignment remains a normal-mode allowance | Recommendation plus compatibility allowance |
| 2.5 | Literal-only constants | Supported | Parsed | Formal |
| 2.6 | `←` assignment | Supported; non-strict mode also accepts `<-` | `<-` reported as compatibility | Formal plus compatibility allowance |
| 3 | One- and two-dimensional arrays | Supported | Parsed | Formal |
| 3 | Arrays with more than two dimensions | Accepted | Reported as `C2027-X004` | Compatibility allowance |
| 4 | Enumerated, pointer, record and set types | Supported | Parsed | Formal |
| 4 | Named set operations | Supported | Reported as `C2027-X001` | `psei` extension |
| 5 | Input, output, arithmetic, relations, logic and standard functions | Supported | Expressions, operands and standard calls are type-checked | Formal |
| 5.1 | `OUTPUT` without a value | Accepted as a blank line | Reported as `C2027-X002` | Compatibility allowance |
| 6.1 | `IF` selection | Supported | Parsed | Formal |
| 6.2 | `CASE OF <identifier>` and ordered ranges | Supported | Parsed; expression selectors reported as `C2027-X003` | Formal plus compatibility allowance |
| 7 | `FOR`, `REPEAT` and `WHILE` iteration | Supported | Parsed | Formal |
| 7.1 | Repeating the loop identifier after `NEXT` | Optional | Not currently reported | Recommendation |
| 8 | Procedures, functions, `RETURN`, `BYVAL` and `BYREF` | Supported | Calls, arguments, writable `BYREF` values and function return paths are checked | Formal |
| 8.1 | Parentheses in procedure calls | Required by execution | Bare calls receive targeted `C2027-C001` diagnostic | Formal grammar; guide page 19 has an inconsistent example |
| 9 | Text and random file handling | Supported by in-memory and local file systems | Parsed without file access | Formal |
| 10 | Classes, access control, constructors, inheritance and `SUPER` | Supported | Types, members, constructors, inheritance and statically resolvable access are checked | Formal |

## Deliberate normal-mode allowances

Normal, non-strict execution remains useful for teaching and existing source.
It accepts `<-`, inferred variables, non-ASCII alphabetic identifiers, blank
`OUTPUT`, expression selectors in `CASE`, and arrays with more than two
dimensions. These allowances must not be presented as official Cambridge
syntax. The compliance profile reports the allowances that conflict with an
explicit formal format.

## Static semantic boundary

The profile runs the same non-executing semantic analyzer exposed by
`pseudo analyze`. It reports undefined identifiers, invalid types and
operators, call and `BYREF` errors, invalid member access, incomplete function
return paths and unreachable statements with stable `SEM###` codes.

The analyzer is intentionally not a flow-sensitive or interprocedural proof
engine. Explicit-initialization findings are available separately through
`pseudo analyze --recommendations`; value-dependent failures such as array
bounds, division by zero, file state and uninitialized pointers remain runtime
checks.

The profile also does not prescribe camelCase/PascalCase beyond ASCII and
consistent case-insensitive spelling. These gaps are separate from features
that cannot be recovered from plain text, such as font choice and wrapped
continuation-line alignment.
