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
-- EE 362 - Lab 3 reference component
--
-- Mux3 : generic-width 3-to-1 multiplexer, row 3 = defined default (zeros)
--
--   (1) Y_i = S1'S0'.A_i + S1'S0.B_i + S1S0'.C_i + S1S0.0
--   (2) Y_i = S1'.( S0'.A_i + S0.B_i ) + S1.S0'.C_i     [factoring S1']
--
-- 'case' is used deliberately: VHDL forces it to cover every selector value,
-- so the language prevents the Example 3 latch.
--------------------------------------------------------------------------------

library ieee;
use ieee.std_logic_1164.all;

entity Mux3 is
    generic (W : positive := 32);
    port (
        A   : in  std_logic_vector(W - 1 downto 0);
        B   : in  std_logic_vector(W - 1 downto 0);
        C   : in  std_logic_vector(W - 1 downto 0);
        Sel : in  std_logic_vector(1 downto 0);
        Y   : out std_logic_vector(W - 1 downto 0)
    );
end entity Mux3;

architecture rtl of Mux3 is
begin
    process (A, B, C, Sel)
    begin
        case Sel is
            when "00"   => Y <= A;
            when "01"   => Y <= B;
            when "10"   => Y <= C;
            when "11"   => Y <= (others => '0');   -- row 3, defined default
            when others => Y <= (others => 'X');   -- selector not 0/1
        end case;
    end process;
end architecture rtl;
