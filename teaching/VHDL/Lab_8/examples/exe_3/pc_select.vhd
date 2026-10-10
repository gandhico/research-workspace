--------------------------------------------------------------------------------
-- EE 362 - Computer Organization Laboratory
-- Lab 8, Example 3 - Choosing the next PC: two decisions, not one
--
-- Students routinely try to merge these into a single control signal, and it
-- does not work. They are genuinely two separate questions:
--
--     NIAG_sel   WHICH address is the candidate?    (NSA / REL / REG / ABS)
--     NIAG_cond  Is a RELATIVE branch actually taken? (from the ALU flags)
--
-- and only the RELATIVE path is conditional:
--
--     sel = NSA  ->  PC+ = NSA                       unconditional
--     sel = REL  ->  PC+ = Taken ? Rel : NSA         CONDITIONAL
--     sel = REG  ->  PC+ = RegAddr                   unconditional
--     sel = ABS  ->  PC+ = Abslt                     unconditional
--
-- WHY NOT-TAKEN FALLS BACK TO NSA
--   A branch that is not taken is not a special state. It simply means "carry
--   on to the next instruction" - which is exactly NSA. That is why there is no
--   fifth select code for "branch not taken": the fall-back is already there.
--
-- WHY JUMPS ARE UNCONDITIONAL BY CONSTRUCTION
--   There is no conditional J in this instruction set. A jump's condition, if
--   it had one, would have to come from the same flags - and that is what
--   branches are for. This is a design decision, not a limitation you have to
--   work around: conditional control flow uses relative addressing because
--   conditions are usually local.
--
-- THE STRUCTURE
--   This is your Lab 3 Mux3/Mux2 work, one more time. The 'Taken' gate is a
--   2-to-1 mux in front of the 4-to-1 mux. Nothing new is being built.
--------------------------------------------------------------------------------

library ieee;
use ieee.std_logic_1164.all;

use work.NIAG_Pkg.all;

entity pc_select is
    port (
        Sel     : in  std_logic_vector(1 downto 0);   -- NIAG_SEL_*
        Taken   : in  std_logic;                      -- from branch_conditions
        NSA     : in  std_logic_vector(31 downto 0);
        Rel     : in  std_logic_vector(31 downto 0);
        RegAddr : in  std_logic_vector(31 downto 0);
        Abslt   : in  std_logic_vector(31 downto 0);
        NextPC  : out std_logic_vector(31 downto 0)
    );
end entity pc_select;

architecture rtl of pc_select is

    -- The conditional stage: a relative branch that is not taken falls back to
    -- the next sequential address. One 2-to-1 mux.
    signal rel_or_nsa : std_logic_vector(31 downto 0);

begin

    rel_or_nsa <= Rel when Taken = '1' else NSA;

    -- The selection stage: one 4-to-1 mux over the four candidate addresses.
    with Sel select
        NextPC <= NSA         when NIAG_SEL_NSA,
                  rel_or_nsa  when NIAG_SEL_REL,
                  RegAddr     when NIAG_SEL_REG,
                  Abslt       when NIAG_SEL_ABS,
                  NSA         when others;   -- safe default: carry on

end architecture rtl;
