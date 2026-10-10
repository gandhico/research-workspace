--------------------------------------------------------------------------------
-- EE 362 - Computer Organization Laboratory
-- Lab 8 - Assignment, Part 3 of 4
--
-- NIAG_MUX : choose the next PC
--
-- YOUR NAME  :
-- SECTION    :  Monday / Tuesday
-- DATE       :
--
-- TWO DECISIONS, NOT ONE. Students routinely try to merge these and it does
-- not work:
--
--     Sel    WHICH address is the candidate?     (NSA / REL / REG / ABS)
--     Taken  is a RELATIVE branch actually used? (from NIAG_Cond)
--
-- and ONLY the relative path is conditional:
--
--   #  Sel            ||  NextPC
--   0  NIAG_SEL_NSA   ||  NSA                        unconditional
--   1  NIAG_SEL_REL   ||  Taken ? Rel : NSA          CONDITIONAL
--   2  NIAG_SEL_REG   ||  RegAddr                    unconditional
--   3  NIAG_SEL_ABS   ||  Abslt                      unconditional
--
-- WHY NOT-TAKEN FALLS BACK TO NSA
--   A branch that is not taken is not a special state - it means "carry on to
--   the next instruction", which is exactly NSA. That is why there is no fifth
--   select code for "branch not taken": the fall-back is already in the table.
--
-- WHY JUMPS ARE UNCONDITIONAL BY CONSTRUCTION
--   There is no conditional J in this instruction set. Conditional control flow
--   uses relative addressing, because conditions are usually local. That is a
--   design decision, not a limitation.
--
-- STRUCTURE: this is Lab 3 again. A 2-to-1 mux (the Taken gate) feeding a
-- 4-to-1 mux (the selection). You may instantiate your Lab 3 Mux2/Mux3 or write
-- it directly - say which in your report.
--------------------------------------------------------------------------------

library ieee;
use ieee.std_logic_1164.all;

use work.NIAG_Pkg.all;

entity NIAG_MUX is
    port (
        Sel     : in  std_logic_vector(1 downto 0);   -- NIAG_SEL_*
        Taken   : in  std_logic;                      -- from NIAG_Cond
        NSA     : in  std_logic_vector(31 downto 0);
        Rel     : in  std_logic_vector(31 downto 0);
        RegAddr : in  std_logic_vector(31 downto 0);
        Abslt   : in  std_logic_vector(31 downto 0);
        NextPC  : out std_logic_vector(31 downto 0)
    );
end entity NIAG_MUX;

architecture rtl of NIAG_MUX is

    -- TODO 1: declare an internal signal for the conditional stage - the
    --         "Rel if taken, otherwise NSA" result. Two stages is much clearer
    --         than one expression, and the RTL Viewer will show both.


begin

    -- TODO 2: the conditional stage (a 2-to-1 mux on Taken).


    -- TODO 3: the selection stage (a 4-to-1 mux on Sel).
    --         Use the NIAG_SEL_* constants. Include 'when others', and make
    --         the default NSA - "carry on" is the safe answer.


end architecture rtl;
