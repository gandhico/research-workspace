--------------------------------------------------------------------------------
-- EE 362 - Computer Organization Laboratory
-- Lab 5 - ALU function codes           *** PROVIDED COMPLETE - DO NOT EDIT ***
--
-- A PACKAGE is a named collection of declarations that several files can share.
-- Put a constant here once and every file that says
--
--     use work.ALU_Pkg.all;
--
-- can use it. Change it here and every user changes with it.
--
-- WHY THIS MATTERS MORE THAN IT LOOKS
--   Your ALU will select among sixteen operations using a 5-bit code. You could
--   write  when "01001" =>  in the ALU and  Func <= "01001";  in the testbench,
--   and then spend twenty minutes finding out you typed "01010" in one of them.
--   With the package you write ALU_FUNC_SOLS in both places, and a typo becomes
--   a compile error instead of a wrong answer.
--
--   NAMED CONSTANTS TURN SILENT BUGS INTO LOUD ONES. That is the whole point.
--
-- These codes come from the original EE 362 CPU library, so the ALU you build
-- here is the one the CPU expects in Lab 12.
--------------------------------------------------------------------------------

library ieee;
use ieee.std_logic_1164.all;

package ALU_Pkg is

    -- Arithmetic
    constant ALU_FUNC_ADD  : std_logic_vector(4 downto 0) := "00000";  -- Ain + Bin
    constant ALU_FUNC_SUB  : std_logic_vector(4 downto 0) := "00001";  -- Ain - Bin
    constant ALU_FUNC_NEG  : std_logic_vector(4 downto 0) := "00110";  -- 0 - Bin

    -- Shifts.  All shift Ain by the amount on the Shft port.
    constant ALU_FUNC_SLA  : std_logic_vector(4 downto 0) := "00111";  -- shift left arithmetic
    constant ALU_FUNC_SRA  : std_logic_vector(4 downto 0) := "01000";  -- shift right arithmetic
    constant ALU_FUNC_SLL  : std_logic_vector(4 downto 0) := "10010";  -- shift left logical
    constant ALU_FUNC_SRL  : std_logic_vector(4 downto 0) := "10011";  -- shift right logical

    -- Set on less than.  Result is 1 or 0, not a comparison flag.
    constant ALU_FUNC_SOLS : std_logic_vector(4 downto 0) := "01001";  -- signed
    constant ALU_FUNC_SOLU : std_logic_vector(4 downto 0) := "01010";  -- unsigned

    -- Bitwise logic
    constant ALU_FUNC_AND  : std_logic_vector(4 downto 0) := "01011";
    constant ALU_FUNC_NAND : std_logic_vector(4 downto 0) := "01100";
    constant ALU_FUNC_OR   : std_logic_vector(4 downto 0) := "01101";
    constant ALU_FUNC_NOR  : std_logic_vector(4 downto 0) := "01110";
    constant ALU_FUNC_XOR  : std_logic_vector(4 downto 0) := "01111";
    constant ALU_FUNC_XNOR : std_logic_vector(4 downto 0) := "10000";
    constant ALU_FUNC_NOT  : std_logic_vector(4 downto 0) := "10001";  -- not Bin

end package ALU_Pkg;
