--------------------------------------------------------------------------------
-- EE 362 - Lab 2 REFERENCE SOLUTION testbench  (TA only - do not publish)
--
-- 20 checks across three DUTs: MSFlipFlop, RegN(5), RegN(32).
--------------------------------------------------------------------------------

library ieee;
use ieee.std_logic_1164.all;

entity tb_Lab2 is
end entity tb_Lab2;

architecture test of tb_Lab2 is

    constant PERIOD : time := 20 ns;

    signal Clk : std_logic := '0';
    signal Clr : std_logic := '0';
    signal Rst : std_logic := '0';
    signal Ld  : std_logic := '0';

    signal Dff : std_logic := '0';
    signal Qff : std_logic;

    signal D5  : std_logic_vector(4 downto 0)  := (others => '0');
    signal Q5  : std_logic_vector(4 downto 0);

    signal D32 : std_logic_vector(31 downto 0) := (others => '0');
    signal Q32 : std_logic_vector(31 downto 0);

    signal running : boolean := true;

begin

    DUT_FF : entity work.MSFlipFlop
        port map (D => Dff, Clk => Clk, Clr => Clr, Q => Qff);

    DUT_R5 : entity work.RegN
        generic map (N => 5)
        port map (D => D5, Clk => Clk, Ld => Ld, Rst => Rst, Q => Q5);

    DUT_R32 : entity work.RegN
        generic map (N => 32)
        port map (D => D32, Clk => Clk, Ld => Ld, Rst => Rst, Q => Q32);

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

        procedure checkff (expected : in std_logic; msg : in string) is
        begin
            if Qff /= expected then
                report "FAIL (FF): " & msg &
                       " - expected " & std_logic'image(expected) &
                       ", got "       & std_logic'image(Qff) severity error;
                errors := errors + 1;
            end if;
        end procedure checkff;

        procedure check5 (expected : in std_logic_vector(4 downto 0);
                          msg : in string) is
        begin
            if Q5 /= expected then
                report "FAIL (5-bit): " & msg severity error;
                errors := errors + 1;
            end if;
        end procedure check5;

        procedure check32 (expected : in std_logic_vector(31 downto 0);
                           msg : in string) is
        begin
            if Q32 /= expected then
                report "FAIL (32-bit): " & msg severity error;
                errors := errors + 1;
            end if;
        end procedure check32;

    begin

        -- 1. Asynchronous reset asserted mid-period, with Ld and data high.
        --    If the reset is only sampled at the edge, this check fails.
        Clr <= '1'; Rst <= '1'; Ld <= '1';
        Dff <= '1'; D5 <= "11111"; D32 <= (others => '1');
        wait for 3 ns;
        checkff('0', "1. async clear acts immediately");
        check5("00000", "1. async reset acts immediately");
        check32(x"00000000", "1. async reset acts immediately");

        Clr <= '0'; Rst <= '0';

        -- 2. Load at a rising edge
        wait until falling_edge(Clk);
        Dff <= '1'; D5 <= "10101"; D32 <= x"DEADBEEF";
        wait until rising_edge(Clk);
        wait for 1 ns;
        checkff('1',  "2. FF captured D at the edge");
        check5("10101", "2. 5-bit loaded at the edge");
        check32(x"DEADBEEF", "2. 32-bit loaded at the edge");

        -- 3. THE EDGE VECTOR: toggle between edges, nothing may move
        wait until falling_edge(Clk);
        Dff <= '0'; D5 <= "01010"; D32 <= x"00000000"; wait for 2 ns;
        Dff <= '1'; D5 <= "11111"; D32 <= x"FFFFFFFF"; wait for 2 ns;
        Dff <= '0'; D5 <= "00000"; D32 <= x"12345678"; wait for 2 ns;
        checkff('1',  "3. FF ignores toggling between edges");
        check5("10101", "3. 5-bit holds between edges");
        check32(x"DEADBEEF", "3. 32-bit holds between edges");

        -- 4. The edge takes the LAST value before it
        wait until rising_edge(Clk);
        wait for 1 ns;
        checkff('0',  "4. FF captured the last value before the edge");
        check5("00000", "4. 5-bit captured the last value");
        check32(x"12345678", "4. 32-bit captured the last value");

        -- 5. Edge with Ld = '0': registers hold, flip-flop still follows
        wait until falling_edge(Clk);
        Ld <= '0';
        D5 <= "11011"; D32 <= x"AAAAAAAA";
        wait until rising_edge(Clk);
        wait for 1 ns;
        check5("00000", "5. edge with Ld low does not load");
        check32(x"12345678", "5. edge with Ld low does not load");

        -- 6. Async clear on the flip-flop only, mid-period, while holding.
        --    Clearing both latches is what makes this stick; clearing only the
        --    slave would let the master push the old value back at the next edge.
        wait until falling_edge(Clk);
        Dff <= '1';
        wait until rising_edge(Clk);
        wait for 1 ns;
        checkff('1', "6a. FF loaded before the clear");
        wait for 3 ns;
        Clr <= '1';
        wait for 1 ns;
        checkff('0', "6b. async clear works mid-period");

        -- 7. And it must STAY cleared through the next edge
        wait until rising_edge(Clk);
        wait for 1 ns;
        checkff('0', "7. clear is not undone by the next edge");
        Clr <= '0';

        if errors = 0 then
            report "PASS - Lab 2: all 20 checks passed." severity note;
        else
            report "FAILED - Lab 2: " & integer'image(errors) &
                   " check(s) failed." severity error;
        end if;

        running <= false;
        wait;
    end process stimulus;

end architecture test;
