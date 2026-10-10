--------------------------------------------------------------------------------
-- EE 362 - Lab 0, Example 1 - self-checking testbench
-- Exhaustive: all 8 rows of the truth table, 10 ns each (ends at 80 ns).
--------------------------------------------------------------------------------
library ieee;
use ieee.std_logic_1164.all;

entity majority3_tb is
end entity majority3_tb;

architecture test of majority3_tb is

    signal A, B, C : std_logic := '0';
    signal Y       : std_logic;

    -- The truth table, as data: A, B, C, expected Y
    type row_t   is array (0 to 3) of std_logic;
    type table_t is array (0 to 7) of row_t;
    constant TABLE : table_t := (
        ('0','0','0','0'),      -- row 0
        ('0','0','1','0'),      -- row 1
        ('0','1','0','0'),      -- row 2
        ('0','1','1','1'),      -- row 3
        ('1','0','0','0'),      -- row 4
        ('1','0','1','1'),      -- row 5
        ('1','1','0','1'),      -- row 6
        ('1','1','1','1') );    -- row 7

begin

    dut : entity work.majority3
        port map ( A => A, B => B, C => C, Y => Y );

    stimulus : process
        variable errors : natural := 0;
    begin
        for i in TABLE'range loop
            A <= TABLE(i)(0);  B <= TABLE(i)(1);  C <= TABLE(i)(2);
            wait for 10 ns;
            if Y /= TABLE(i)(3) then
                report "FAIL: row " & integer'image(i) severity error;
                errors := errors + 1;
            end if;
        end loop;

        if errors = 0 then
            report "PASS - majority3: all 8 rows correct" severity note;
        else
            report "FAILED - majority3: " & integer'image(errors) &
                   " row(s) wrong" severity error;
        end if;
        wait;
    end process stimulus;

end architecture test;
