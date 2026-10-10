--------------------------------------------------------------------------------
-- EE 362 - Computer Organization Laboratory
-- Lab 12 - Testbench  (PROVIDED COMPLETE - you do not have to write this one)
--
-- YOUR NAME  :
-- SECTION    :  Monday / Tuesday
-- DATE       :
--
-- This lab is wiring and debugging, not test writing, so the testbench is
-- given to you finished. It does three things:
--
--   1. prints the EXECUTION TRACE, one line per clock period
--   2. records what the machine actually did
--   3. checks the final state:  r1 = 0,  r2 = 0x400,  stored word = 0x400
--
-- THE TRACE IT PRINTS IS THE TABLE YOUR REPORT NEEDS. Copy it in.
--
-- ============================================================================
-- ONE THING IN HERE IS WORTH READING CAREFULLY
-- ============================================================================
-- The tracer samples JUST BEFORE the falling edge, never after it.
--
-- After the edge the write has already committed, and for a self-referencing
-- instruction such as
--         ADDI r1, r1, -1
-- the combinational logic immediately recomputes from the NEW r1 - so a
-- post-edge sample would show the result of the NEXT iteration, not this one.
--
-- The hardware would be perfectly correct and the observer would be lying.
-- This is a real and common way to waste an hour, and it is worth knowing that
-- WHEN you sample is part of the measurement.
--------------------------------------------------------------------------------

library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

entity tb_Lab12 is
end entity tb_Lab12;

architecture test of tb_Lab12 is

    constant PERIOD : time := 20 ns;

    signal SysClk : std_logic := '0';
    signal Rst    : std_logic := '1';

    signal PC_out, IR_out, ALU_out, RegWrData : std_logic_vector(31 downto 0);
    signal RegWr    : std_logic;
    signal RegWrAddr : std_logic_vector(4 downto 0);
    signal MemBus_out : std_logic_vector(31 downto 0);
    signal MemWr      : std_logic;

    -- What the monitor observed, for the end-of-run checks.
    signal last_r1   : std_logic_vector(31 downto 0) := (others => 'U');
    signal last_r2   : std_logic_vector(31 downto 0) := (others => 'U');
    signal stored    : std_logic_vector(31 downto 0) := (others => 'U');
    signal saw_store : boolean := false;
    signal instr_count : natural := 0;

    signal running : boolean := true;

    -- Turn a 32-bit vector into readable hex for the trace.
    function hex (v : std_logic_vector) return string is
        constant DIGITS : string := "0123456789ABCDEF";
        variable u : unsigned(v'length - 1 downto 0) := unsigned(v);
        variable r : string(1 to v'length / 4);
    begin
        for i in r'range loop
            r(i) := DIGITS(to_integer(u(u'high downto u'high - 3)) + 1);
            u := shift_left(u, 4);
        end loop;
        return r;
    end function hex;

    -- Disassemble just enough to make the trace readable.
    function mnem (ir : std_logic_vector(31 downto 0)) return string is
        variable op : std_logic_vector(5 downto 0) := ir(31 downto 26);
        variable fn : std_logic_vector(5 downto 0) := ir(5 downto 0);
    begin
        if    op = "001111" then return "LUI ";
        elsif op = "001000" then return "ADDI";
        elsif op = "000110" then return "BLEZ";
        elsif op = "000010" then return "J   ";
        elsif op = "101011" then return "SW  ";
        elsif op = "100011" then return "LW  ";
        elsif op = "000000" and fn = "100000" then return "ADD ";
        elsif op = "000000" and fn = "000000" then return "SLL ";
        else                      return "??  ";
        end if;
    end function mnem;

begin

    DUT : entity work.CPU
        port map (SysClk => SysClk, Rst => Rst,
                  PC_out => PC_out, IR_out => IR_out, ALU_out => ALU_out,
                  RegWr => RegWr, RegWrAddr => RegWrAddr,
                  RegWrData => RegWrData,
                  MemBus_out => MemBus_out, MemWr => MemWr);

    clock_gen : process
    begin
        while running loop
            SysClk <= '0'; wait for PERIOD / 2;
            SysClk <= '1'; wait for PERIOD / 2;
        end loop;
        wait;
    end process clock_gen;

    ----------------------------------------------------------------------------
    -- Trace printer.
    --
    -- SAMPLE JUST BEFORE THE FALLING EDGE, never after it. After the edge the
    -- write has committed, and for a self-referencing instruction such as
    --     ADDI r1, r1, -1
    -- the combinational logic immediately recomputes from the NEW r1 - so a
    -- post-edge sample shows the result of the next iteration, not this one.
    -- The hardware is fine; the observer would be lying.
    ----------------------------------------------------------------------------
    tracer : process
        variable cyc : natural := 0;
    begin
        wait until Rst = '0';
        report "cyc | PC       | IR       | instr | ALUout   | wr | val" severity note;

        while running loop
            wait until rising_edge(SysClk);
            wait for PERIOD / 2 - 1 ns;      -- 1 ns before the falling edge
            if running and cyc < 50 then
                if RegWr = '1' then
                    report integer'image(cyc) & " | " & hex(PC_out) & " | " &
                           hex(IR_out) & " | " & mnem(IR_out) & "  | " &
                           hex(ALU_out) & " | r" &
                           integer'image(to_integer(unsigned(RegWrAddr))) &
                           " | " & hex(RegWrData) severity note;
                else
                    report integer'image(cyc) & " | " & hex(PC_out) & " | " &
                           hex(IR_out) & " | " & mnem(IR_out) & "  | " &
                           hex(ALU_out) & " |  - |" severity note;
                end if;
            end if;
            cyc := cyc + 1;
        end loop;
        wait;
    end process tracer;

    ----------------------------------------------------------------------------
    -- Monitor: records what the machine actually did, sampled at the same
    -- point as the trace (just before each commit).
    ----------------------------------------------------------------------------
    monitor : process
    begin
        wait until Rst = '0';
        while running loop
            wait until rising_edge(SysClk);
            wait for PERIOD / 2 - 1 ns;
            if running then
                instr_count <= instr_count + 1;
                if RegWr = '1' and RegWrAddr = "00001" then
                    last_r1 <= RegWrData;
                end if;
                if RegWr = '1' and RegWrAddr = "00010" then
                    last_r2 <= RegWrData;
                end if;
                if MemWr = '1' then
                    stored    <= MemBus_out;
                    saw_store <= true;
                end if;
            end if;
        end loop;
        wait;
    end process monitor;

    ----------------------------------------------------------------------------
    -- Run the program, then check the result
    ----------------------------------------------------------------------------
    stimulus : process
        variable errors : natural := 0;
    begin

        -- Release reset BETWEEN edges, in the middle of a low phase, so the
        -- next event is a RISING edge (fetch) and not a falling one (commit).
        -- Releasing it exactly on an edge is a race: the PC could advance
        -- before the first instruction has ever been fetched.
        Rst <= '1';
        wait for PERIOD * 2;
        wait for PERIOD / 4;
        Rst <= '0';

        -- 45 instructions, one per period, plus slack for the fetch pipeline.
        wait for PERIOD * 60;

        ------------------------------------------------------------------
        -- The program has run. Check the final state through the last
        -- observable write and the stored word.
        ------------------------------------------------------------------
        report "---- program complete ----" severity note;

        ------------------------------------------------------------------
        -- THE RESULT. Your CPU computes 2^10.
        ------------------------------------------------------------------
        -- If nothing was ever written, say so plainly rather than printing a
        -- hex value: the hex helper renders metavalues as 0, which would read
        -- as "expected 0, got 0" and waste a student's time.
        if is_x(last_r2) then
            report "FAIL: no write to r2 was ever observed - the CPU is not " &
                   "executing. Start at check 1 of the bisection method: is " &
                   "the PC advancing by 4?" severity error;
            errors := errors + 1;
        elsif last_r2 /= x"00000400" then
            report "FAIL: r2 should end at 0x00000400 (1024 = 2^10), got 0x" &
                   hex(last_r2) severity error;
            errors := errors + 1;
        end if;

        if is_x(last_r1) then
            report "FAIL: no write to r1 was ever observed." severity error;
            errors := errors + 1;
        elsif last_r1 /= x"00000000" then
            report "FAIL: r1 should end at 0 (the loop counter ran out), got 0x" &
                   hex(last_r1) severity error;
            errors := errors + 1;
        end if;

        if not saw_store then
            report "FAIL: the SW never executed - the loop did not exit"
                severity error;
            errors := errors + 1;
        elsif stored /= x"00000400" then
            report "FAIL: the stored word should be 0x00000400, got 0x" &
                   hex(stored) severity error;
            errors := errors + 1;
        end if;

        if not is_x(last_r1) then
            report "final r1     = 0x" & hex(last_r1) severity note;
        end if;
        if not is_x(last_r2) then
            report "final r2     = 0x" & hex(last_r2) & "   (= 1024 = 2^10)"
                severity note;
        end if;
        if saw_store then
            report "stored word  = 0x" & hex(stored) & "   at address 0"
                severity note;
        end if;

        if errors = 0 then
            report "PASS - Lab 12: the CPU computes 2^10 and stores it."
                severity note;
        else
            report "FAILED - Lab 12: " & integer'image(errors) &
                   " check(s) failed." severity error;
        end if;

        running <= false;
        wait;
    end process stimulus;

end architecture test;
