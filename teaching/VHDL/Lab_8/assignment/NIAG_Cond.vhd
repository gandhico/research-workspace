--------------------------------------------------------------------------------
-- EE 362 - Computer Organization Laboratory
-- Lab 8 - Assignment, Part 2 of 4
--
-- NIAG_Cond : is this relative branch actually taken?
--
-- YOUR NAME  :
-- SECTION    :  Monday / Tuesday
-- DATE       :
--
-- THIS IS THE PAYOFF FOR THE ALU FLAGS YOU BUILT IN LAB 5.
--
-- The ALU gives you exactly two facts about its result: Zero and Neg. From
-- those two bits comes every conditional branch the machine has:
--
--   code             meaning     Taken =
--   --------------   ---------   ------------
--   NIAG_COND_NONE   always      1
--   NIAG_COND_EQ     = 0         Z
--   NIAG_COND_NEQ    /= 0        Z'
--   NIAG_COND_GTZ    > 0         N' . Z'
--   NIAG_COND_GEZ    >= 0        N'
--   NIAG_COND_LTZ    < 0         N
--   NIAG_COND_LEZ    <= 0        N + Z
--
-- SIX ONE-LINE BOOLEAN EQUATIONS, and that is the whole conditional-branch
-- capability of the processor. Nothing else is involved.
--
-- WORTH NOTICING BEFORE YOU WRITE IT
--   GTZ and LEZ are complements.   GEZ and LTZ are complements.
--   EQ and NEQ are complements.
--
--   So the hardware is SMALLER than the instruction list suggests. That is a
--   general truth about instruction sets and it is why you read the control
--   table rather than the manual: the manual lists what a programmer may write,
--   the table shows what the hardware actually does.
--
-- Your report must show all six equations and point out the complement pairs.
--
-- THE DEFAULT MATTERS: an unrecognised condition code must produce a DEFINED
-- answer, and the safe one is NOT TAKEN. A CPU that takes a branch it does not
-- understand runs away; one that ignores it merely does the wrong thing slowly.
--------------------------------------------------------------------------------

library ieee;
use ieee.std_logic_1164.all;

use work.NIAG_Pkg.all;

entity NIAG_Cond is
    port (
        Cond  : in  std_logic_vector(2 downto 0);   -- NIAG_COND_*
        Zero  : in  std_logic;                      -- ALU Zero flag
        Neg   : in  std_logic;                      -- ALU Neg flag
        Taken : out std_logic
    );
end entity NIAG_Cond;

architecture rtl of NIAG_Cond is
begin

    -- TODO: implement the seven rows above.
    --       A 'with Cond select' is the natural shape - it is a table, so use
    --       a table construct. Use the NIAG_COND_* constants, never "001".
    --       Do not forget 'when others'.

end architecture rtl;
