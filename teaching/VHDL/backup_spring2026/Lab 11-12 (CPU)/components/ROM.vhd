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
        -- Official CPU Lab program from the handout.
        16#00# => x"3C", 16#01# => x"01", 16#02# => x"00", 16#03# => x"0B", -- LUI  r1, 0x000B
        16#04# => x"3C", 16#05# => x"02", 16#06# => x"00", 16#07# => x"01", -- LUI  r2, 0x0001
        16#08# => x"20", 16#09# => x"21", 16#0A# => x"FF", 16#0B# => x"FF", -- ADDI r1, r1, -1
        16#0C# => x"18", 16#0D# => x"20", 16#0E# => x"00", 16#0F# => x"02", -- BLEZ r1, +2
        16#10# => x"00", 16#11# => x"02", 16#12# => x"10", 16#13# => x"40", -- SLL  r2, r2, 1
        16#14# => x"08", 16#15# => x"00", 16#16# => x"00", 16#17# => x"02", -- J    top_of_loop
        16#18# => x"AC", 16#19# => x"02", 16#1A# => x"00", 16#1B# => x"00", -- SW   r2, 0(r0)
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
