--------------------------------------------------------------------------------
-- EE362 - Introduction to Computer Organization Laboratory
-- VHDL GUIDE: Main Mathematical / Arithmetic Operators
--
-- PURPOSE
--   This file is a commented reference for the main VHDL mathematical
--   operators and their symbols/keywords.
--
-- IMPORTANT
--   For arithmetic with std_logic_vector-like buses, use IEEE.NUMERIC_STD
--   and the types UNSIGNED or SIGNED.
--
--   std_logic_vector by itself is mainly a collection of logic values.
--   UNSIGNED and SIGNED give the vector a numeric interpretation.
--
-- MAIN ARITHMETIC OPERATORS
--
--   Symbol / Keyword      Meaning
--   ----------------      ----------------------------------------------
--          +              Addition
--          -              Subtraction / unary minus
--          *              Multiplication
--          /              Division
--         mod             Modulus
--         rem             Remainder
--         abs             Absolute value
--          **             Exponentiation
--
-- MAIN RELATIONAL OPERATORS
--
--          =              Equal to
--         /=              Not equal to
--          <              Less than
--         <=              Less than or equal to   [inside expressions]
--          >              Greater than
--         >=              Greater than or equal to
--
-- IMPORTANT: <= HAS TWO COMMON ROLES IN VHDL
--
--   y <= a + b;           Signal assignment
--
--   if a <= b then        Relational comparison: "a less than or equal to b"
--
-- The meaning depends on the CONTEXT.
--
-- OTHER USEFUL SYMBOLS / KEYWORDS
--
--         :=              Variable / constant initialization or assignment
--         =>              Association, mapping, or CASE choice
--          &              Concatenation
--        downto           Descending range direction
--          to             Ascending range direction
--
-- LOGICAL OPERATORS OFTEN USED WITH DIGITAL EQUATIONS
--
--         and             Logical AND
--          or             Logical OR
--         xor             Exclusive OR
--        xnor             Exclusive NOR
--         not             Logical NOT
--        nand             NAND
--         nor             NOR
--
-- NOTE
--   "mod", "rem", "abs", "and", "or", "xor", etc. are KEYWORDS.
--   "+", "-", "*", "/", "**", "=", "/=", "<", "<=", ">", ">=", "&", ":=",
--   and "=>" are operator/syntax SYMBOLS.
--------------------------------------------------------------------------------

library ieee;
-- Make the IEEE library available.

use ieee.std_logic_1164.all;
-- Defines std_logic and std_logic_vector.

use ieee.numeric_std.all;
-- Defines SIGNED and UNSIGNED arithmetic and conversions such as:
--   to_unsigned(...)
--   to_signed(...)
--   to_integer(...)

entity mathematical_operators_guide is
-- This entity is only a compact teaching example.
-- It is not intended to implement one specific useful circuit.

    port (
        a_u : in  unsigned(7 downto 0);
        -- 8-bit UNSIGNED input.
        -- Numerical range: 0 to 255.

        b_u : in  unsigned(7 downto 0);
        -- Second 8-bit UNSIGNED input.

        a_s : in  signed(7 downto 0);
        -- 8-bit SIGNED input using two's-complement interpretation.
        -- Numerical range: -128 to +127.

        b_s : in  signed(7 downto 0);
        -- Second 8-bit SIGNED input.

        add_u : out unsigned(8 downto 0);
        -- 9-bit output for unsigned addition.
        -- One extra bit is provided to preserve a possible carry.

        sub_s : out signed(8 downto 0);
        -- 9-bit output for signed subtraction.

        mul_u : out unsigned(15 downto 0);
        -- Multiplying two 8-bit unsigned numbers may require up to 16 bits.

        equal_u : out std_logic;
        -- Comparison result: '1' if a_u = b_u.

        less_u : out std_logic
        -- Comparison result: '1' if a_u < b_u.
    );

end entity mathematical_operators_guide;

architecture examples of mathematical_operators_guide is

    constant C1 : integer := 17;
    -- ":=" initializes a CONSTANT.
    -- Here C1 has the integer value 17.

    constant C2 : integer := 5;
    -- Another integer constant used in the commented examples below.

    constant EX_ADD : integer := C1 + C2;
    -- "+" = ADDITION
    -- 17 + 5 = 22

    constant EX_SUB : integer := C1 - C2;
    -- "-" = SUBTRACTION
    -- 17 - 5 = 12

    constant EX_MUL : integer := C1 * C2;
    -- "*" = MULTIPLICATION
    -- 17 * 5 = 85

    constant EX_DIV : integer := C1 / C2;
    -- "/" = INTEGER DIVISION here
    -- 17 / 5 = 3
    -- The fractional part is discarded because the operands are integers.

    constant EX_MOD : integer := C1 mod C2;
    -- "mod" = MODULUS
    -- 17 mod 5 = 2
    --
    -- mod and rem are identical for positive operands.
    -- Their behavior differs for some negative operands.

    constant EX_REM : integer := C1 rem C2;
    -- "rem" = REMAINDER
    -- 17 rem 5 = 2

    constant EX_ABS : integer := abs(-12);
    -- "abs" = ABSOLUTE VALUE
    -- abs(-12) = 12

    constant EX_POW : integer := 2 ** 4;
    -- "**" = EXPONENTIATION
    -- 2 ** 4 = 16

begin

    ----------------------------------------------------------------------------
    -- 1) ADDITION
    ----------------------------------------------------------------------------

    add_u <= ('0' & a_u) + ('0' & b_u);
    -- "+" performs addition.
    --
    -- "&" is CONCATENATION.
    --
    -- '0' & a_u extends the 8-bit value a_u to 9 bits:
    --     a_u       = 1111_1111   (255)
    --     '0'&a_u   = 0_1111_1111
    --
    -- The extra bit allows us to preserve a carry:
    --     255 + 255 = 510
    --
    -- A 9-bit result is therefore required.

    ----------------------------------------------------------------------------
    -- 2) SUBTRACTION
    ----------------------------------------------------------------------------

    sub_s <= resize(a_s, 9) - resize(b_s, 9);
    -- "-" performs subtraction.
    --
    -- resize(...) is provided by numeric_std.
    -- It extends each signed operand to 9 bits before subtraction.
    --
    -- For SIGNED values, resize preserves the sign.

    ----------------------------------------------------------------------------
    -- 3) MULTIPLICATION
    ----------------------------------------------------------------------------

    mul_u <= a_u * b_u;
    -- "*" performs multiplication.
    --
    -- 8-bit x 8-bit unsigned multiplication can require a 16-bit result.
    --
    -- Example:
    --     255 * 255 = 65025

    ----------------------------------------------------------------------------
    -- 4) DIVISION
    ----------------------------------------------------------------------------
    -- Example syntax:
    --
    --     quotient <= a_u / b_u;
    --
    -- "/" performs division.
    --
    -- IMPORTANT:
    --   Division by ZERO is invalid.
    --
    -- IMPORTANT FOR SYNTHESIS:
    --   Division by an arbitrary hardware signal can infer expensive hardware.
    --   Division by a constant power of two can often be implemented much more
    --   efficiently.

    ----------------------------------------------------------------------------
    -- 5) MODULUS
    ----------------------------------------------------------------------------
    -- Example:
    --
    --     result <= value mod divisor;
    --
    -- "mod" returns the modulus.
    --
    -- Integer example:
    --     17 mod 5 = 2
    --
    -- Useful idea:
    --     even/odd checking can be related to modulus by 2.

    ----------------------------------------------------------------------------
    -- 6) REMAINDER
    ----------------------------------------------------------------------------
    -- Example:
    --
    --     result <= value rem divisor;
    --
    -- "rem" returns a remainder.
    --
    -- For positive operands:
    --     17 mod 5 = 2
    --     17 rem 5 = 2
    --
    -- For negative operands, MOD and REM follow different sign rules.
    -- For introductory labs, use them carefully and verify expected behavior
    -- in simulation when negative values are involved.

    ----------------------------------------------------------------------------
    -- 7) ABSOLUTE VALUE
    ----------------------------------------------------------------------------
    -- Example using INTEGER:
    --
    --     magnitude := abs(error);
    --
    -- "abs" removes the sign:
    --     abs(-12) = 12
    --
    -- This keyword is useful whenever only the magnitude matters.

    ----------------------------------------------------------------------------
    -- 8) EXPONENTIATION
    ----------------------------------------------------------------------------
    -- Example:
    --
    --     2 ** 4
    --
    -- "**" means "raised to the power of".
    --
    --     2 ** 4 = 16
    --
    -- In synthesizable hardware, arbitrary exponentiation is generally not a
    -- simple operation. Constant powers are much easier for synthesis tools
    -- to optimize.

    ----------------------------------------------------------------------------
    -- 9) EQUALITY
    ----------------------------------------------------------------------------

    equal_u <= '1' when a_u = b_u else '0';
    -- "=" means EQUAL TO when used inside an expression.
    --
    -- Read:
    --   "equal_u receives 1 when a_u equals b_u, otherwise 0."

    ----------------------------------------------------------------------------
    -- 10) NOT EQUAL
    ----------------------------------------------------------------------------
    -- Example:
    --
    --     if a_u /= b_u then
    --
    -- "/=" means NOT EQUAL TO.

    ----------------------------------------------------------------------------
    -- 11) LESS THAN
    ----------------------------------------------------------------------------

    less_u <= '1' when a_u < b_u else '0';
    -- "<" means LESS THAN.

    ----------------------------------------------------------------------------
    -- 12) LESS THAN OR EQUAL
    ----------------------------------------------------------------------------
    -- Example:
    --
    --     if a_u <= b_u then
    --
    -- Here "<=" means LESS THAN OR EQUAL TO because it appears inside
    -- a Boolean comparison expression.
    --
    -- Compare with:
    --
    --     add_u <= ...
    --
    -- where "<=" means SIGNAL ASSIGNMENT.

    ----------------------------------------------------------------------------
    -- 13) GREATER THAN
    ----------------------------------------------------------------------------
    -- Example:
    --
    --     if a_u > b_u then
    --
    -- ">" means GREATER THAN.

    ----------------------------------------------------------------------------
    -- 14) GREATER THAN OR EQUAL
    ----------------------------------------------------------------------------
    -- Example:
    --
    --     if a_u >= b_u then
    --
    -- ">=" means GREATER THAN OR EQUAL TO.

    ----------------------------------------------------------------------------
    -- 15) UNARY PLUS / MINUS
    ----------------------------------------------------------------------------
    -- Unary minus changes the sign of a numeric value:
    --
    --     -5
    --     -signed_value
    --
    -- Unary plus is also legal:
    --
    --     +5
    --
    -- but is less commonly needed.

    ----------------------------------------------------------------------------
    -- 16) CONCATENATION
    ----------------------------------------------------------------------------
    -- "&" joins values or vectors.
    --
    -- Examples:
    --
    --     '0' & a_u
    --       -> prepend one zero bit
    --
    --     "1010" & "0011"
    --       -> "10100011"
    --
    -- Concatenation is not arithmetic by itself, but is extremely useful
    -- when preparing operands or building buses.

    ----------------------------------------------------------------------------
    -- 17) LOGICAL OPERATORS
    ----------------------------------------------------------------------------
    -- These operators are frequently used in Boolean equations:
    --
    --     a and b
    --     a or b
    --     a xor b
    --     not a
    --     a nand b
    --     a nor b
    --     a xnor b
    --
    -- Example from the Majority-of-Three circuit:
    --
    --     y <= (a and b) or (a and c) or (b and c);
    --
    -- Example from the Full Adder:
    --
    --     sum <= a xor b xor cin;
    --
    --     cout <= (a and b) or
    --             (a and cin) or
    --             (b and cin);

    ----------------------------------------------------------------------------
    -- QUICK SYMBOL / KEYWORD REFERENCE
    ----------------------------------------------------------------------------
    --
    -- ARITHMETIC
    --   +      addition
    --   -      subtraction / unary minus
    --   *      multiplication
    --   /      division
    --   mod    modulus
    --   rem    remainder
    --   abs    absolute value
    --   **     exponentiation
    --
    -- RELATIONAL
    --   =      equal
    --   /=     not equal
    --   <      less than
    --   <=     less than or equal to  [inside an expression]
    --   >      greater than
    --   >=     greater than or equal to
    --
    -- LOGICAL
    --   and    AND
    --   or     OR
    --   xor    exclusive OR
    --   xnor   exclusive NOR
    --   not    NOT
    --   nand   NAND
    --   nor    NOR
    --
    -- OTHER VERY COMMON VHDL SYMBOLS
    --   <=     signal assignment      [outside comparison expressions]
    --   :=     variable/constant assignment or initialization
    --   =>     association / port mapping / CASE association
    --   &      concatenation
    --   '0'    one std_logic value
    --   "0101" std_logic_vector literal
    --   ;      statement/declaration terminator
    --   :      declaration separator
    --   --     comment
    --
    ----------------------------------------------------------------------------

end architecture examples;
