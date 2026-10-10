--------------------------------------------------------------------------------
-- EE 362 - Computer Organization Laboratory
-- Lab 6, Example 1 - A register file small enough to watch
--
-- 4 registers, 8 bits each, one read port. The real thing is 32 x 32 with two
-- read ports, which is the same design and impossible to see in a waveform.
-- Get it here, then scale it.
--
-- THREE THINGS YOU ALREADY OWN
--   A register file is not a new kind of component. It is:
--
--     an address DECODER  (Lab 0)  -> which register does this address mean?
--     an array of REGISTERS (Lab 2) -> each one is your RegN
--     a MULTIPLEXER       (Lab 3)  -> which register's output goes to the port?
--
--   That is the whole thing. Nothing else is happening.
--
-- THE ARRAY TYPE
--   A VHDL array of vectors gives you storage indexed by a number:
--
--       type reg_array is array (0 to 3) of std_logic_vector(7 downto 0);
--       signal regs : reg_array;
--
--   regs(2) is the third register. The index must be an INTEGER, which is why
--   the address arrives as bits and gets converted - Lab 4, Example 3.
--
-- WRITE IS CLOCKED, READS ARE NOT
--   The write happens on a clock edge, because storage needs an edge to be
--   unambiguous. The reads are plain combinational lookups: change the address
--   and the output follows immediately, no clock involved.
--
--   That asymmetry is deliberate and it is what the CPU needs. In Lab 12 the
--   register file must produce both operands DURING a cycle, and store the
--   result AT THE END of it.
--------------------------------------------------------------------------------

library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

entity regfile_small is
    port (
        Asel : in  std_logic_vector(1 downto 0);    -- read address
        Dsel : in  std_logic_vector(1 downto 0);    -- write address
        Din  : in  std_logic_vector(7 downto 0);    -- write data
        Strb : in  std_logic;                       -- write enable
        clk  : in  std_logic;
        Aout : out std_logic_vector(7 downto 0)     -- read data
    );
end entity regfile_small;

architecture rtl of regfile_small is

    type reg_array is array (0 to 3) of std_logic_vector(7 downto 0);

    -- Initialised so the waveform shows zeros rather than 'U' at time zero.
    -- Real hardware does not power up zeroed; this is a simulation convenience
    -- and you should say so if you rely on it.
    signal regs : reg_array := (others => (others => '0'));

begin

    ----------------------------------------------------------------------------
    -- WRITE PORT - clocked.
    -- The decoder is implicit: regs(index) selects one register, which is
    -- exactly what a 2-to-4 decoder driving four write-enables would do.
    ----------------------------------------------------------------------------
    process (clk)
    begin
        if rising_edge(clk) then
            if Strb = '1' then
                regs(to_integer(unsigned(Dsel))) <= Din;
            end if;
            -- no else: not writing means hold, exactly as in Lab 2
        end if;
    end process;

    ----------------------------------------------------------------------------
    -- READ PORT - combinational.
    -- This single line is a 4-to-1 multiplexer, 8 bits wide. The synthesiser
    -- builds one; look at the RTL Viewer and you will see it.
    ----------------------------------------------------------------------------
    Aout <= regs(to_integer(unsigned(Asel)));

end architecture rtl;
