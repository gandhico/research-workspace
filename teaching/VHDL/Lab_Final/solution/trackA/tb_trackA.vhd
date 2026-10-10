--------------------------------------------------------------------------------
-- EE 362 - Final Lab, Track A REFERENCE testbench  (TA only)
--
-- Verifies a new instruction at BOTH levels, which is the whole point of the
-- track:
--
--   1. the DECODER produces the right control bundle for it
--   2. the CPU actually executes it, in a program
--
-- Either one alone is insufficient. A decoder row that is right in isolation
-- can still be wired to a datapath that cannot carry it out; a program that
-- gets the right answer can do so for the wrong reason.
--------------------------------------------------------------------------------

library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

use work.CPU_Pkg.all;

entity tb_trackA is
end entity tb_trackA;

architecture test of tb_trackA is

    constant PERIOD : time := 20 ns;

    -- decoder-level check
    signal Instr : std_logic_vector(31 downto 0) := (others => '0');
    signal Ctrl  : CTRL_REC;

    -- CPU-level check
    signal SysClk : std_logic := '0';
    signal Rst    : std_logic := '1';
    signal PC_out, IR_out, ALU_out, RegWrData, MemBus_out : std_logic_vector(31 downto 0);
    signal RegWr, MemWr : std_logic;
    signal RegWrAddr : std_logic_vector(4 downto 0);

    signal running : boolean := true;
    signal last_r1 : std_logic_vector(31 downto 0) := (others => 'U');
    signal stored  : std_logic_vector(31 downto 0) := (others => 'U');
    signal saw_store : boolean := false;

begin

    U_DEC : entity work.Decoder
        port map (Instr => Instr, Ctrl => Ctrl);

    U_CPU : entity work.CPU
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

    monitor : process
    begin
        wait until Rst = '0';
        while running loop
            wait until rising_edge(SysClk);
            wait for PERIOD / 2 - 1 ns;
            if running then
                if RegWr = '1' and RegWrAddr = "00001" then
                    last_r1 <= RegWrData;
                end if;
                if MemWr = '1' then
                    stored <= MemBus_out; saw_store <= true;
                end if;
            end if;
        end loop;
        wait;
    end process monitor;

    stimulus : process
        variable errors : natural := 0;

        procedure chk (cond : in boolean; msg : in string) is
        begin
            if not cond then
                report "FAIL: " & msg severity error;
                errors := errors + 1;
            end if;
        end procedure chk;
    begin

        ----------------------------------------------------------------------
        -- LEVEL 1: the decoder row.  ORI r1, r1, 0x00F0 = 0x342100F0
        ----------------------------------------------------------------------
        Instr <= x"342100F0"; wait for 10 ns;

        chk(Ctrl.ALU_func = ALU_FUNC_OR,    "1. ORI: the ALU ORs");
        chk(Ctrl.ALU_Asel = ALU_ASEL_IMMED, "2. ORI: A input is the immediate");
        chk(Ctrl.IR_Xsel  = IR_XSEL_ZERO,
            "3. ORI: ZERO-extends - the immediate is a bit pattern");
        chk(Ctrl.IR_Xlsft = IR_XLSFT_NONE,  "4. ORI: not scaled");
        chk(Ctrl.RF_Wsel  = RF_WSEL_RT,     "5. ORI: destination is rt");
        chk(Ctrl.RF_strb  = RF_STRB_STROBE, "6. ORI: a register is written");
        chk(Ctrl.DM_en    = DM_EN_DISABLE,  "7. ORI: memory untouched");
        chk(Ctrl.RF_oe    = RF_OE_HIZ,      "8. ORI: bus not driven");

        -- the existing instructions must still decode correctly
        Instr <= x"2021FFFF"; wait for 10 ns;
        chk(Ctrl.IR_Xsel = IR_XSEL_SIGN,
            "9. ADDI still sign-extends - the new row broke nothing");
        Instr <= x"AC020000"; wait for 10 ns;
        chk(Ctrl.RF_strb = RF_STRB_HOLD,
            "10. SW still writes no register");

        ----------------------------------------------------------------------
        -- LEVEL 2: the CPU runs the program
        ----------------------------------------------------------------------
        Rst <= '1';
        wait for PERIOD * 2;
        wait for PERIOD / 4;
        Rst <= '0';

        wait for PERIOD * 12;

        chk(last_r1 = x"000000FF",
            "11. after two ORIs, r1 = 0x000000FF");
        chk(saw_store, "12. the SW executed");
        chk(stored = x"000000FF", "13. 0x000000FF was stored at address 0");

        if not is_x(last_r1) then
            report "final r1    = 0x" & to_hstring(last_r1) severity note;
        end if;
        if saw_store then
            report "stored word = 0x" & to_hstring(stored) severity note;
        end if;

        if errors = 0 then
            report "PASS - Track A: ORI decodes correctly AND executes in the CPU."
                severity note;
        else
            report "FAILED - Track A: " & integer'image(errors) &
                   " check(s) failed." severity error;
        end if;

        running <= false;
        wait;
    end process stimulus;

end architecture test;
