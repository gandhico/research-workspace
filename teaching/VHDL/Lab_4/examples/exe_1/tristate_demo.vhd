--------------------------------------------------------------------------------
-- EE 362 - Computer Organization Laboratory
-- Lab 4, Example 1 - Tri-state buffers and a shared bus
--
-- Everything you have built so far obeyed Boolean algebra: every signal was
-- '0' or '1'. This one does not.
--
-- A tri-state buffer has a third state, 'Z' - HIGH IMPEDANCE. It means
-- "I am not driving this wire at all." That is not a value. It is the ABSENCE
-- of a value, and Boolean algebra has no symbol for it.
--
--   #  Sel  ||  Y
--   0   0   ||  Z      not driving
--   1   1   ||  A      driving
--
-- This is NOT a Boolean function. You cannot write Y = f(Sel, A) in AND/OR/NOT,
-- because the output range is {0, 1, Z} and Boolean algebra only has {0, 1}.
--
-- WHY VHDL NEEDS A "RESOLVED" TYPE
--   If two drivers touch the same wire, something must decide what the wire
--   actually reads. std_logic is a RESOLVED type: it carries a function that
--   combines all the drivers. Here is the part of that table you need:
--
--          |  0  |  1  |  Z
--     -----+-----+-----+-----
--       0  |  0  |  X  |  0
--       1  |  X  |  1  |  1
--       Z  |  0  |  1  |  Z
--
--   Two drivers agreeing -> that value.
--   One driving, one at 'Z' -> the driven value. (This is how a bus works.)
--   Two drivers disagreeing -> 'X'.
--
-- SO: 'X' IN YOUR WAVEFORM NEVER MEANS THE SIMULATOR IS CONFUSED.
-- It means two things drove one wire and disagreed. Remember that - in Lab 9
-- and Lab 12 it is the fastest diagnosis you own.
--------------------------------------------------------------------------------

library ieee;
use ieee.std_logic_1164.all;

entity tristate_buf is
    port (
        A   : in  std_logic;
        Sel : in  std_logic;                -- '1' = drive, '0' = release
        Y   : out std_logic
    );
end entity tristate_buf;

architecture rtl of tristate_buf is
begin
    Y <= A when Sel = '1' else 'Z';
end architecture rtl;


--------------------------------------------------------------------------------
-- Two buffers sharing one wire. This is a BUS.
--
-- Bus discipline: at most ONE driver enabled at a time. Enable none and the
-- bus floats at 'Z'. Enable two and you get 'X' - and in real silicon, a short
-- from supply to ground through two output transistors.
--------------------------------------------------------------------------------
library ieee;
use ieee.std_logic_1164.all;

entity bus_demo is
    port (
        A, B     : in  std_logic;
        SelA     : in  std_logic;
        SelB     : in  std_logic;
        BusWire  : out std_logic
    );
end entity bus_demo;

architecture rtl of bus_demo is
begin

    -- BOTH of these drive the same output signal. That is legal precisely
    -- because std_logic is resolved - with an unresolved type it would be an
    -- error to have two drivers at all.
    DRIVER_A : entity work.tristate_buf
        port map (A => A, Sel => SelA, Y => BusWire);

    DRIVER_B : entity work.tristate_buf
        port map (A => B, Sel => SelB, Y => BusWire);

end architecture rtl;
