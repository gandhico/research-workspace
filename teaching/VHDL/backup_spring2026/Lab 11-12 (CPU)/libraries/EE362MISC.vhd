library IEEE;
use IEEE.STD_LOGIC_1164.ALL;

package MISC_Pkg is
    component ImmedXtnd is
        port(
            Sel  : in  STD_LOGIC;
            In16 : in  STD_LOGIC_VECTOR(15 downto 0);
            Out32: out STD_LOGIC_VECTOR(31 downto 0)
        );
    end component;

    component ALUinMUX is
        port(
            Sel  : in  STD_LOGIC;
            In0  : in  STD_LOGIC_VECTOR(31 downto 0);
            In1  : in  STD_LOGIC_VECTOR(31 downto 0);
            Y    : out STD_LOGIC_VECTOR(31 downto 0)
        );
    end component;

    component ALUsftMUX is
        port(
            Sel  : in  STD_LOGIC;
            In0  : in  STD_LOGIC_VECTOR(4 downto 0);
            In1  : in  STD_LOGIC_VECTOR(4 downto 0);
            Y    : out STD_LOGIC_VECTOR(4 downto 0)
        );
    end component;

    component DselMUX is
        port(
            Sel  : in  STD_LOGIC_VECTOR(1 downto 0);
            Rd   : in  STD_LOGIC_VECTOR(4 downto 0);
            Rt   : in  STD_LOGIC_VECTOR(4 downto 0);
            Y    : out STD_LOGIC_VECTOR(4 downto 0)
        );
    end component;

    component DinMUX is
        port(
            Sel  : in  STD_LOGIC_VECTOR(1 downto 0);
            In0  : in  STD_LOGIC_VECTOR(31 downto 0);
            In1  : in  STD_LOGIC_VECTOR(31 downto 0);
            In2  : in  STD_LOGIC_VECTOR(31 downto 0);
            Y    : out STD_LOGIC_VECTOR(31 downto 0)
        );
    end component;

    component TriBuffer is
        port(
            En   : in  STD_LOGIC;
            Din  : in  STD_LOGIC_VECTOR(31 downto 0);
            Dout : out STD_LOGIC_VECTOR(31 downto 0)
        );
    end component;
end package;
