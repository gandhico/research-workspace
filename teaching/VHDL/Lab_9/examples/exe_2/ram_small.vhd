--------------------------------------------------------------------------------
-- EE 362 - Computer Organization Laboratory
-- Lab 9, Example 2 - A RAM, and the bus discipline around it
--
-- A RAM differs from a ROM in two ways: it can be written, and it shares its
-- data bus with whoever else writes to memory.
--
-- THE CONTROL SIGNALS - note the polarities, they are fixed by the CPU library
--
--   en   = '1'  the memory is selected at all
--   rw   = '1'  READ    (yes, '1' is read - check this twice)
--   rw   = '0'  WRITE
--   Strb = '1'  perform the write, on the FALLING clock edge
--
--   #  en  rw  Strb  ||  Data bus        memory
--   0   0   -   -    ||  Z...Z           hold
--   1   1   1   -    ||  M[A] word       hold          (read)
--   2   1   0   0    ||  Z...Z           hold
--   3   1   0   1    ||  Z (driven in)   M[A..A+3] <- Data   (write, at falling edge)
--
--   DataDrive = en . rw            <- when the RAM drives the bus
--   Write     = en . rw' . Strb    <- sampled at the falling edge
--
-- WHY 'inout'
--   The data bus is SHARED. On a read the RAM drives it; on a write the
--   register file drives it, through the TriBuffer you built in Lab 4. Exactly
--   one driver at a time - and that is what 'en . rw' enforces.
--
--   When the RAM is not driving it must release the bus to 'Z', not hold it at
--   '0'. Driving '0' would fight the other driver and give you 'X' across the
--   whole bus. This is Lab 4, applied for real.
--
-- WHY WRITES HAPPEN ON THE FALLING EDGE
--   In the Lab 12 CPU the instruction register loads on the RISING edge and
--   memory writes on the FALLING edge. That gives the address and data half a
--   clock period to settle before anything is stored. Two-phase timing, and it
--   is the reason the CPU works at all.
--------------------------------------------------------------------------------

library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

entity ram_small is
    port (
        Addr : in    std_logic_vector(31 downto 0);
        Strb : in    std_logic;
        rw   : in    std_logic;                       -- '1' read, '0' write
        en   : in    std_logic;
        clk  : in    std_logic;
        Data : inout std_logic_vector(31 downto 0)    -- SHARED bus
    );
end entity ram_small;

architecture rtl of ram_small is

    type ram_array is array (0 to 15) of std_logic_vector(7 downto 0);

    signal MEM  : ram_array := (others => x"00");
    signal base : natural range 0 to 12;
    signal word : std_logic_vector(31 downto 0);

begin

    base <= to_integer(unsigned(Addr(3 downto 0)));

    -- The stored word, always available internally...
    word <= MEM(base) & MEM(base + 1) & MEM(base + 2) & MEM(base + 3);

    -- ...but only DRIVEN onto the shared bus when this memory is reading.
    -- Otherwise: release to 'Z'. Never drive '0'.
    Data <= word when (en = '1' and rw = '1') else (others => 'Z');

    -- The write. Falling edge, so address and data have had half a period.
    process (clk)
    begin
        if falling_edge(clk) then
            if en = '1' and rw = '0' and Strb = '1' then
                MEM(base)     <= Data(31 downto 24);
                MEM(base + 1) <= Data(23 downto 16);
                MEM(base + 2) <= Data(15 downto  8);
                MEM(base + 3) <= Data( 7 downto  0);
            end if;
        end if;
    end process;

end architecture rtl;
