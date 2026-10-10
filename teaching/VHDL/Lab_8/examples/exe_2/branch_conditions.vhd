--------------------------------------------------------------------------------
-- EE 362 - Computer Organization Laboratory
-- Lab 8, Example 2 - Every conditional branch, as six Boolean equations
--
-- This is the payoff for the ALU flags you built in Lab 5.
--
-- The ALU gives you exactly two facts about its result:
--     Zero (Z) - the result is zero
--     Neg  (N) - the result's top bit, i.e. it is negative
--
-- From those two bits, EVERY conditional branch in the machine:
--
--   code            meaning     Taken =
--   -------------   ---------   -------------
--   NIAG_COND_NONE  always      1
--   NIAG_COND_EQ    = 0         Z
--   NIAG_COND_NEQ   /= 0        Z'
--   NIAG_COND_GTZ   > 0         N' . Z'
--   NIAG_COND_GEZ   >= 0        N'
--   NIAG_COND_LTZ   < 0         N
--   NIAG_COND_LEZ   <= 0        N + Z
--
-- SIX ONE-LINE EQUATIONS. That is the whole conditional-branch capability of
-- the processor.
--
-- WORTH NOTICING - the pairs are complements:
--     GTZ and LEZ    are complements    (N'Z')' = N + Z
--     GEZ and LTZ    are complements    (N')'   = N
--     EQ  and NEQ    are complements
--
-- So the hardware is SMALLER than the instruction list makes it look. Six named
-- conditions, three complementary pairs plus "always". This is why you read the
-- control table rather than the instruction manual: the manual lists what a
-- programmer can write, the table shows what the hardware actually does.
--
-- WHY 'Taken' IS SEPARATE FROM 'which address'
--   NIAG_sel says WHICH address to use; NIAG_cond says WHETHER to use it. Two
--   separate control fields because they are two separate decisions - and only
--   the relative path is ever conditional. A jump is unconditional by
--   construction; there is no such thing as a conditional J.
--------------------------------------------------------------------------------

library ieee;
use ieee.std_logic_1164.all;

use work.NIAG_Pkg.all;

entity branch_conditions is
    port (
        Cond  : in  std_logic_vector(2 downto 0);   -- NIAG_COND_*
        Zero  : in  std_logic;                      -- ALU Zero flag
        Neg   : in  std_logic;                      -- ALU Neg flag
        Taken : out std_logic
    );
end entity branch_conditions;

architecture rtl of branch_conditions is
begin

    -- One line per condition, each straight from the equation above.
    with Cond select
        Taken <= '1'                        when NIAG_COND_NONE,
                 Zero                       when NIAG_COND_EQ,
                 not Zero                   when NIAG_COND_NEQ,
                 (not Neg) and (not Zero)   when NIAG_COND_GTZ,
                 not Neg                    when NIAG_COND_GEZ,
                 Neg                        when NIAG_COND_LTZ,
                 Neg or Zero                when NIAG_COND_LEZ,
                 '0'                        when others;   -- defined default

end architecture rtl;
