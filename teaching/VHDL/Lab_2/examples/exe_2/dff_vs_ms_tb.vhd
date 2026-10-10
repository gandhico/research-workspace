--------------------------------------------------------------------------------
-- EE 362 - Computer Organization Laboratory
-- Lab 2, Example 2 - Structural vs behavioural, driven by the same stimulus
--
-- Both flip-flops see identical inputs. Every check asserts that they agree.
-- If the two descriptions really do describe the same hardware, no check can
-- ever fail - and that is the claim being tested.
--
-- IN THE WAVEFORM: Q_struct and Q_behav are indistinguishable.
-- IN THE RTL VIEWER: they are completely different pictures.
--
-- That gap - same behaviour, different structure - is what a synthesiser is
-- for. You describe intent; it chooses an implementation.
--------------------------------------------------------------------------------

library ieee;
use ieee.std_logic_1164.all;

entity dff_vs_ms_tb is
end entity dff_vs_ms_tb;

architecture test of dff_vs_ms_tb is

    constant PERIOD : time := 20 ns;

    signal Clk      : std_logic := '0';
    signal D        : std_logic := '0';
    signal Q_struct : std_logic;
    signal Q_behav  : std_logic;

    signal running  : boolean := true;

begin

    DUT_STRUCT : entity work.ms_flipflop
        port map (D => D, Clk => Clk, Q => Q_struct);

    DUT_BEHAV : entity work.dff
        port map (D => D, Clk => Clk, Q => Q_behav);

    clock_gen : process
    begin
        while running loop
            Clk <= '0'; wait for PERIOD / 2;
            Clk <= '1'; wait for PERIOD / 2;
        end loop;
        wait;
    end process clock_gen;

    stimulus : process

        variable errors : natural := 0;

        procedure agree (msg : in string) is
        begin
            if Q_struct /= Q_behav then
                report "FAIL: " & msg &
                       " - structural = " & std_logic'image(Q_struct) &
                       ", behavioural = " & std_logic'image(Q_behav)
                    severity error;
                errors := errors + 1;
            end if;
        end procedure agree;

    begin

        -- Walk a pattern through both, changing D safely after falling edges
        for i in 0 to 7 loop
            wait until falling_edge(Clk);
            case i is
                when 0 | 3 | 4 | 6 => D <= '1';
                when others        => D <= '0';
            end case;
            wait until rising_edge(Clk);
            wait for 1 ns;
            agree("cycle " & integer'image(i));
        end loop;

        -- Toggle rapidly between edges: both must ignore all of it
        wait until falling_edge(Clk);
        D <= '1'; wait for 1 ns; agree("mid-period toggle 1");
        D <= '0'; wait for 1 ns; agree("mid-period toggle 2");
        D <= '1'; wait for 1 ns; agree("mid-period toggle 3");

        wait until rising_edge(Clk);
        wait for 1 ns;
        agree("after the capturing edge");

        if errors = 0 then
            report "PASS - the two descriptions are behaviourally identical."
                severity note;
        else
            report "FAILED - descriptions disagree in " &
                   integer'image(errors) & " place(s)." severity error;
        end if;

        running <= false;
        wait;
    end process stimulus;

end architecture test;
