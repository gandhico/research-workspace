--------------------------------------------------------------------------------
-- EE 362 - Lab 12 - REFERENCE COMPONENT
--
-- This is the TA reference implementation, provided so that nobody is blocked
-- from building the CPU by an earlier lab that did not finish.
--
--   >>> REPLACE THIS FILE WITH YOUR OWN VERSION IF YOU HAVE ONE. <<<
--
-- Using a reference component costs you nothing on this lab. Your grade for
-- the earlier lab simply stands as it was. Integration is never gated on an
-- earlier miss - that is a deliberate rule of this course, not a favour.
--------------------------------------------------------------------------------

--------------------------------------------------------------------------------
-- EE 362 - Lab 8 reference component
-- NIAG_Cond : the six branch-condition equations over the ALU flags.
--   NONE=1  EQ=Z  NEQ=Z'  GTZ=N'.Z'  GEZ=N'  LTZ=N  LEZ=N+Z
-- Complement pairs: GTZ/LEZ, GEZ/LTZ, EQ/NEQ.
-- Default is NOT TAKEN: a CPU that takes a branch it does not understand runs
-- away; one that ignores it merely does the wrong thing slowly.
--------------------------------------------------------------------------------
library ieee;
use ieee.std_logic_1164.all;
use work.NIAG_Pkg.all;

entity NIAG_Cond is
    port (
        Cond  : in  std_logic_vector(2 downto 0);
        Zero  : in  std_logic;
        Neg   : in  std_logic;
        Taken : out std_logic
    );
end entity NIAG_Cond;

architecture rtl of NIAG_Cond is
begin
    with Cond select
        Taken <= '1'                      when NIAG_COND_NONE,
                 Zero                     when NIAG_COND_EQ,
                 not Zero                 when NIAG_COND_NEQ,
                 (not Neg) and (not Zero) when NIAG_COND_GTZ,
                 not Neg                  when NIAG_COND_GEZ,
                 Neg                      when NIAG_COND_LTZ,
                 Neg or Zero              when NIAG_COND_LEZ,
                 '0'                      when others;
end architecture rtl;
