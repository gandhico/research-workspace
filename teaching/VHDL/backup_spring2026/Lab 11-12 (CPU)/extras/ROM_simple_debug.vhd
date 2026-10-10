library IEEE;
use IEEE.STD_LOGIC_1164.ALL;
use IEEE.NUMERIC_STD.ALL;
use work.Memory_Pkg.ALL;

entity ROM is
    port(
        Addr : in  STD_LOGIC_VECTOR(31 downto 0);
        Data : out STD_LOGIC_VECTOR(31 downto 0)
    );
end ROM;

architecture Behavioral of ROM is
    constant Mem : ROM_Memory := (
        16#00# => x"20", 16#01# => x"01", 16#02# => x"00", 16#03# => x"0A", -- ADDI r1, r0, 10
        16#04# => x"20", 16#05# => x"02", 16#06# => x"00", 16#07# => x"0F", -- ADDI r2, r0, 15
        16#08# => x"00", 16#09# => x"22", 16#0A# => x"18", 16#0B# => x"20", -- ADD  r3, r1, r2
        others => x"00"
    );

    function ReadWord(memory : ROM_Memory; base : integer) return STD_LOGIC_VECTOR is
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
    Data <= ReadWord(Mem, to_integer(unsigned(Addr)));
end Behavioral;
