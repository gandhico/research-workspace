--------------------------------------------------------------------------------
-- EE 362 - Lab 5, Example 2 - Testbench for the mini ALU
--
-- The check that matters is vector 4: an AND that produces zero.
--
-- If the flags were taken from the adder instead of from the selected result,
-- everything else here still passes and only that one vector fails. That is
-- what a well-chosen test vector looks like - it isolates one wrong decision.
--------------------------------------------------------------------------------

library ieee;
use ieee.std_logic_1164.all;

entity alu_mini_tb is
end entity alu_mini_tb;

architecture test of alu_mini_tb is

    signal Ain, Bin, Rout : std_logic_vector(31 downto 0) := (others => '0');
    signal Func : std_logic := '0';
    signal Zero, Neg : std_logic;

begin

    DUT : entity work.alu_mini
        port map (Ain => Ain, Bin => Bin, Func => Func,
                  Rout => Rout, Zero => Zero, Neg => Neg);

    stimulus : process

        variable errors : natural := 0;

        procedure check (wr : in std_logic_vector(31 downto 0);
                         wz, wn : in std_logic; msg : in string) is
        begin
            if Rout /= wr then
                report "FAIL (result): " & msg severity error;
                errors := errors + 1;
            end if;
            if Zero /= wz then
                report "FAIL (Zero): " & msg severity error;
                errors := errors + 1;
            end if;
            if Neg /= wn then
                report "FAIL (Neg): " & msg severity error;
                errors := errors + 1;
            end if;
        end procedure check;

    begin

        -- Add selected
        Ain <= x"00000005"; Bin <= x"00000003"; Func <= '0'; wait for 10 ns;
        check(x"00000008", '0', '0', "1. Func=0 selects the adder");

        -- And selected, same inputs. Different answer, same instant.
        Func <= '1'; wait for 10 ns;
        check(x"00000001", '0', '0', "2. Func=1 selects AND, same inputs");

        -- A negative AND result, to exercise the Neg flag through the mux
        Ain <= x"FFFFFFFF"; Bin <= x"80000000"; Func <= '1'; wait for 10 ns;
        check(x"80000000", '0', '1', "3. AND result is negative");

        -- THE VECTOR THAT MATTERS: an AND producing zero, while the adder
        -- (running in parallel, ignored) produces something non-zero.
        -- Flags must describe the SELECTED result.
        Ain <= x"0000FFFF"; Bin <= x"FFFF0000"; Func <= '1'; wait for 10 ns;
        check(x"00000000", '1', '0',
              "4. AND gives zero -> Zero must be set, even though the adder did not");

        if errors = 0 then
            report "PASS - alu_mini: flags follow the selected result." severity note;
        else
            report "FAILED - alu_mini: " & integer'image(errors) &
                   " check(s) failed." severity error;
        end if;

        wait;
    end process stimulus;

end architecture test;
