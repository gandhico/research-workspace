--------------------------------------------------------------------------------
-- EE 362 - Computer Organization Laboratory
-- Lab 6, Example 2 - A second read port, and why it is nearly free
--
-- Compare this file with Example 1. The difference is TWO LINES:
--
--     a Bsel input port
--     Bout <= regs(to_integer(unsigned(Bsel)));
--
-- The storage did not change at all. Only another multiplexer was added.
--
-- WHY READ PORTS ARE CHEAP AND WRITE PORTS ARE NOT
--   A read port is a multiplexer hanging off storage that already exists.
--   Adding one costs one more mux and nothing else - the registers are
--   untouched, and any number of readers can look at a register at once.
--
--   A write port is different. Two write ports mean two things might try to
--   store into the SAME register in the SAME cycle, and the hardware must
--   decide who wins. That needs arbitration, priority logic, and a decision
--   about what "both wrote" even means. It is not one more mux - it is a new
--   correctness problem.
--
--   Compare the E4 resource numbers for Example 1 and Example 2 to see the
--   read-port cost for yourself. It is small.
--
-- WHY THE CPU NEEDS EXACTLY TWO READS AND ONE WRITE
--   Look at any R-type instruction:  ADD rd, rs, rt
--   Two source registers are read, one destination register is written. Two
--   reads, one write - the register file's shape is dictated by the
--   instruction format, not chosen for convenience.
--
--   That is a genuine hardware/software interface point: the ISA and the
--   register file were designed against each other.
--------------------------------------------------------------------------------

library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

entity regfile_two_ports is
    port (
        Asel : in  std_logic_vector(1 downto 0);    -- read address A
        Bsel : in  std_logic_vector(1 downto 0);    -- read address B  <- new
        Dsel : in  std_logic_vector(1 downto 0);    -- write address
        Din  : in  std_logic_vector(7 downto 0);
        Strb : in  std_logic;
        clk  : in  std_logic;
        Aout : out std_logic_vector(7 downto 0);
        Bout : out std_logic_vector(7 downto 0)     -- read data B     <- new
    );
end entity regfile_two_ports;

architecture rtl of regfile_two_ports is

    type reg_array is array (0 to 3) of std_logic_vector(7 downto 0);
    signal regs : reg_array := (others => (others => '0'));

begin

    -- Write port: IDENTICAL to Example 1. Storage is unchanged.
    process (clk)
    begin
        if rising_edge(clk) then
            if Strb = '1' then
                regs(to_integer(unsigned(Dsel))) <= Din;
            end if;
        end if;
    end process;

    -- Two independent read multiplexers over the same storage.
    -- They can point at the same register with no conflict whatsoever -
    -- reading does not disturb anything.
    Aout <= regs(to_integer(unsigned(Asel)));
    Bout <= regs(to_integer(unsigned(Bsel)));

end architecture rtl;
