library IEEE;
use IEEE.STD_LOGIC_1164.ALL;
use IEEE.NUMERIC_STD.ALL;
use work.RegFile_Pkg.all;

entity RegFile is
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
end RegFile;

architecture Behavioral of RegFile is
    signal Regs : REGFILE_ARRAY := (others => (others => '0'));
begin
    Aout <= (others => '0') when ASel = "00000" else Regs(to_integer(unsigned(ASel)));
    Bout <= (others => '0') when BSel = "00000" else Regs(to_integer(unsigned(BSel)));

    process(Clk)
        variable widx : integer;
    begin
        if falling_edge(Clk) then
            if Strb = '1' then
                widx := to_integer(unsigned(WSel));
                if widx /= 0 then
                    Regs(widx) <= Din;
                end if;
            end if;
            Regs(0) <= (others => '0');
        end if;
    end process;
end Behavioral;
