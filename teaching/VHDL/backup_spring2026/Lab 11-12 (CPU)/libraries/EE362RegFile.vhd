library IEEE;
use IEEE.STD_LOGIC_1164.ALL;

package RegFile_Pkg is
    type REGFILE_ARRAY is array (0 to 31) of STD_LOGIC_VECTOR(31 downto 0);

    component RegFile is
        port(
            ASel : in  STD_LOGIC_VECTOR(4 downto 0);
            BSel : in  STD_LOGIC_VECTOR(4 downto 0);
            WSel : in  STD_LOGIC_VECTOR(4 downto 0);
            Din  : in  STD_LOGIC_VECTOR(31 downto 0);
            Strb : in  STD_LOGIC;
            Clk  : in  STD_LOGIC;
            Aout : out STD_LOGIC_VECTOR(31 downto 0);
            Bout : out STD_LOGIC_VECTOR(31 downto 0)
        );
    end component;
end package;
