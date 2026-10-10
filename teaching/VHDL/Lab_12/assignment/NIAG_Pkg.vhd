--------------------------------------------------------------------------------
-- EE 362 - Computer Organization Laboratory
-- Lab 8 - NIAG select and condition codes   *** PROVIDED COMPLETE - DO NOT EDIT ***
--
-- Same idea as Lab 5's ALU_Pkg: named constants instead of raw bit patterns, so
-- a typo becomes a compile error rather than a wrong answer.
--
-- These codes come from the original EE 362 CPU library, so the NIAG you build
-- here is the one your decoder drives in Labs 10-11 and your CPU uses in Lab 12.
--------------------------------------------------------------------------------

library ieee;
use ieee.std_logic_1164.all;

package NIAG_Pkg is

    ----------------------------------------------------------------------------
    -- WHICH ADDRESS does the PC take next?
    ----------------------------------------------------------------------------
    constant NIAG_SEL_NSA : std_logic_vector(1 downto 0) := "00";  -- PC + 4
    constant NIAG_SEL_REL : std_logic_vector(1 downto 0) := "01";  -- branch target
    constant NIAG_SEL_REG : std_logic_vector(1 downto 0) := "10";  -- register (JR)
    constant NIAG_SEL_ABS : std_logic_vector(1 downto 0) := "11";  -- jump target

    ----------------------------------------------------------------------------
    -- UNDER WHAT CONDITION is a relative branch actually taken?
    --
    -- These are evaluated against the ALU's Zero and Neg flags from Lab 5.
    -- NIAG_SEL_REL selects the branch target; NIAG_COND decides whether it is
    -- used at all. Two separate decisions, two separate control fields.
    ----------------------------------------------------------------------------
    constant NIAG_COND_NONE : std_logic_vector(2 downto 0) := "000";  -- always
    constant NIAG_COND_EQ   : std_logic_vector(2 downto 0) := "001";  -- = 0
    constant NIAG_COND_NEQ  : std_logic_vector(2 downto 0) := "010";  -- /= 0
    constant NIAG_COND_GTZ  : std_logic_vector(2 downto 0) := "011";  -- > 0
    constant NIAG_COND_GEZ  : std_logic_vector(2 downto 0) := "100";  -- >= 0
    constant NIAG_COND_LTZ  : std_logic_vector(2 downto 0) := "101";  -- < 0
    constant NIAG_COND_LEZ  : std_logic_vector(2 downto 0) := "110";  -- <= 0

end package NIAG_Pkg;
