library IEEE;
use IEEE.STD_LOGIC_1164.ALL;
use work.ALU_Pkg.all;

package NIAG_Pkg is
    component NIAG is
        port(
            Target  : in  STD_LOGIC_VECTOR(25 downto 0);
            Immed   : in  STD_LOGIC_VECTOR(31 downto 0);
            Reg     : in  STD_LOGIC_VECTOR(31 downto 0);
            Xshft   : in  STD_LOGIC;
            PCin    : in  STD_LOGIC_VECTOR(31 downto 0);
            Cond    : in  STD_LOGIC_VECTOR(2 downto 0);
            Sel     : in  STD_LOGIC_VECTOR(1 downto 0);
            Stat    : in  STAT_SIGNL_REC;
            MemAdrs : out STD_LOGIC_VECTOR(31 downto 0);
            RtnAdrs : out STD_LOGIC_VECTOR(31 downto 0)
        );
    end component;

    component NIAG_NSA is
        port(PC : in STD_LOGIC_VECTOR(31 downto 0); NSA : out STD_LOGIC_VECTOR(31 downto 0));
    end component;

    component NIAG_Abslt is
        port(
            Index     : in  STD_LOGIC_VECTOR(25 downto 0);
            NSA       : in  STD_LOGIC_VECTOR(31 downto 0);
            AbsltAdrs : out STD_LOGIC_VECTOR(31 downto 0)
        );
    end component;

    component NIAG_Rel is
        port(
            Immed   : in  STD_LOGIC_VECTOR(31 downto 0);
            Xshft   : in  STD_LOGIC;
            NSA     : in  STD_LOGIC_VECTOR(31 downto 0);
            RelAdrs : out STD_LOGIC_VECTOR(31 downto 0)
        );
    end component;

    component NIAG_Reg is
        port(Reg : in STD_LOGIC_VECTOR(31 downto 0); RegAdrs : out STD_LOGIC_VECTOR(31 downto 0));
    end component;

    component NIAG_Rtn is
        port(PC : in STD_LOGIC_VECTOR(31 downto 0); RtnAdrs : out STD_LOGIC_VECTOR(31 downto 0));
    end component;

    component NIAG_MUX is
        port(
            NxtAdrs   : in  STD_LOGIC_VECTOR(31 downto 0);
            AbsltAdrs : in  STD_LOGIC_VECTOR(31 downto 0);
            RelAdrs   : in  STD_LOGIC_VECTOR(31 downto 0);
            RegAdrs   : in  STD_LOGIC_VECTOR(31 downto 0);
            Cond      : in  STD_LOGIC_VECTOR(2 downto 0);
            Sel       : in  STD_LOGIC_VECTOR(1 downto 0);
            Stat      : in  STAT_SIGNL_REC;
            InstrAdrs : out STD_LOGIC_VECTOR(31 downto 0)
        );
    end component;
end package;
