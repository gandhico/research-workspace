--------------------------------------------------------------------------------
-- EE 362 - Computer Organization Laboratory
-- Lab 7 - Assignment, Part 3 of 3
--
-- NIAG_Reg : the program counter
--
-- YOUR NAME  :
-- SECTION    :  Monday / Tuesday
-- DATE       :
--
-- SPECIFICATION - Table T
--
--   #  Rst  Strb  Clk    ||  PC+           note
--   0   1    -    -      ||  RESET_VEC     asynchronous, and RESET_VEC = 0
--   1   0    -    not ^  ||  PC            hold between edges
--   2   0    0    ^      ||  PC            edge, but not loading (a stall)
--   3   0    1    ^      ||  NextPC        load
--
-- THIS IS YOUR LAB 2 RegN, RENAMED.
--   Q+ = Rst' . ( Strb.NextPC + Strb'.PC )
--   Compare with Lab 2:  Q+ = Rst' . ( Ld.D + Ld'.Q )
--   Same equation. Ld became Strb, D became NextPC. Nothing new.
--
--   You may either write it out or instantiate your RegN with N => 32. Say in
--   your report which you did and why. (Reusing a tested component is usually
--   the better engineering answer - but the reset VALUE here is not zero in
--   general, so check that your RegN can express it before you rely on it.)
--
-- WHY A LOADABLE REGISTER AND NOT A COUNTER
--   A counter only counts. A program counter must also jump - to a branch
--   target, to a subroutine, back from one. So "advance to the next
--   instruction" is not a special mechanism: it is just loading NSA.
--
--   In Lab 8 you replace the single NextPC input with a multiplexer over five
--   candidate addresses. Sequential execution becomes one input of that mux.
--
-- WHY THE RESET VECTOR MATTERS
--   On reset the PC must go somewhere DEFINED. A PC that powers up at 'U'
--   fetches garbage forever, and every waveform you look at afterwards is
--   meaningless. This is the first thing to check in Lab 12 when nothing works.
--------------------------------------------------------------------------------

library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

entity NIAG_Reg is
    generic (
        RESET_VEC : natural := 0            -- where execution starts
    );
    port (
        NextPC : in  std_logic_vector(31 downto 0);
        Strb   : in  std_logic;             -- load enable
        Rst    : in  std_logic;             -- asynchronous reset
        clk    : in  std_logic;
        PC     : out std_logic_vector(31 downto 0)
    );
end entity NIAG_Reg;

architecture rtl of NIAG_Reg is

    -- TODO 1: declare the register signal, initialised to the reset vector.
    --         to_unsigned(RESET_VEC, 32) converts the generic to a vector.


begin

    -- TODO 2: the register process.
    --         Sensitivity list: the clock, plus the ASYNCHRONOUS control.
    --         Rst first and OUTSIDE the edge test - that is what makes it
    --         asynchronous. Then rising_edge, then Strb.
    --         Exactly the Lab 2 structure.


    -- TODO 3: drive the PC output from your register signal.


end architecture rtl;
