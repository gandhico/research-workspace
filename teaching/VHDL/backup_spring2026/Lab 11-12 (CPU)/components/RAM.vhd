library IEEE;
use IEEE.STD_LOGIC_1164.ALL;
use IEEE.NUMERIC_STD.ALL;
use work.Memory_Pkg.ALL;

entity RAM is
    port(
        Addr : in    STD_LOGIC_VECTOR(31 downto 0);
        Strb : in    STD_LOGIC;
        rw   : in    STD_LOGIC;
        en   : in    STD_LOGIC;
        clk  : in    STD_LOGIC;
        Data : inout STD_LOGIC_VECTOR(31 downto 0)
    );
end RAM;

architecture Behavioral of RAM is
    signal Mem : RAM_Memory := (others => x"00");
    signal read_word : STD_LOGIC_VECTOR(31 downto 0);

    function ReadWord(memory : RAM_Memory; base : integer) return STD_LOGIC_VECTOR is
        variable result : STD_LOGIC_VECTOR(31 downto 0) := (others => '0');
    begin
        if (base >= 0) and (base <= 511) then
            if base     <= 511 then result(31 downto 24) := memory(base);     end if;
            if base + 1 <= 511 then result(23 downto 16) := memory(base + 1); end if;
            if base + 2 <= 511 then result(15 downto 8)  := memory(base + 2); end if;
            if base + 3 <= 511 then result(7 downto 0)   := memory(base + 3); end if;
        end if;
        return result;
    end function;
begin
    read_word <= ReadWord(Mem, to_integer(unsigned(Addr)));
    Data <= read_word when (en = '1' and rw = '1') else (others => 'Z');

    process(clk)
        variable base : integer;
    begin
        if falling_edge(clk) then
            base := to_integer(unsigned(Addr));
            if en = '1' and rw = '0' and Strb = '1' then
                if base     <= 511 then Mem(base)     <= Data(31 downto 24); end if;
                if base + 1 <= 511 then Mem(base + 1) <= Data(23 downto 16); end if;
                if base + 2 <= 511 then Mem(base + 2) <= Data(15 downto 8);  end if;
                if base + 3 <= 511 then Mem(base + 3) <= Data(7 downto 0);   end if;
            end if;
        end if;
    end process;
end Behavioral;
