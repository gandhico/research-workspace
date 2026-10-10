# EE362 — VHDL Keyword and Symbol Names

This is a quick-reference list for the main **VHDL keywords, operator symbols, and punctuation symbols** used in the first laboratory examples and in the mathematical-operators guide.

## 1. Arithmetic operators

| VHDL | Name to say aloud | Meaning |
|---|---|---|
| `+` | plus | Addition |
| `-` | minus | Subtraction / unary minus |
| `*` | asterisk / multiply | Multiplication |
| `/` | slash / divide | Division |
| `**` | double asterisk / exponentiation | Raise to a power |
| `mod` | mod / modulus | Modulus |
| `rem` | remainder | Remainder |
| `abs` | absolute value | Absolute value |

## 2. Relational / comparison operators

| VHDL | Name to say aloud | Meaning |
|---|---|---|
| `=` | equals | Equal to |
| `/=` | slash equals / not equal | Not equal to |
| `<` | less than | Less than |
| `<=` | less than or equal to | Comparison when used inside an expression |
| `>` | greater than | Greater than |
| `>=` | greater than or equal to | Greater than or equal to |

> **Important:** `<=` has two common meanings in VHDL.  
> `if a <= b then` → **less than or equal to**  
> `y <= a;` → **signal assignment**

## 3. Logical operators

| VHDL | Name to say aloud | Meaning |
|---|---|---|
| `and` | AND | Logical AND |
| `or` | OR | Logical OR |
| `xor` | exclusive OR / XOR | Logical XOR |
| `xnor` | exclusive NOR / XNOR | Logical XNOR |
| `not` | NOT | Logical inversion |
| `nand` | NAND | NOT-AND |
| `nor` | NOR | NOT-OR |

## 4. Assignment, association, and connection symbols

| VHDL | Name to say aloud | Typical use |
|---|---|---|
| `<=` | signal assignment | `y <= a and b;` |
| `:=` | colon equals / variable assignment | Variables, constants, initialization |
| `=>` | association arrow / maps to | `a => input_a`, `when "00" =>` |
| `&` | ampersand / concatenation | Join bits or vectors |

## 5. Declaration and punctuation symbols

| VHDL | Name to say aloud | Typical use |
|---|---|---|
| `:` | colon | Separates a name from its type/mode |
| `;` | semicolon | Ends most declarations/statements |
| `,` | comma | Separates items |
| `.` | dot / period | Package or selected-name notation |
| `(` | left parenthesis / open parenthesis | Begins a list/expression |
| `)` | right parenthesis / close parenthesis | Ends a list/expression |
| `'` | apostrophe / single quote | Single `std_logic` literal, e.g. `'1'` |
| `"` | double quote | Vector/string literal, e.g. `"1010"` |
| `--` | double hyphen / comment | Starts a VHDL comment |
| `_` | underscore | Used inside identifiers such as `full_adder` |

## 6. Range and indexing keywords

| VHDL | Name to say aloud | Meaning |
|---|---|---|
| `downto` | down to | Descending range |
| `to` | to | Ascending range |

Examples:

```vhdl
std_logic_vector(7 downto 0)
std_logic_vector(0 to 7)
```

## 7. Main structural VHDL keywords

| Keyword | Name / meaning |
|---|---|
| `library` | Declares a library to use |
| `use` | Makes package contents visible |
| `all` | Selects all visible items from a package |
| `entity` | Defines the external hardware interface |
| `is` | Begins the body of a declaration |
| `port` | Declares entity input/output ports |
| `in` | Input port mode |
| `out` | Output port mode |
| `inout` | Bidirectional port mode |
| `buffer` | Output-like port readable internally |
| `end` | Ends a VHDL construct |
| `architecture` | Defines an implementation of an entity |
| `of` | Associates an architecture with an entity |
| `begin` | Begins executable/concurrent statements |
| `signal` | Declares an internal signal/wire |
| `constant` | Declares a constant |
| `variable` | Declares a variable |

## 8. Decision and process keywords

| Keyword | Name / meaning |
|---|---|
| `process` | Groups sequential VHDL statements |
| `if` | Begins a conditional decision |
| `then` | Begins statements for a true condition |
| `elsif` | Else-if condition |
| `else` | Alternative branch |
| `case` | Multi-way selection |
| `when` | Defines a CASE choice or conditional assignment |
| `others` | Covers all remaining choices |
| `loop` | Begins a loop |
| `for` | Counted loop / range iteration |
| `while` | Conditional loop |
| `exit` | Leaves a loop |
| `next` | Skips to the next loop iteration |
| `wait` | Suspends a process in simulation |

## 9. Testbench / verification keywords

| Keyword | Name / meaning |
|---|---|
| `assert` | Checks that a condition is true |
| `report` | Produces a simulator message |
| `severity` | Gives a report/assertion severity level |
| `note` | Low-severity message |
| `warning` | Warning severity |
| `error` | Error severity |
| `failure` | Highest common severity |

## 10. Common VHDL types used in EE362

These are **types/package identifiers**, not reserved keywords, but students will see them constantly.

| Name | Meaning |
|---|---|
| `std_logic` | One multi-valued digital logic signal |
| `std_logic_vector` | Vector of `std_logic` values |
| `unsigned` | Binary vector interpreted as an unsigned number |
| `signed` | Binary vector interpreted as a signed two's-complement number |
| `integer` | Integer numeric type |
| `boolean` | `true` / `false` type |

## 11. Common literal symbols

| VHDL | Name / meaning |
|---|---|
| `'0'` | Logic zero |
| `'1'` | Logic one |
| `'U'` | Uninitialized |
| `'X'` | Unknown |
| `'Z'` | High impedance |
| `'-'` | Don't care |
| `"0000"` | Four-bit vector literal |
| `true` | Boolean true |
| `false` | Boolean false |

## 12. Quick spoken-reference list

```text
+     plus
-     minus
*     asterisk / multiply
/     slash / divide
**    double asterisk / exponentiation
=     equals
/=    not equal
<     less than
<=    less than or equal / signal assignment
>     greater than
>=    greater than or equal
:=    colon equals
=>    association arrow / maps to
&     ampersand / concatenation
:     colon
;     semicolon
,     comma
.     dot / period
'     apostrophe / single quote
"     double quote
--    double hyphen / comment
_     underscore
()    parentheses
```

## 13. First-lab keyword sequence

For the first four EE362 examples, these are the most important words to recognize immediately:

```text
library
use
all
entity
is
port
in
out
end
architecture
of
begin
process
if
then
else
case
when
others
downto
and
or
xor
not
```

The main idea for students is:

```text
ENTITY       -> What signals go in and out?
ARCHITECTURE -> What does the hardware do / contain?
<=           -> What signal receives a value?
PROCESS      -> What grouped behavior is being described?
```
