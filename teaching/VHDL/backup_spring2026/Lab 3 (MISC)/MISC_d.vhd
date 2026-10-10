library IEEE;
use IEEE.STD_LOGIC_1164.ALL;
use work.EE362Decoder.ALL;

-- Entity declaration:
-- Top-level block for the MISC lab.
-- It connects:
--   1) the 16-to-32 immediate extender
--   2) the tri-state buffer
--
-- The control signals are expected to use symbolic constants
-- from EE362Decoder.
entity MISC is
    Port (
        SelExt : in  STD_LOGIC;                      -- IR_XSEL_ZERO or IR_XSEL_SIGN
        SelOE  : in  STD_LOGIC;                      -- RF_OE_DRIVE or RF_OE_HiZ
        In16   : in  STD_LOGIC_VECTOR(15 downto 0); -- Input to extender
        TriIn  : in  STD_LOGIC;                      -- Input to tri-state buffer
        Out32  : out STD_LOGIC_VECTOR(31 downto 0); -- Extended 32-bit output
        TriOut : out STD_LOGIC                       -- Tri-state output
    );
end MISC;

architecture Structural of MISC is

    -- Component declaration for the immediate extender
    component ImmedExtnd
        Port (
            Sel   : in  STD_LOGIC;
            In16  : in  STD_LOGIC_VECTOR(15 downto 0);
            Out32 : out STD_LOGIC_VECTOR(31 downto 0)
        );
    end component;

    -- Component declaration for the tri-state buffer
    component TriBuffer
        Port (
            OE   : in  STD_LOGIC;
            INP  : in  STD_LOGIC;
            OUTP : out STD_LOGIC
        );
    end component;

begin

    -- Extender instance:
    -- uses SelExt to choose zero extension or sign extension
    U1: ImmedExtnd
        port map (
            Sel   => SelExt,
            In16  => In16,
            Out32 => Out32
        );

    -- Tri-state buffer instance:
    -- uses SelOE to choose DRIVE or Hi-Z
    U2: TriBuffer
        port map (
            OE   => SelOE,
            INP  => TriIn,
            OUTP => TriOut
        );

end Structural;