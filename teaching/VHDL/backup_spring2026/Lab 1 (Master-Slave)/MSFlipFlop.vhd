library ieee;
use ieee.std_logic_1164.all;

-- Entity declaration:
-- This module implements a Master-Slave Flip-Flop using two transparent latches.
-- The master latch is enabled when Strobe = '0',
-- and the slave latch is enabled when Strobe = '1'.
entity MS_FF is
    port(
        Reset_n : in  std_logic;  -- Active-low asynchronous reset
        Strobe  : in  std_logic;  -- Control signal that acts like the clock
        Data    : in  std_logic;  -- Input data
        Q       : out std_logic;  -- Normal output
        Qn      : out std_logic   -- Complemented output
    );
end entity;

-- Structural architecture:
-- Builds the flip-flop by interconnecting two Transparent_Latch blocks.
architecture structural of MS_FF is

    -- Output of the master latch
    signal master_q   : std_logic;

    -- Internal signal for the final stored value
    signal q_internal : std_logic;

    -- Inverted strobe signal:
    -- used so the master and slave latches are never transparent at the same time
    signal strobe_not : std_logic;

begin

    -- Invert the strobe signal
    strobe_not <= not Strobe;

    -- Master latch:
    -- Active when Strobe = '0' (because Gate = not Strobe).
    -- While active, it captures the input Data.
    -- When Strobe goes to '1', the master holds its last value.
    master: entity work.Transparent_Latch
        port map(
            Reset_n => Reset_n,
            Gate    => strobe_not,
            Data    => Data,
            Q       => master_q,
            Qn      => open
        );

    -- Slave latch:
    -- Active when Strobe = '1'.
    -- It receives the stored output of the master latch.
    -- Therefore, the external output only updates when Strobe changes state,
    -- giving flip-flop behavior instead of simple latch behavior.
    slave: entity work.Transparent_Latch
        port map(
            Reset_n => Reset_n,
            Gate    => Strobe,
            Data    => master_q,
            Q       => q_internal,
            Qn      => open
        );

    -- Final output assignments
    Q  <= q_internal;      -- Stored output
    Qn <= not q_internal;  -- Complement of stored output

end architecture;