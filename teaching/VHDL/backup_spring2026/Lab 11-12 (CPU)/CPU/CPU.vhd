library IEEE;
use IEEE.STD_LOGIC_1164.ALL;
use IEEE.NUMERIC_STD.ALL;

use work.ALU_Pkg.all;
use work.DecodeLogic_Pkg.all;
use work.Memory_Pkg.all;
use work.NIAG_Pkg.all;
use work.RegFile_Pkg.all;
use work.MISC_Pkg.all;

entity CPU is
    port(
        SysClk : in STD_LOGIC
    );
end CPU;

architecture Template of CPU is
    signal PCreg        : STD_LOGIC_VECTOR(31 downto 0) := (others => '0');
    signal IRreg        : STD_LOGIC_VECTOR(31 downto 0) := (others => '0');
    signal IMemData     : STD_LOGIC_VECTOR(31 downto 0);
    signal Ctrl         : CTRL_SIGNL_REC;
    signal Rfmt         : R_INSTRUCTION;
    signal Ifmt         : I_INSTRUCTION;
    signal Jfmt         : J_INSTRUCTION;
    signal XtndrOut     : STD_LOGIC_VECTOR(31 downto 0);
    signal RegFileAout  : STD_LOGIC_VECTOR(31 downto 0);
    signal RegFileBout  : STD_LOGIC_VECTOR(31 downto 0);
    signal ALUinMUXout  : STD_LOGIC_VECTOR(31 downto 0);
    signal ALUsftMUXout : STD_LOGIC_VECTOR(4 downto 0);
    signal ALUout       : STD_LOGIC_VECTOR(31 downto 0);
    signal ALUstat      : STAT_SIGNL_REC;
    signal NIAGout      : STD_LOGIC_VECTOR(31 downto 0);
    signal RtnAdrs      : STD_LOGIC_VECTOR(31 downto 0);
    signal DselMUXout   : STD_LOGIC_VECTOR(4 downto 0);
    signal DinMUXout    : STD_LOGIC_VECTOR(31 downto 0);
    signal TriOut       : STD_LOGIC_VECTOR(31 downto 0);
    signal MemDataBus   : STD_LOGIC_VECTOR(31 downto 0);
begin
    -- Decode helpers.
    Rfmt <= IR_to_Rtype(IRreg);
    Ifmt <= IR_to_Itype(IRreg);
    Jfmt <= IR_to_Jtype(IRreg);

    --------------------------------------------------------------------------
    -- TODO: instantiate ROM, Decoder, ImmedXtnd, RegFile, ALUinMUX,
    -- ALUsftMUX, ALU, NIAG, DselMUX, TriBuffer, RAM, and DinMUX.
    -- Use the CPU block diagram to route the instruction fields, control
    -- signals, ALU result, memory bus, and return address correctly.
    --------------------------------------------------------------------------

    -- Example idea:
    -- U_ROM : entity work.ROM
    --     port map(Addr => PCreg, Data => IMemData);

    --------------------------------------------------------------------------
    -- TODO: on the rising edge of SysClk, load IRreg from IMemData.
    -- TODO: on the falling edge of SysClk, load PCreg from NIAGout when
    --       Ctrl.NIAG_strb is asserted.
    --------------------------------------------------------------------------

    -- Hint:
    -- process(SysClk)
    -- begin
    --     if rising_edge(SysClk) then
    --         IRreg <= IMemData;
    --     end if;
    -- end process;

end Template;
