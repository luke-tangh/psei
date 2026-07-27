# psei

`psei` 是一个轻量级 Cambridge International AS & A Level Computer Science 9618 风格伪代码解释器。

它实现了 Cambridge-style pseudocode 的一个实用子集，可用于：

- 本地运行 `.pseudo` 伪代码文件
- 在 REPL 中交互式测试伪代码
- 在 Python 程序或测试中通过 API 执行伪代码
- 编写教学示例、单元测试和错误用例

> 注意：`psei` 不是 Cambridge 官方工具，也不是完整考试格式校验器。它的目标是提供一个实用、可测试、接近 Cambridge pseudocode 风格的解释器。

---

## 目录

- [功能概览](#功能概览)
- [安装](#安装)
- [CLI 使用](#cli-使用)
- [REPL 使用](#repl-使用)
- [Python API 使用](#python-api-使用)
- [伪代码示例](#伪代码示例)
- [Strict mode](#strict-mode)
- [资源限制](#资源限制)
- [文件处理](#文件处理)
- [用户自定义类型](#用户自定义类型)
- [过程、函数与参数传递](#过程函数与参数传递)
- [面向对象伪代码](#面向对象伪代码)
- [错误处理](#错误处理)
- [开发与测试](#开发与测试)
- [项目结构](#项目结构)
- [当前限制](#当前限制)

---

## 功能概览

当前支持的主要功能包括：

### 基础语言结构

- `DECLARE`
- `CONSTANT`
- 赋值运算符 `←`
- `INPUT`
- `OUTPUT`
- 注释 `//`

### 基本数据类型

- `INTEGER`
- `REAL`
- `CHAR`
- `STRING`
- `BOOLEAN`
- `DATE`

### 表达式与运算

- 算术：
  - `+`
  - `-`
  - `*`
  - `/`
  - `DIV`
  - `MOD`
- 比较：
  - `=`
  - `<>`
  - `<`
  - `<=`
  - `>`
  - `>=`
- 逻辑：
  - `AND`
  - `OR`
  - `NOT`
- 字符串连接：
  - `&`

### 控制结构

- `IF ... THEN ... ELSE ... ENDIF`
- `CASE OF ... OTHERWISE ... ENDCASE`
- `FOR ... TO ... STEP ... NEXT`
- `WHILE ... ENDWHILE`
- `REPEAT ... UNTIL`

### 数组

- 一维数组
- 二维数组
- 固定上下界
- 数组越界检查
- 整个数组赋值，使用复制语义

### 用户自定义类型

- 枚举类型
- 指针类型
- 集合类型
- 记录类型
- 类 / 对象类型

### 子程序

- `PROCEDURE`
- `FUNCTION`
- `CALL`
- `RETURN`
- `BYVAL`
- `BYREF`

### 文件处理

- 文本文件：
  - `OPENFILE ... FOR READ`
  - `OPENFILE ... FOR WRITE`
  - `OPENFILE ... FOR APPEND`
  - `READFILE`
  - `WRITEFILE`
  - `CLOSEFILE`
  - `EOF(...)`
- 随机文件：
  - `OPENFILE ... FOR RANDOM`
  - `SEEK`
  - `GETRECORD`
  - `PUTRECORD`

### 面向对象子集

- `CLASS ... ENDCLASS`
- `PUBLIC`
- `PRIVATE`
- `INHERITS`
- `SUPER`
- 构造器 `PROCEDURE NEW(...)`
- 创建对象：`NEW ClassName(...)`
- 方法调用：`Object.Method(...)`

---

## 安装

### 1. 克隆项目

```bash
git clone <repo-url>
cd psei
```

### 2. 建议创建虚拟环境

Linux / macOS:

```bash
python -m venv .venv
source .venv/bin/activate
```

Windows PowerShell:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

### 3. 安装项目

普通安装：

```bash
python -m pip install --upgrade pip
python -m pip install -e .
```

开发安装：

```bash
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

项目要求：

```text
Python >= 3.10
```

---

## CLI 使用

安装后会提供两个等价命令：

```bash
pseudo
psei
```

### 运行一个伪代码文件

```bash
pseudo run path/to/program.pseudo
```

例如：

```bash
pseudo run examples/passing/declare_assign_output.pseudo
```

也可以使用 Python module 方式运行：

```bash
python -m psei run examples/passing/declare_assign_output.pseudo
```

### 使用 strict mode 运行

```bash
pseudo run path/to/program.pseudo --strict
```

例如：

```bash
pseudo run examples/errors/strict_ascii_assignment.pseudo --strict
```

### CLI 错误行为

如果程序出现词法、语法或运行时错误：

- 错误信息会输出到 `stderr`
- 进程退出码为 `1`

---

## REPL 使用

启动 REPL：

```bash
pseudo repl
```

或：

```bash
python -m psei repl
```

使用 strict mode 启动 REPL：

```bash
pseudo repl --strict
```

REPL 支持的命令：

```text
:help     显示帮助
:vars     显示当前变量
:reset    重置运行时
:quit     退出
:exit     退出
```

示例：

```text
pseudo> DECLARE X : INTEGER
pseudo> X ← 10
pseudo> OUTPUT X + 5
15
pseudo> :vars
X : INTEGER = 10
pseudo> :quit
```

对于需要多行的结构，例如 `IF`、`WHILE`、`PROCEDURE`，REPL 会等待输入完整代码块。

---

## Python API 使用

除了 CLI，`psei` 也可以作为 Python 库使用。

### 执行字符串源码

```python
from psei import run_source

source = """
DECLARE Counter : INTEGER
Counter ← 0
Counter ← Counter + 1
OUTPUT Counter
"""

run_source(source)
```

输出：

```text
1
```

### 捕获 OUTPUT 输出

默认情况下，`OUTPUT` 会调用 Python 的 `print`。如果需要在测试中捕获输出，可以传入自定义 `Runtime`。

```python
from psei import Runtime, run_source

output = []

runtime = Runtime(output_writer=output.append)

run_source("""
OUTPUT "Hello"
OUTPUT "World"
""", runtime)

assert output == ["Hello", "World"]
```

### 提供 INPUT 输入

```python
from psei import Runtime, run_source

inputs = iter(["41"])
output = []

runtime = Runtime(
    input_provider=lambda: next(inputs),
    output_writer=output.append,
)

run_source("""
DECLARE X : INTEGER

INPUT X
OUTPUT X + 1
""", runtime)

assert output == ["42"]
```

### 运行文件

```python
from psei import run_file

run_file("path/to/program.pseudo")
```

`run_file()` 会使用本地文件系统，文件路径相对于伪代码文件所在目录解析。

---

## 伪代码示例

### 基本声明、赋值与输出

```text
DECLARE Counter : INTEGER

Counter ← 0
Counter ← Counter + 1

OUTPUT Counter
```

输出：

```text
1
```

---

### 数组与循环

```text
DECLARE Values : ARRAY[1:4] OF INTEGER
DECLARE I : INTEGER
DECLARE Total : INTEGER

Total ← 0

FOR I ← 1 TO 4
   Values[I] ← I * 2
   Total ← Total + Values[I]
NEXT I

OUTPUT "Total=", Total
```

输出：

```text
Total=20
```

---

### IF 判断

```text
DECLARE Score : INTEGER

Score ← 75

IF Score >= 50 THEN
   OUTPUT "Pass"
ELSE
   OUTPUT "Fail"
ENDIF
```

---

### CASE 判断

```text
DECLARE Mark : INTEGER

Mark ← 75

CASE OF Mark
   0 TO 49 : OUTPUT "Fail"
   50 TO 69 : OUTPUT "Pass"
   70 TO 100 : OUTPUT "Distinction"
   OTHERWISE : OUTPUT "Invalid"
ENDCASE
```

---

### WHILE 循环

```text
DECLARE Number : INTEGER

Number ← 27

WHILE Number > 9
   Number ← Number - 9
ENDWHILE

OUTPUT Number
```

输出：

```text
9
```

---

### REPEAT 循环

```text
DECLARE Number : INTEGER

Number ← 0

REPEAT
   Number ← Number + 1
UNTIL Number = 3

OUTPUT Number
```

输出：

```text
3
```

---

## Strict mode

strict mode 是一个有限的 Cambridge-style 防护模式，不是完整格式校验器。

启用 strict mode：

```bash
pseudo run program.pseudo --strict
```

或在 Python API 中：

```python
from psei import Runtime, run_source

runtime = Runtime(strict=True)

run_source("""
DECLARE X : INTEGER
X ← 1
""", runtime, strict=True)
```

strict mode 当前会检查：

- 赋值必须使用 `←`
- ASCII 形式 `<-` 会被拒绝
- 变量赋值前必须先声明
- 标识符只能包含 ASCII 字母、数字和 `_`
- 标识符必须以 ASCII 字母开头

非 strict mode 当前允许：

- 使用 `←` 或 `<-` 赋值
- 对未声明变量赋值时，自动创建并推断类型
- 非 ASCII 字母出现在标识符中

无论是否启用 strict mode，解释器都会执行核心运行时检查，例如：

- 类型检查
- 常量不可重新赋值
- 数组越界检查
- 记录字段检查
- 枚举类型检查
- 文件模式检查
- 除零检查
- 条件表达式必须为 `BOOLEAN`
- `BYREF` 参数必须是可赋值目标
- 函数返回值类型检查

---

## 资源限制

`Runtime` 默认带有保守的执行资源限制，用于避免错误程序或恶意程序拖死解释器。

默认限制：

```python
Runtime(
    max_steps=1_000_000,
    max_array_elements=1_000_000,
    max_call_depth=1_000,
    max_output_chars=1_000_000,
)
```

含义：

| 参数 | 作用 |
|---|---|
| `max_steps` | 最大执行步数，防止无限循环 |
| `max_array_elements` | 单个数组最大元素数，防止巨大数组导致内存耗尽 |
| `max_call_depth` | 最大过程 / 函数 / 方法调用深度，防止无限递归 |
| `max_output_chars` | 最大输出字符数，防止无限输出 |

示例：

```python
from psei import Runtime, run_source
from psei.errors import PseudoRuntimeError

runtime = Runtime(max_steps=1000)

try:
    run_source("""
WHILE TRUE
ENDWHILE
""", runtime)
except PseudoRuntimeError as error:
    print(error)
```

如果确实需要关闭某个限制，可以传入 `None`：

```python
runtime = Runtime(max_steps=None)
```

> 注意：这些限制不是完整安全沙箱。如果要在生产环境运行不可信用户代码，仍建议在进程、容器或操作系统层面增加 CPU、内存和超时限制。

---

## 文件处理

### `run_source()` 中的文件处理

`run_source()` 默认使用内存文件系统。

这意味着：

- 不会在当前目录创建真实文件
- 运行结果可预测
- 适合单元测试和 REPL 场景

示例：

```text
OPENFILE "Log.txt" FOR WRITE
WRITEFILE "Log.txt", "Hello"
CLOSEFILE "Log.txt"

OPENFILE "Log.txt" FOR READ
READFILE "Log.txt", Line
OUTPUT Line
CLOSEFILE "Log.txt"
```

---

### `run_file()` 中的文件处理

`run_file()` 使用本地文件系统。

特点：

- 相对路径以伪代码文件所在目录为根目录
- 不允许绝对路径
- 不允许路径逃逸到程序目录之外
- 文本文件以 UTF-8 读写
- random file 使用 JSON 格式持久化

---

### 文本文件示例

```text
DECLARE LineOfText : STRING

OPENFILE "FileA.txt" FOR WRITE
WRITEFILE "FileA.txt", "First"
WRITEFILE "FileA.txt", "Second"
CLOSEFILE "FileA.txt"

OPENFILE "FileA.txt" FOR READ

WHILE NOT EOF("FileA.txt")
   READFILE "FileA.txt", LineOfText
   OUTPUT LineOfText
ENDWHILE

CLOSEFILE "FileA.txt"
```

---

### 随机文件示例

```text
TYPE StudentRecord
   DECLARE LastName : STRING
   DECLARE YearGroup : INTEGER
ENDTYPE

DECLARE Pupil : StudentRecord
DECLARE Loaded : StudentRecord

Pupil.LastName ← "Johnson"
Pupil.YearGroup ← 6

OPENFILE "StudentFile.Dat" FOR RANDOM

SEEK "StudentFile.Dat", 10
PUTRECORD "StudentFile.Dat", Pupil

SEEK "StudentFile.Dat", 10
GETRECORD "StudentFile.Dat", Loaded

CLOSEFILE "StudentFile.Dat"

OUTPUT Loaded.LastName, ":", Loaded.YearGroup
```

random file 能保存：

- 标量值
- 数组
- 记录
- 集合

random file 不能保存：

- 对象实例
- 指针值

---

## 用户自定义类型

### 枚举类型

```text
TYPE Season = (Spring, Summer, Autumn, Winter)

DECLARE ThisSeason : Season

ThisSeason ← Summer

OUTPUT ThisSeason
```

输出：

```text
Summer
```

枚举值大小写不敏感。

如果变量名和枚举值重名，变量会遮蔽枚举值。

---

### 记录类型

```text
TYPE StudentRecord
   DECLARE LastName : STRING
   DECLARE FirstName : STRING
   DECLARE YearGroup : INTEGER
ENDTYPE

DECLARE Pupil : StudentRecord

Pupil.LastName ← "Johnson"
Pupil.FirstName ← "Leroy"
Pupil.YearGroup ← 6

OUTPUT Pupil.LastName, ",", Pupil.FirstName, ",", Pupil.YearGroup
```

---

### 记录赋值

记录赋值使用复制语义，不会共享字段存储。

```text
DECLARE Pupil1 : StudentRecord
DECLARE Pupil2 : StudentRecord

Pupil1.LastName ← "Johnson"
Pupil1.YearGroup ← 6

Pupil2 ← Pupil1

Pupil1.YearGroup ← 7

OUTPUT Pupil2.YearGroup
OUTPUT Pupil1.YearGroup
```

输出：

```text
6
7
```

---

### 数组中的记录

```text
TYPE StudentRecord
   DECLARE Name : STRING
   DECLARE YearGroup : INTEGER
ENDTYPE

DECLARE Form : ARRAY[1:2] OF StudentRecord

Form[1].Name ← "Ali"
Form[1].YearGroup ← 12

Form[2].Name ← "Mei"
Form[2].YearGroup ← 11

OUTPUT Form[1].Name, ":", Form[1].YearGroup
OUTPUT Form[2].Name, ":", Form[2].YearGroup
```

---

### 指针类型

```text
TYPE TIntPointer = ^INTEGER

DECLARE X : INTEGER
DECLARE P : TIntPointer

X ← 10
P ← ^X

OUTPUT P^

P^ ← 20

OUTPUT X
```

---

### 集合类型

```text
TYPE LetterSet = SET OF CHAR

DEFINE Vowels ('A','E','I','O','U') : LetterSet

OUTPUT Vowels
```

集合目前主要支持定义、赋值和输出占位显示，并没有实现完整集合运算库。

---

## 过程、函数与参数传递

### 过程

```text
PROCEDURE Hello()
   OUTPUT "Hello"
ENDPROCEDURE

CALL Hello()
```

---

### 带参数的过程

```text
PROCEDURE Square(Size : INTEGER)
   FOR Side ← 1 TO 4
      OUTPUT "Side length=", Size
   NEXT Side
ENDPROCEDURE

CALL Square(100)
```

---

### BYVAL

参数默认按值传递。

```text
PROCEDURE AddOne(X : INTEGER)
   X ← X + 1
ENDPROCEDURE

DECLARE A : INTEGER

A ← 5

CALL AddOne(A)

OUTPUT A
```

输出：

```text
5
```

---

### BYREF

`BYREF` 参数会修改调用者传入的变量、数组元素、记录字段或对象属性。

```text
PROCEDURE AddOne(BYREF X : INTEGER)
   X ← X + 1
ENDPROCEDURE

DECLARE A : INTEGER

A ← 5

CALL AddOne(A)

OUTPUT A
```

输出：

```text
6
```

`BYREF` / `BYVAL` 模式会持续作用于后续参数，直到再次显式指定。

```text
PROCEDURE Swap(BYREF X : INTEGER, Y : INTEGER)
   DECLARE Temp : INTEGER

   Temp ← X
   X ← Y
   Y ← Temp
ENDPROCEDURE
```

在上面的例子中，`X` 和 `Y` 都是 `BYREF`。

如果要重置为按值传递：

```text
PROCEDURE Test(BYREF X : INTEGER, BYVAL Y : INTEGER)
   X ← 10
   Y ← 20
ENDPROCEDURE
```

---

### 函数

```text
FUNCTION Max(Number1 : INTEGER, Number2 : INTEGER) RETURNS INTEGER
   IF Number1 > Number2 THEN
      RETURN Number1
   ELSE
      RETURN Number2
   ENDIF
ENDFUNCTION

OUTPUT "Maximum=", Max(10, 20)
```

函数调用必须作为表达式的一部分使用。

正确：

```text
OUTPUT Max(10, 20)
X ← Max(10, 20)
```

错误：

```text
Max(10, 20)
```

函数参数不能使用 `BYREF`。

---

## 面向对象伪代码

### 基本类

```text
CLASS Player
   PRIVATE Attempts : INTEGER

   Attempts ← 3

   PUBLIC PROCEDURE SetAttempts(Number : INTEGER)
      Attempts ← Number
   ENDPROCEDURE

   PUBLIC FUNCTION GetAttempts() RETURNS INTEGER
      RETURN Attempts
   ENDFUNCTION
ENDCLASS

DECLARE P : Player

P ← NEW Player()

OUTPUT P.GetAttempts()

P.SetAttempts(5)

OUTPUT P.GetAttempts()
```

输出：

```text
3
5
```

---

### 构造器

构造器使用名为 `NEW` 的过程。

```text
CLASS Pet
   PRIVATE Name : STRING

   PUBLIC PROCEDURE NEW(GivenName : STRING)
      Name ← GivenName
   ENDPROCEDURE

   PUBLIC FUNCTION GetName() RETURNS STRING
      RETURN Name
   ENDFUNCTION
ENDCLASS

MyPet ← NEW Pet("Kitty")

OUTPUT MyPet.GetName()
```

---

### 继承与 SUPER

```text
CLASS Pet
   PRIVATE Name : STRING

   PUBLIC PROCEDURE NEW(GivenName : STRING)
      Name ← GivenName
   ENDPROCEDURE

   PUBLIC FUNCTION GetName() RETURNS STRING
      RETURN Name
   ENDFUNCTION
ENDCLASS

CLASS Cat INHERITS Pet
   PRIVATE Breed : STRING

   PUBLIC PROCEDURE NEW(GivenName : STRING, GivenBreed : STRING)
      SUPER.NEW(GivenName)
      Breed ← GivenBreed
   ENDPROCEDURE

   PUBLIC FUNCTION GetBreed() RETURNS STRING
      RETURN Breed
   ENDFUNCTION
ENDCLASS

MyCat ← NEW Cat("Kitty", "Shorthaired")

OUTPUT MyCat.GetName()
OUTPUT MyCat.GetBreed()
```

输出：

```text
Kitty
Shorthaired
```

---

### PUBLIC / PRIVATE

`PUBLIC` 成员可以从对象外部访问。

`PRIVATE` 成员只能在声明它的类的方法或初始化语句中访问。

示例：

```text
CLASS Account
   PRIVATE Balance : INTEGER

   PUBLIC PROCEDURE NEW(StartBalance : INTEGER)
      Balance ← StartBalance
   ENDPROCEDURE

   PUBLIC FUNCTION GetBalance() RETURNS INTEGER
      RETURN Balance
   ENDFUNCTION
ENDCLASS

A ← NEW Account(100)

OUTPUT A.GetBalance()
```

下面的外部访问会报错：

```text
OUTPUT A.Balance
```

---

## 内置函数

当前支持：

| 函数 | 说明 |
|---|---|
| `RIGHT(ThisString, x)` | 返回字符串右侧 `x` 个字符 |
| `MID(ThisString, x, y)` | 从第 `x` 位开始返回长度为 `y` 的子串，位置从 `1` 开始 |
| `LENGTH(ThisString)` | 返回字符串长度 |
| `LCASE(ThisChar)` | ASCII 大写字母转小写，其余字符不变 |
| `UCASE(ThisChar)` | ASCII 小写字母转大写，其余字符不变 |
| `INT(x)` | 返回数值整数部分 |
| `RAND(x)` | 返回 `[0, x)` 范围内随机 `REAL` |
| `EOF(file)` | 判断文本文件是否到达末尾 |

示例：

```text
OUTPUT RIGHT("ABCDEFGH", 3)
OUTPUT MID("ABCDEFGH", 2, 3)
OUTPUT LENGTH("Happy Days")
OUTPUT UCASE('h')
OUTPUT LCASE('W')
OUTPUT INT(27.5415)
```

输出：

```text
FGH
BCD
10
H
w
27
```

---

## 错误处理

主要错误类型位于 `psei.errors`：

```python
from psei.errors import (
    PseudoError,
    LexError,
    ParseError,
    IncompleteInput,
    PseudoRuntimeError,
)
```

| 错误类型 | 说明 |
|---|---|
| `LexError` | 词法错误，例如非法字符、非法字符字面量 |
| `ParseError` | 语法错误 |
| `IncompleteInput` | REPL 中输入尚未完整 |
| `PseudoRuntimeError` | 运行时错误，例如类型错误、除零、数组越界 |

示例：

```python
from psei import run_source
from psei.errors import PseudoError

try:
    run_source("""
DECLARE X : INTEGER
X ← "not an integer"
""")
except PseudoError as error:
    print(error)
```

---

## 开发与测试

安装开发依赖：

```bash
python -m pip install -e ".[dev]"
```

运行测试：

```bash
python -m pytest -q
```

项目内置了两类示例：

```text
examples/passing/
examples/errors/
```

其中：

- `examples/passing/*.pseudo` 是应正常运行的程序
- 同名 `.out` 文件保存预期输出
- `examples/errors/*.pseudo` 是应抛出错误的程序
- `examples/errors/manifest.json` 描述预期错误类型

---

## 项目结构

```text
psei/
├── examples/
│   ├── passing/
│   └── errors/
├── src/
│   └── psei/
│       ├── lexer.py
│       ├── parser.py
│       ├── ast_nodes.py
│       ├── interpreter.py
│       ├── runner.py
│       ├── cli.py
│       ├── repl.py
│       ├── runtime/
│       │   ├── core.py
│       │   ├── environment.py
│       │   ├── files.py
│       │   ├── oop.py
│       │   ├── serialization.py
│       │   ├── types.py
│       │   └── values.py
│       ├── tokens.py
│       └── values.py
├── tests/
├── pyproject.toml
└── README.md
```

核心模块说明：

| 文件 / 目录 | 作用 |
|---|---|
| `lexer.py` | 词法分析 |
| `parser.py` | 语法分析，生成 AST |
| `ast_nodes.py` | AST 节点定义 |
| `interpreter.py` | 执行 AST |
| `runtime/core.py` | 运行时对象、作用域、资源限制 |
| `runtime/environment.py` | 变量、常量、引用绑定 |
| `runtime/types.py` | 类型系统、值复制、类型转换 |
| `runtime/files.py` | 文本文件和随机文件抽象 |
| `runtime/oop.py` | 类和对象运行时结构 |
| `runner.py` | `run_source()` / `run_file()` |
| `cli.py` | 命令行入口 |
| `repl.py` | 交互式 REPL |

---

## 当前限制

当前项目实现的是 Cambridge-style pseudocode 的实用子集，而不是完整语言或完整考试格式检查器。

尚未完整实现或不作为重点支持的内容包括：

- Cambridge syllabus 中所有 ADT 库的完整覆盖
  - stack
  - queue
  - linked list
  - dictionary
  - binary tree
- 完整格式 / 风格校验
  - 关键字是否全部大写
  - 缩进是否符合指南
  - 标识符是否符合 mixed case 风格
- 完整集合运算库
- 完整编译器级静态分析
- 进程级安全沙箱

如果需要执行不可信代码，建议结合：

- subprocess 超时
- OS-level memory limit
- container / sandbox
- API 层请求超时和输出大小限制

---

## 最小可用示例

创建文件 `hello.pseudo`：

```text
DECLARE Name : STRING

Name ← "Cambridge pseudocode"

OUTPUT "Hello, ", Name
```

运行：

```bash
pseudo run hello.pseudo
```

输出：

```text
Hello, Cambridge pseudocode
```
