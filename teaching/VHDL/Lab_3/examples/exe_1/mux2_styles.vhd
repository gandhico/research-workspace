--------------------------------------------------------------------------------
-- EE 362 - Computer Organization Laboratory
-- Lab 3, Example 1 - One multiplexer, three coding styles
--
-- Three entities. Identical behaviour. Identical synthesised hardware.
-- The only thing that differs is how you SAY it.
--
--   Y = Sel'.A + Sel.B
--
-- 1. CONDITIONAL signal assignment    (when / else)
--      Reads as a priority chain: "B if Sel is 1, otherwise A".
--      Good when the choices really are prioritised.
--
-- 2. SELECTED signal assignment       (with / select)
--      Reads as a table: "for this value of Sel, take this input".
--      Good when the choices are parallel and exhaustive - which is exactly
--      what a multiplexer is. This is usually the clearest for datapath work.
--
-- 3. CASE inside a process
--      Same table, but sequential. You need this once the logic is more than
--      one assignment, and it is what the decoder in Labs 10-11 will use.
--
-- All three are correct. Pick the one that makes the INTENT obvious.
--------------------------------------------------------------------------------

library ieee;
use ieee.std_logic_1164.all;

--------------------------------------------------------------------------------
-- Style 1 : conditional signal assignment
--------------------------------------------------------------------------------
entity mux2_whenelse is
    port (A, B, Sel : in std_logic; Y : out std_logic);
end entity mux2_whenelse;

architecture rtl of mux2_whenelse is
begin
    Y <= B when Sel = '1' else A;
end architecture rtl;


--------------------------------------------------------------------------------
-- Style 2 : selected signal assignment
--------------------------------------------------------------------------------
library ieee;
use ieee.std_logic_1164.all;

entity mux2_withselect is
    port (A, B, Sel : in std_logic; Y : out std_logic);
end entity mux2_withselect;

architecture rtl of mux2_withselect is
begin
    with Sel select
        Y <= A when '0',
             B when '1',
             A when others;         -- 'X', 'Z', 'U' ... must be covered
end architecture rtl;


--------------------------------------------------------------------------------
-- Style 3 : case inside a process
--------------------------------------------------------------------------------
library ieee;
use ieee.std_logic_1164.all;

entity mux2_case is
    port (A, B, Sel : in std_logic; Y : out std_logic);
end entity mux2_case;

architecture rtl of mux2_case is
begin
    process (A, B, Sel)             -- combinational: EVERY signal read
    begin
        case Sel is
            when '0'    => Y <= A;
            when '1'    => Y <= B;
            when others => Y <= A;  -- required: std_logic has nine values
        end case;
    end process;
end architecture rtl;
