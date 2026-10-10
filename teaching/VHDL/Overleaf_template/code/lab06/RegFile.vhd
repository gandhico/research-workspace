-- PLACEHOLDER: replace with YOUR OWN RegFile.vhd
--------------------------------------------------------------------------------
-- EE 362 - Computer Organization Laboratory
-- Lab 6 - Assignment: the Register File
--
-- YOUR NAME  :
-- SECTION    :  Monday / Tuesday
-- DATE       :
--
-- 32 registers, 32 bits each. Two combinational read ports, one clocked write
-- port, and register 0 permanently zero.
--
-- THIS IS SMALLER THAN IT LOOKS. Three components you already own:
--
--     an address DECODER   (Lab 0)  -> which register does this address mean?
--     an array of REGISTERS (Lab 2) -> each cell is your RegN
--     two MULTIPLEXERS     (Lab 3)  -> which register reaches each read port?
--
-- After the ALU this is a light week. Do not be intimidated by "32 registers".
--
-- SPECIFICATION - Table C
--
--   #  Strb  Dsel      ||  effect at the rising edge
--   0    0    -        ||  no write
--   1    1    "00000"  ||  NO WRITE - register 0 is hardwired
--   2    1    k /= 0   ||  R_k <- Din
--
--   Reads are combinational and always valid:
--       Aout = R[Asel],  Bout = R[Bsel],  with R[0] identically zero
--
-- EQUATIONS
--
--   address minterm   m_k(S) = 1 iff S = k          (a 5-to-32 decoder)
--
--   write enable      We_k = Strb . m_k(Dsel) . [k /= 0]
--                                                ^^^^^^^^
--                                   THIS TERM IS "HARDWIRED TO ZERO".
--                                   Not a convention. A missing wire.
--
--   storage           R_k+ = We_k.Din + We_k'.R_k       <- Lab 2's register,
--                                                          thirty-two times
--
--   read port A       Aout = SUM over k of m_k(Asel).R_k     <- a 32-to-1 mux
--                     R_0 is identically 0, so k=0 contributes nothing
--
-- WHY $0 EXISTS
--   A permanent zero makes the instruction set smaller. You get several
--   instructions free:
--       move rd, rs   is   ADD rd, rs, $0
--       clear rd      is   ADD rd, $0, $0
--   and the Lab 12 program relies on it: SW r2, 0(r0) computes its address as
--   r0 + 0 = 0, with no special "absolute address" instruction needed.
--
-- READ-DURING-WRITE
--   If a read port addresses the register being written on the same edge, does
--   it see the old value or the new one? Example 3 shows this design is
--   READ-OLD. You must STATE which behaviour yours has in your report.
--   "I do not know" is not an acceptable answer about your own design.
--
-- PORT NAMES ARE FIXED. They come from the original EE 362 CPU library, and the
-- CPU in Lab 12 instantiates this entity by these exact names. Do not rename.
--------------------------------------------------------------------------------

library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

entity RegFile is
    port (
        Asel : in  std_logic_vector(4 downto 0);    -- read address A
        Bsel : in  std_logic_vector(4 downto 0);    -- read address B
        Dsel : in  std_logic_vector(4 downto 0);    -- write address
        Din  : in  std_logic_vector(31 downto 0);   -- write data
        Strb : in  std_logic;                       -- write enable
        clk  : in  std_logic;
        Aout : out std_logic_vector(31 downto 0);   -- read data A
        Bout : out std_logic_vector(31 downto 0)    -- read data B
    );
end entity RegFile;

architecture rtl of RegFile is

    -- TODO 1: declare the storage.
    --         An array of 32 elements, each a 32-bit std_logic_vector.
    --         Follow the pattern from Example 1:
    --             type reg_array is array (0 to 31) of std_logic_vector(31 downto 0);
    --         Initialise it to zeros so the waveform is readable at time 0.


begin

    ----------------------------------------------------------------------------
    -- TODO 2: the WRITE port. Clocked.
    --
    --   - rising edge only
    --   - write when Strb is asserted
    --   - AND when Dsel is not register 0
    --
    -- The register-0 condition is the [k /= 0] term of the equation above.
    -- One extra condition, and $0 becomes physically unwritable.
    ----------------------------------------------------------------------------


    ----------------------------------------------------------------------------
    -- TODO 3: the two READ ports. Combinational - no clock.
    --
    --   Aout is R[Asel], except that address 0 always reads as zero.
    --   Bout is R[Bsel], same rule.
    --
    -- Blocking the write (TODO 2) and forcing the read (here) are belt and
    -- braces: either alone would work, but with both, a mistake in one place
    -- still cannot produce a non-zero $0.
    ----------------------------------------------------------------------------


end architecture rtl;
