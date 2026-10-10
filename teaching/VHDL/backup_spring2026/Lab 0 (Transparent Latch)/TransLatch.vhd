library ieee;
use ieee.std_logic_1164.all;
-- Entity declaration:
-- Defines the inputs and outputs of the transparent latch.

entity Transparent_Latch is
    port(
        Reset_n : in  std_logic;  -- Active-low asynchronous reset
        Gate    : in  std_logic;  -- Enable control: when '1', latch is transparent
        Data    : in  std_logic;  -- Data input
        Q       : out std_logic;  -- Normal output
        Qn      : out std_logic   -- Complemented output
    );
end entity;

-- Architecture declaration:
-- Describes the internal behavior of the latch.
architecture behavioral of Transparent_Latch is

    -- Internal signal used to store the current latch value.
    signal q_int : std_logic := '0';

begin

    -- Process block:
    -- A transparent latch must react immediately to reset, gate,
    -- or data changes, so all are included in the sensitivity list.
    process(Reset_n, Gate, Data)
    begin
        -- If reset is asserted ('0'), force the internal state to '0'
        -- regardless of Gate or Data.
        if Reset_n = '0' then
            q_int <= '0';

        -- If Gate is high, the latch is transparent:
        -- the output follows the input Data.
        elsif Gate = '1' then
            q_int <= Data;

        -- If Gate is low, no assignment is made here.
        -- Therefore, q_int keeps its previous value,
        -- which is the latch "hold" condition.
        end if;
    end process;

    -- Output assignments:
    -- Q gives the stored value,
    -- Qn gives its logical complement.
    Q  <= q_int;
    Qn <= not q_int;

end architecture;