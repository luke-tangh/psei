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
  - [ ] Declaring arrays
  - [ ] Using arrays
4. User-defined data types
  - [ ] Defining user-defined data types
    - [ ] Enumerated
    - [ ] Pointer
    - [ ] Record
    - [ ] Set
  - [ ] Using user-defined data types
5. Common operations
  - [ ] Input and output
  - [x] Arithmetic operations
  - [x] Relational operations
  - [x] Logic operators
  - [ ] String functions and operations
  - [ ] Numeric functions
6. Selection
  - [x] IF statements
  - [ ] CASE statements
7. Iteration (repetition)
  - [ ] Count-controlled (FOR) loops
  - [ ] Post-condition (REPEAT) loops
  - [x] Pre-condition (WHILE) loops
8. Procedures and functions
  - [ ] Defining and calling procedures
  - [ ] Defining and calling functions
  - [ ] Passing parameters by value or by reference
9. File handling
  - [ ] Handling text files
  - [ ] Handling random files
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
./PseI ../examples/hello.pse --show-ast --show-st
./PseI ../examples/if.pse --show-ast --show-st
./PseI ../examples/while.pse --show-ast --show-st
./PseI ../examples/scope.pse --show-ast --show-st
./PseI ../examples/datatypes.pse --show-ast --show-st
```


