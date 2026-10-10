--------------------------------------------------------------------------------
-- EE 362 - Lab 12 - REFERENCE COMPONENT
--
-- This is the TA reference implementation, provided so that nobody is blocked
-- from building the CPU by an earlier lab that did not finish.
--
--   >>> REPLACE THIS FILE WITH YOUR OWN VERSION IF YOU HAVE ONE. <<<
--
-- Using a reference component costs you nothing on this lab. Your grade for
-- the earlier lab simply stands as it was. Integration is never gated on an
-- earlier miss - that is a deliberate rule of this course, not a favour.
--------------------------------------------------------------------------------

--------------------------------------------------------------------------------
-- EE 362 - Lab 6 reference component
--
-- RegFile : 32 x 32, two combinational read ports, one clocked write port,
--           register 0 hardwired to zero.
--
--   We_k = Strb . m_k(Dsel) . [k /= 0]
--   R_k+ = We_k.Din + We_k'.R_k
--   Aout = SUM m_k(Asel).R_k,  R_0 identically zero
--
-- Read-during-write behaviour: READ-OLD. The read multiplexers look at stored
-- outputs, and nothing is stored until the edge. No bypass path is built.
--
-- Points to check when marking:
--   * register 0 blocked on the WRITE side (Dsel /= "00000")
--   * register 0 forced on the READ side as well
--   * reads are outside the clocked process
--   * no 'else' on the Strb test - not writing means hold
--------------------------------------------------------------------------------

library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

entity RegFile is
    port (
        Asel : in  std_logic_vector(4 downto 0);
        Bsel : in  std_logic_vector(4 downto 0);
        Dsel : in  std_logic_vector(4 downto 0);
        Din  : in  std_logic_vector(31 downto 0);
        Strb : in  std_logic;
        clk  : in  std_logic;
        Aout : out std_logic_vector(31 downto 0);
        Bout : out std_logic_vector(31 downto 0)
    );
end entity RegFile;

architecture rtl of RegFile is

    type reg_array is array (0 to 31) of std_logic_vector(31 downto 0);

    signal regs : reg_array := (others => (others => '0'));

begin

    ----------------------------------------------------------------------------
    -- Write port: clocked. The Dsel /= "00000" term is the whole of
    -- "register 0 is hardwired".
    ----------------------------------------------------------------------------
    process (clk)
    begin
        if rising_edge(clk) then
            if Strb = '1' and Dsel /= "00000" then
                regs(to_integer(unsigned(Dsel))) <= Din;
            end if;
            -- no else: not writing means hold
        end if;
    end process;

    ----------------------------------------------------------------------------
    -- Read ports: combinational 32-to-1 multiplexers, with address 0 forced.
    ----------------------------------------------------------------------------
    Aout <= (others => '0') when Asel = "00000"
       else regs(to_integer(unsigned(Asel)));

    Bout <= (others => '0') when Bsel = "00000"
       else regs(to_integer(unsigned(Bsel)));

end architecture rtl;
