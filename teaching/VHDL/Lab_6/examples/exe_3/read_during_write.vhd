--------------------------------------------------------------------------------
-- EE 362 - Computer Organization Laboratory
-- Lab 6, Example 3 - Read-during-write, and register zero
--
-- TWO DESIGN DECISIONS THAT LOOK LIKE DETAILS AND ARE NOT.
--
-- ============================================================================
-- 1. READ-DURING-WRITE
-- ============================================================================
-- What should a read port produce when it is addressing the very register
-- being written on this clock edge - the OLD value or the NEW one?
--
-- There is no universally right answer. Both are buildable:
--
--   READ-OLD  (write-first = false): the read port sees the value that was
--             there before the edge. This is what you get naturally from a
--             clocked write plus a combinational read, because the read
--             multiplexer is looking at the register's current output.
--
--   READ-NEW  (write-first = true): the read port is bypassed to the incoming
--             write data. Costs an extra comparator and mux per read port.
--
-- Your design will be READ-OLD unless you deliberately add the bypass. That is
-- correct for this CPU: in Lab 12 the register file is read at the START of a
-- cycle and written at the END of it, so the two never collide in a way that
-- matters.
--
-- WHAT YOU MUST DO: know which one you built, and say so in your report. A
-- student who cannot answer "old or new?" has not understood their own design.
--
-- ============================================================================
-- 2. REGISTER ZERO
-- ============================================================================
-- In MIPS, $0 always reads as zero. Not by convention that software politely
-- follows - the HARDWARE refuses to store into it.
--
--   We_k = Strb . m_k(Dsel) . [k /= 0]
--                             ^^^^^^^^
--                             this AND term is the whole mechanism
--
-- One extra condition on the write enable. That is what "hardwired to zero"
-- means: not a rule, a missing wire.
--
-- Why have such a register at all? Because it makes the instruction set
-- smaller. With a permanent zero you get several instructions for free:
--
--     move rd, rs      is    ADD rd, rs, $0
--     clear rd         is    ADD rd, $0, $0
--     compare-to-zero  is    SUB rt, rs, $0
--
-- and the Lab 12 program uses exactly this: SW r2, 0(r0) computes its address
-- as r0 + 0, which is 0. No special "absolute address" instruction needed.
--------------------------------------------------------------------------------

library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

entity read_during_write is
    port (
        Asel : in  std_logic_vector(1 downto 0);
        Dsel : in  std_logic_vector(1 downto 0);
        Din  : in  std_logic_vector(7 downto 0);
        Strb : in  std_logic;
        clk  : in  std_logic;
        Aout : out std_logic_vector(7 downto 0)
    );
end entity read_during_write;

architecture rtl of read_during_write is

    type reg_array is array (0 to 3) of std_logic_vector(7 downto 0);
    signal regs : reg_array := (others => (others => '0'));

begin

    process (clk)
    begin
        if rising_edge(clk) then
            -- The [k /= 0] term. Register 0 is never written, whatever Dsel says.
            if Strb = '1' and Dsel /= "00" then
                regs(to_integer(unsigned(Dsel))) <= Din;
            end if;
        end if;
    end process;

    -- Register 0 always reads as zero, regardless of what is in regs(0).
    -- Belt and braces: the write is blocked above AND the read is forced here.
    -- Either alone would work; both together mean a mistake in one place
    -- cannot produce a non-zero $0.
    Aout <= (others => '0') when Asel = "00"
       else regs(to_integer(unsigned(Asel)));

end architecture rtl;
