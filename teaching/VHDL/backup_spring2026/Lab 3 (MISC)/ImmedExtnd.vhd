library IEEE;
use IEEE.STD_LOGIC_1164.ALL;

-- Entity declaration:
-- This block extends a 16-bit immediate value to 32 bits.
-- No decoder constants are used here.
-- Instead, Sel directly controls the extension mode:
--   Sel = '0' -> zero extension
--   Sel = '1' -> sign extension
entity ImmedExtnd is
    Port (
        Sel   : in  STD_LOGIC;  -- Direct select: 0 = zero extend, 1 = sign extend
        In16  : in  STD_LOGIC_VECTOR(15 downto 0);   -- 16-bit input value
        Out32 : out STD_LOGIC_VECTOR(31 downto 0)    -- 32-bit extended output
    );
end ImmedExtnd;

architecture Behavioral of ImmedExtnd is
begin

    -- Combinational process:
    -- Updates the output whenever Sel or In16 changes.
    process(Sel, In16)
    begin
        if Sel = '0' then
            -- Zero extension:
            -- Fill the upper 16 bits with zeros.
            Out32 <= (15 downto 0 => '0') & In16;
        else
            -- Sign extension:
            -- Replicate the sign bit In16(15) into the upper 16 bits.
            Out32 <= (15 downto 0 => In16(15)) & In16;
        end if;
    end process;

end Behavioral;