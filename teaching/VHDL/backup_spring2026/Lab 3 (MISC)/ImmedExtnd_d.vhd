library IEEE;
use IEEE.STD_LOGIC_1164.ALL;
use work.EE362Decoder.ALL;

-- Entity declaration:
-- Extends a 16-bit immediate value to 32 bits.
-- The extension mode is selected by symbolic constants from EE362Decoder:
--   IR_XSEL_ZERO -> zero extension
--   IR_XSEL_SIGN -> sign extension
entity ImmedExtnd is
    Port (
        Sel   : in  STD_LOGIC;                      -- Extension select from decoder constants
        In16  : in  STD_LOGIC_VECTOR(15 downto 0); -- 16-bit input immediate
        Out32 : out STD_LOGIC_VECTOR(31 downto 0)  -- 32-bit extended output
    );
end ImmedExtnd;

architecture Behavioral of ImmedExtnd is
begin

    -- Combinational process:
    -- Output updates immediately when Sel or In16 changes.
    process(Sel, In16)
    begin
        if Sel = IR_XSEL_ZERO then
            -- Zero extension:
            -- fill the upper 16 bits with zeros
            Out32 <= (15 downto 0 => '0') & In16;

        elsif Sel = IR_XSEL_SIGN then
            -- Sign extension:
            -- copy the sign bit In16(15) into the upper 16 bits
            Out32 <= (15 downto 0 => In16(15)) & In16;

        else
            -- Safe default for undefined control values
            Out32 <= (others => '0');
        end if;
    end process;

end Behavioral;