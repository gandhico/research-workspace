library IEEE;
use IEEE.STD_LOGIC_1164.ALL;
use IEEE.NUMERIC_STD.ALL;
use work.Memory_Pkg.ALL;

entity TestRAM is
end TestRAM;

architecture sim of TestRAM is
    signal Addr      : STD_LOGIC_VECTOR(31 downto 0) := (others => '0');
    signal Strb      : STD_LOGIC := '0';
    signal rw        : STD_LOGIC := '1';
    signal en        : STD_LOGIC := '0';
    signal clk       : STD_LOGIC := '0';
    signal Data_bus  : STD_LOGIC_VECTOR(31 downto 0);

    -- CPU-side bus driver
    signal CPU_Data  : STD_LOGIC_VECTOR(31 downto 0) := (others => '0');
    signal CPU_Drive : STD_LOGIC := '0';

    -- Stops the clock when the testbench is finished
    signal done      : STD_LOGIC := '0';

    constant Tclk : time := 10 ns;

    -- Returns TRUE only if every bit on the bus is 'Z'
    function all_z(v : STD_LOGIC_VECTOR) return boolean is
    begin
        for i in v'range loop
            if v(i) /= 'Z' then
                return false;
            end if;
        end loop;
        return true;
    end function;

begin
    -- CPU drives the shared bus only during write cycles
    Data_bus <= CPU_Data when CPU_Drive = '1' else (others => 'Z');

    UUT : RAM
        port map(
            Addr => Addr,
            Strb => Strb,
            rw   => rw,
            en   => en,
            clk  => clk,
            Data => Data_bus
        );

    -- Clock runs only until done = '1'
    clk_process : process
    begin
        while done = '0' loop
            clk <= '0';
            wait for Tclk/2;
            clk <= '1';
            wait for Tclk/2;
        end loop;
        wait;
    end process;

    stim_proc : process
    begin
        ----------------------------------------------------------------
        -- 1) Idle: RAM must not drive the bus when disabled
        ----------------------------------------------------------------
        en        <= '0';
        rw        <= '1';
        Strb      <= '0';
        CPU_Drive <= '0';
        wait for 12 ns;

        assert all_z(Data_bus)
            report "FAIL: Data bus should float when RAM is disabled"
            severity error;

        ----------------------------------------------------------------
        -- 2) Write 0x12345678 at address 0x00000002
        ----------------------------------------------------------------
        Addr      <= x"00000002";
        en        <= '1';
        rw        <= '0';
        CPU_Data  <= x"12345678";
        CPU_Drive <= '1';
        Strb      <= '1';

        wait until rising_edge(clk);
        wait for 1 ns;

        Strb      <= '0';
        CPU_Drive <= '0';
        wait for 4 ns;

        ----------------------------------------------------------------
        -- 3) Read back from 0x00000002
        ----------------------------------------------------------------
        rw   <= '1';
        Addr <= x"00000002";
        wait for 2 ns;

        assert Data_bus = x"12345678"
            report "FAIL: Readback at 0x00000002 should be 0x12345678"
            severity error;

        ----------------------------------------------------------------
        -- 4) Overwrite at 0x00000004
        ----------------------------------------------------------------
        rw        <= '0';
        Addr      <= x"00000004";
        CPU_Data  <= x"ABCDEF01";
        CPU_Drive <= '1';
        Strb      <= '1';

        wait until rising_edge(clk);
        wait for 1 ns;

        Strb      <= '0';
        CPU_Drive <= '0';
        wait for 4 ns;

        ----------------------------------------------------------------
        -- 5) Read 0x00000002 to verify overlap behavior
        ----------------------------------------------------------------
        rw   <= '1';
        Addr <= x"00000002";
        wait for 2 ns;

        assert Data_bus = x"1234ABCD"
            report "FAIL: Overlap read at 0x00000002 should be 0x1234ABCD"
            severity error;

        ----------------------------------------------------------------
        -- 6) Read 0x00000004
        ----------------------------------------------------------------
        Addr <= x"00000004";
        wait for 2 ns;

        assert Data_bus = x"ABCDEF01"
            report "FAIL: Readback at 0x00000004 should be 0xABCDEF01"
            severity error;

        ----------------------------------------------------------------
        -- 7) No write when Strb is low
        ----------------------------------------------------------------
        rw        <= '0';
        Addr      <= x"00000008";
        CPU_Data  <= x"DEADBEEF";
        CPU_Drive <= '1';
        Strb      <= '0';

        wait until rising_edge(clk);
        wait for 1 ns;

        CPU_Drive <= '0';
        rw        <= '1';
        wait for 2 ns;

        assert Data_bus = x"00000000"
            report "FAIL: RAM should not write when Strb is low"
            severity error;

        ----------------------------------------------------------------
        -- 8) Out-of-range write must be ignored
        ----------------------------------------------------------------
        rw        <= '0';
        Addr      <= x"00000080";
        CPU_Data  <= x"CAFEBABE";
        CPU_Drive <= '1';
        Strb      <= '1';

        wait until rising_edge(clk);
        wait for 1 ns;

        Strb      <= '0';
        CPU_Drive <= '0';
        rw        <= '1';
        wait for 2 ns;

        assert Data_bus = x"00000000"
            report "FAIL: Addresses above 0x7F must be ignored"
            severity error;

        ----------------------------------------------------------------
        -- 9) Bus must float when read is not enabled
        ----------------------------------------------------------------
        en   <= '0';
        rw   <= '1';
        Addr <= x"00000004";
        wait for 2 ns;

        assert all_z(Data_bus)
            report "FAIL: Data bus should float when read is not enabled"
            severity error;

        report "TestRAM completed successfully." severity note;

        done <= '1';
        wait;
    end process;

end sim;