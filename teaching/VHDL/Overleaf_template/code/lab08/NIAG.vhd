-- PLACEHOLDER: replace with YOUR OWN NIAG.vhd
--------------------------------------------------------------------------------
-- EE 362 - Computer Organization Laboratory
-- Lab 8 - Assignment, Part 4 of 4
--
-- NIAG : the complete Next Instruction Address Generator
--
-- YOUR NAME  :
-- SECTION    :  Monday / Tuesday
-- DATE       :
--
-- This is your first INTEGRATION exercise: six components, no new logic.
-- It is a small rehearsal for Lab 12, and worth treating as one - if wiring six
-- blocks is uncomfortable, wiring twelve will be much worse.
--
-- THE STRUCTURE
--
--            +----------+
--     PC --->| NIAG_NSA |--- NSA ---+---------------------+
--       |    +----------+           |                     |
--       |                           v                     v
--       |    Xtnd32 -----------> NIAG_Rel --- Rel ---> +-------+
--       |                                              |       |
--       |    Index ---+                                | NIAG_ |--- NextPC ---+
--       |             +-------> NIAG_Abslt -- Abslt -> |  MUX  |              |
--       |    NSA -----+                                |       |              |
--       |                       RegAddr -------------> +-------+              |
--       |                                                  ^                  |
--       |    Cond, Zero, Neg --> NIAG_Cond --- Taken ------+                  |
--       |                                                                     |
--       +------------------------------ NIAG_Reg <----------------------------+
--                                        (the PC)
--
-- THE RETURN ADDRESS
--   Rtn is simply NSA. When JAL executes, the address to come back to is the
--   instruction after the call - which is exactly PC+4. No hardware needed:
--   it is a wire with a different name, and naming it is what makes the
--   datapath readable.
--
-- WIRING RULES - these matter more than the logic
--   * NAMED ASSOCIATION in every port map: formal => actual. Always. Positional
--     association in a six-component block is how you spend an hour finding a
--     swapped pair of signals.
--   * Declare an internal signal for every wire BETWEEN components. If two
--     components connect, that connection needs a name.
--   * Wire it in the order of the diagram, not the order of your file. Then
--     read it back against the diagram once, before simulating.
--------------------------------------------------------------------------------

library ieee;
use ieee.std_logic_1164.all;

use work.NIAG_Pkg.all;

entity NIAG is
    generic (
        RESET_VEC : natural := 0
    );
    port (
        -- instruction fields
        Index   : in  std_logic_vector(25 downto 0);  -- J index field
        Xtnd32  : in  std_logic_vector(31 downto 0);  -- from the shared ImmedXtnd
        RegAddr : in  std_logic_vector(31 downto 0);  -- register file Bout, for JR

        -- control, from the decoder you write in Labs 10-11
        Sel     : in  std_logic_vector(1 downto 0);   -- NIAG_sel
        Cond    : in  std_logic_vector(2 downto 0);   -- NIAG_cond
        Strb    : in  std_logic;                      -- NIAG_strb: load the PC

        -- status, from the ALU you built in Lab 5
        Zero    : in  std_logic;
        Neg     : in  std_logic;

        Rst     : in  std_logic;
        clk     : in  std_logic;

        -- outputs
        PC      : out std_logic_vector(31 downto 0);
        NSA     : out std_logic_vector(31 downto 0);
        Rtn     : out std_logic_vector(31 downto 0)   -- return address = NSA
    );
end entity NIAG;

architecture structural of NIAG is

    -- TODO 1: declare one internal signal per wire between components.
    --         You need: the PC value, NSA, Rel, Abslt, Taken, NextPC.
    --         Note PC and NSA are also OUTPUTS - you cannot read an 'out'
    --         port, so drive the output from an internal signal.


begin

    -- TODO 2: instantiate the six components, wired per the diagram above.
    --         Named association only.
    --
    --         U_PC    : NIAG_Reg    generic map (RESET_VEC => RESET_VEC)
    --         U_NSA   : NIAG_NSA
    --         U_REL   : NIAG_Rel
    --         U_ABS   : NIAG_Abslt
    --         U_COND  : NIAG_Cond
    --         U_MUX   : NIAG_MUX


    -- TODO 3: drive the three outputs. Rtn is NSA - a wire with a better name.


end architecture structural;
