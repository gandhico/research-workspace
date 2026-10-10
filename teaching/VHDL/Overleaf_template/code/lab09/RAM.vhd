-- PLACEHOLDER: replace with YOUR OWN RAM.vhd
--------------------------------------------------------------------------------
-- EE 362 - Computer Organization Laboratory
-- Lab 9 - Assignment, Part 2 of 2
--
-- RAM : 512-byte data memory on a shared bus
--
-- YOUR NAME  :
-- SECTION    :  Monday / Tuesday
-- DATE       :
--
-- SPECIFICATION - Table C.  CHECK THE POLARITIES TWICE: rw = '1' is READ.
--
--   #  en  rw  Strb  ||  Data bus         memory at the falling edge
--   0   0   -   -    ||  Z...Z            hold
--   1   1   1   -    ||  M[A] word        hold                   (read)
--   2   1   0   0    ||  Z...Z            hold
--   3   1   0   1    ||  Z (driven in)    M[A..A+3] <- Data      (write)
--
-- EQUATIONS
--   DataDrive = en . rw                 -- when this memory drives the bus
--   Write     = en . rw' . Strb         -- sampled at the FALLING edge
--
-- THE BUS IS SHARED - this is Lab 4 for real
--   On a read the RAM drives the data bus. On a write the register file drives
--   it, through the TriBuffer you built in Lab 4. Exactly ONE driver at a time.
--
--   When this memory is not driving it must RELEASE the bus to 'Z'. Driving
--   '0' instead would fight the other driver and produce 'X' across all 32
--   bits - and in Lab 12 that shows up as a store that writes garbage.
--
--   This is why the port is 'inout' and why the drive condition is en AND rw.
--
-- WHY WRITES HAPPEN ON THE FALLING EDGE
--   In the Lab 12 CPU the instruction register loads on the RISING edge and
--   memory writes on the FALLING edge. That gives the address and the data half
--   a clock period to settle before anything is committed. Two-phase timing,
--   and it is the reason the whole machine works.
--
--   Get this edge wrong and Lab 12 will store the right value at the wrong
--   moment - which looks like random corruption.
--
-- BIG-ENDIAN, same as the ROM. Both memories must agree, obviously.
--------------------------------------------------------------------------------

library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

entity RAM is
    port (
        Addr : in    std_logic_vector(31 downto 0);
        Strb : in    std_logic;
        rw   : in    std_logic;                       -- '1' READ, '0' WRITE
        en   : in    std_logic;
        clk  : in    std_logic;
        Data : inout std_logic_vector(31 downto 0)    -- SHARED bus
    );
end entity RAM;

architecture rtl of RAM is

    type ram_array is array (0 to 511) of std_logic_vector(7 downto 0);

    signal MEM : ram_array := (others => x"00");

    -- TODO 1: declare a signal for the byte index, and one for the assembled
    --         stored word. Doing the assembly once into a signal is much
    --         clearer than repeating it inside the bus expression.


begin

    -- TODO 2: reduce Addr to a valid byte index, and assemble the stored word
    --         (big-endian, four bytes). Guard the range as you did in the ROM.


    -- TODO 3: drive the bus ONLY when this memory is reading.
    --         Otherwise release it with (others => 'Z').
    --         Never drive '0' when you mean "not driving".


    -- TODO 4: the write process.
    --         FALLING edge. Split the incoming 32-bit Data into four bytes and
    --         store them big-endian, at the same four addresses you read from.
    --         Condition: en = '1' and rw = '0' and Strb = '1'.


end architecture rtl;
