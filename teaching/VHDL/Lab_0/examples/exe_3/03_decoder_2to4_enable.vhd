--------------------------------------------------------------------------------
-- EE362 - Exercise 3: 2-to-4 Decoder with Enable
-- Purpose: Introduce vectors, PROCESS, IF, and CASE while still describing
--          COMBINATIONAL hardware.
--
-- Function when en = '1':
--   a = "00" -> y = "0001"
--   a = "01" -> y = "0010"
--   a = "10" -> y = "0100"
--   a = "11" -> y = "1000"
--
-- Function when en = '0':
--   y = "0000"
--
-- Important first-class idea:
--   A VHDL PROCESS does NOT automatically mean sequential hardware.
--   This process describes combinational logic because there is no clock or memory,
--   and y receives a value for every possible branch.
--------------------------------------------------------------------------------

library ieee;                               -- Make the IEEE library available.
use ieee.std_logic_1164.all;                -- Import std_logic and std_logic_vector.

entity decoder_2to4_enable is               -- Define the decoder's external interface.
    port (                                  -- Start the input/output list.
        en : in  std_logic;                 -- Enable input: 1 = active, 0 = disabled.
        a  : in  std_logic_vector(1 downto 0); -- Two-bit binary input: a(1) and a(0).
        y  : out std_logic_vector(3 downto 0)  -- Four one-hot decoder outputs.
    );                                      -- End of the port list.
end entity decoder_2to4_enable;             -- End of the decoder entity.

architecture behavioral of decoder_2to4_enable is -- Describe the decoder function.
begin                                       -- Start active/concurrent architecture content.

    process(a, en)                          -- Re-evaluate this process when a or en changes.
    begin                                   -- Begin the statements inside the process.

        if en = '0' then                    -- First check whether the decoder is disabled.
            y <= "0000";                   -- If disabled, no output line is active.

        else                                -- Otherwise, en is active and input a is decoded.

            case a is                       -- Select one result according to the value of a.

                when "00" =>                -- Case for binary input 0.
                    y <= "0001";            -- Activate y(0) only.

                when "01" =>                -- Case for binary input 1.
                    y <= "0010";            -- Activate y(1) only.

                when "10" =>                -- Case for binary input 2.
                    y <= "0100";            -- Activate y(2) only.

                when "11" =>                -- Case for binary input 3.
                    y <= "1000";            -- Activate y(3) only.

                when others =>              -- Catch non-binary simulation values such as X/U.
                    y <= "0000";            -- Use a safe default value for those cases.

            end case;                       -- End of the CASE statement.

        end if;                             -- End of the enable IF statement.

    end process;                            -- End of the combinational process.

end architecture behavioral;               -- End of the decoder architecture.
