--------------------------------------------------------------------------------
-- EE 362 - Computer Organization Laboratory
-- Lab 2, Example 3 - Testbench: ONE entity, TWO widths
--
-- The same reg_n is instantiated at 4 bits and at 12 bits. Nothing in reg_n.vhd
-- changes. That is what a generic buys you.
--
-- Note the syntax order:  generic map ( ... )  comes BEFORE  port map ( ... )
-- and there is NO semicolon between them. Getting this wrong is the most common
-- syntax error of the week.
--------------------------------------------------------------------------------

library ieee;
use ieee.std_logic_1164.all;

entity reg_n_tb is
end entity reg_n_tb;

architecture test of reg_n_tb is

    constant PERIOD : time := 20 ns;

    signal Clk : std_logic := '0';
    signal Ld  : std_logic := '0';
    signal Rst : std_logic := '0';

    signal D4  : std_logic_vector(3 downto 0)  := (others => '0');
    signal Q4  : std_logic_vector(3 downto 0);

    signal D12 : std_logic_vector(11 downto 0) := (others => '0');
    signal Q12 : std_logic_vector(11 downto 0);

    signal running : boolean := true;

begin

    SMALL : entity work.reg_n
        generic map (N => 4)                -- no semicolon before port map
        port map (D => D4, Clk => Clk, Ld => Ld, Rst => Rst, Q => Q4);

    BIG : entity work.reg_n
        generic map (N => 12)
        port map (D => D12, Clk => Clk, Ld => Ld, Rst => Rst, Q => Q12);

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

        procedure check (msg  : in string;
                         e4   : in std_logic_vector(3 downto 0);
                         e12  : in std_logic_vector(11 downto 0)) is
        begin
            if Q4 /= e4 then
                report "FAIL (4-bit): " & msg severity error;
                errors := errors + 1;
            end if;
            if Q12 /= e12 then
                report "FAIL (12-bit): " & msg severity error;
                errors := errors + 1;
            end if;
        end procedure check;

    begin

        -- Row 0: asynchronous reset, asserted BETWEEN edges to prove it is async
        Rst <= '1'; Ld <= '1'; D4 <= "1111"; D12 <= x"FFF";
        wait for 3 ns;
        check("row 0: async reset acts immediately", "0000", x"000");

        -- Row 3: load at the rising edge
        Rst <= '0';
        wait until falling_edge(Clk);
        D4 <= "1010"; D12 <= x"A5C";
        wait until rising_edge(Clk);
        wait for 1 ns;
        check("row 3: loaded at the edge", "1010", x"A5C");

        -- Row 2: edge arrives but Ld is low - hold
        wait until falling_edge(Clk);
        Ld  <= '0';
        D4  <= "0101"; D12 <= x"123";
        wait until rising_edge(Clk);
        wait for 1 ns;
        check("row 2: edge with Ld low does not load", "1010", x"A5C");

        -- Row 1: hold between edges
        wait for 3 ns;
        D4 <= "1111"; D12 <= x"FFF";
        wait for 3 ns;
        check("row 1: holds between edges", "1010", x"A5C");

        -- Async reset again, mid-period, while holding
        wait until falling_edge(Clk);
        wait for 3 ns;
        Rst <= '1';
        wait for 1 ns;
        check("async reset works mid-period", "0000", x"000");
        Rst <= '0';

        if errors = 0 then
            report "PASS - reg_n: both widths correct from one entity."
                severity note;
        else
            report "FAILED - reg_n: " & integer'image(errors) &
                   " check(s) failed." severity error;
        end if;

        running <= false;
        wait;
    end process stimulus;

end architecture test;
