# PseI

## Checklist
1. Pseudocode in examined components
  - [x] Comments
2. Variables, constants and data types
  - [x] Data Types
  - [x] Literals
  - [x] Identifiers
  - [x] Variable declarations
  - [x] Constants
  - [x] Assignments
3. Arrays
  - [x] Declaring arrays
  - [x] Using arrays
4. User-defined data types
  - [x] Defining user-defined data types
    - [x] Enumerated
    - [x] Pointer
    - [x] Record
    - [x] Set
  - [x] Using user-defined data types
5. Common operations
  - [x] Input and output
  - [x] Arithmetic operations
  - [x] Relational operations
  - [x] Logic operators
  - [ ] String functions and operations
  - [ ] Numeric functions
6. Selection
  - [x] IF statements
  - [x] CASE statements
7. Iteration (repetition)
  - [x] Count-controlled (FOR) loops
  - [x] Post-condition (REPEAT) loops
  - [x] Pre-condition (WHILE) loops
8. Procedures and functions
  - [x] Defining and calling procedures
  - [x] Defining and calling functions
  - [x] Passing parameters by value or by reference
9. File handling
  - [x] Handling text files
  - [x] Handling random files
10. Object-oriented Programming
  - [ ] Methods and Properties
  - [ ] Constructors and Inheritance

## Build

```
mkdir build
cd build
cmake ..
```

```
make
./PseI ../examples/types.pse --show-ast --show-st
...
```

## Test
```
cd build
ctest
```
