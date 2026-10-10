--------------------------------------------------------------------------------
-- EE 362 - Computer Organization Laboratory
-- Lab 3, Example 3 - The inferred-latch trap
--
-- Two 3-to-1 multiplexers. One is correct. One is WRONG ON PURPOSE.
--
-- The broken one leaves Sel = "11" unassigned. There is no 'else'. So when the
-- selector takes that value, no assignment happens, and the output KEEPS ITS
-- PREVIOUS VALUE.
--
-- You have seen that sentence before. It is Lab 1's latch, word for word:
--
--     "no assignment happens, so the output keeps its previous value"
--
-- In Lab 1 that was the feature. Here it is a bug. The circuit you wanted is
-- combinational; the circuit you described has memory in it. Quartus will build
-- a latch, warn you about it, and most people will not read the warning.
--
-- HOW TO SEE IT
--   In simulation : drive Sel = "11" and watch Y_bad hold the old value while
--                   Y_good takes a defined default.
--   In the RTL Viewer : Y_bad has a latch symbol in its path. Y_good does not.
--   In the Fitter : Y_bad's design reports latches. A multiplexer must report
--                   ZERO storage elements.
--
-- WHY A 'case' WOULD NOT LET YOU DO THIS
--   VHDL requires a case to cover every possible value of its selector, and
--   std_logic_vector(1 downto 0) has 81 of them - so a case without 'when
--   others' is a COMPILE ERROR, not a latch. It is the if/elsif chain with no
--   final else that slips through. Prefer 'case' with 'when others' and the
--   language will refuse to let you make this mistake.
--------------------------------------------------------------------------------

library ieee;
use ieee.std_logic_1164.all;

--------------------------------------------------------------------------------
-- CORRECT: every selector value assigns something
--------------------------------------------------------------------------------
entity mux3_good is
    port (
        A, B, C : in  std_logic_vector(7 downto 0);
        Sel     : in  std_logic_vector(1 downto 0);
        Y       : out std_logic_vector(7 downto 0)
    );
end entity mux3_good;

architecture rtl of mux3_good is
begin
    process (A, B, C, Sel)
    begin
        case Sel is
            when "00"   => Y <= A;
            when "01"   => Y <= B;
            when "10"   => Y <= C;
            when others => Y <= (others => '0');   -- defined default
        end case;
    end process;
end architecture rtl;


--------------------------------------------------------------------------------
-- BROKEN ON PURPOSE: Sel = "11" assigns nothing
--------------------------------------------------------------------------------
library ieee;
use ieee.std_logic_1164.all;

entity mux3_bad is
    port (
        A, B, C : in  std_logic_vector(7 downto 0);
        Sel     : in  std_logic_vector(1 downto 0);
        Y       : out std_logic_vector(7 downto 0)
    );
end entity mux3_bad;

architecture rtl of mux3_bad is
begin
    process (A, B, C, Sel)
    begin
        if Sel = "00" then
            Y <= A;
        elsif Sel = "01" then
            Y <= B;
        elsif Sel = "10" then
            Y <= C;
        end if;
        -- no else. Sel = "11" assigns nothing, so Y holds. That is a latch.
    end process;
end architecture rtl;
