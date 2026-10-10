LIBRARY IEEE;
USE IEEE.STD_LOGIC_1164.ALL;
USE IEEE.NUMERIC_STD.ALL;
USE IEEE.STD_LOGIC_MISC.ALL;

LIBRARY EE_212_DECODER;
USE EE_212_DECODER.DECODELOGIC_PKG.ALL;

LIBRARY EE_212_ALU;
USE EE_212_ALU.ALU_PKG.ALL;

LIBRARY EE_212_MEMORY;
USE EE_212_MEMORY.MEMORY_PKG.ALL;

LIBRARY EE_212_MISC;
USE EE_212_MISC.MISC_PKG.ALL;

LIBRARY EE_212_NIAG;
USE EE_212_NIAG.NIAG_PKG.ALL;

LIBRARY EE_212_CPU;
USE EE_212_CPU.LABCPU_PKG.ALL;

LIBRARY EE_212_RegFile;
USE EE_212_RegFile.RegFile_PKG.ALL;


Entity CPU is
	port (Clk: in std_logic);
end;

Architecture behavioral of CPU is
	SIGNAL IR    			  : STD_LOGIC_VECTOR(31 DOWNTO 0);
	SIGNAL PC    			  : STD_LOGIC_VECTOR(31 DOWNTO 0):= x"00000000";
	SIGNAL CtrlSgnls    	  : CTRL_SIGNL_REC;
	SIGNAL NIAGout    	  : STD_LOGIC_VECTOR(31 DOWNTO 0);
	SIGNAL XtndrOut    	  : STD_LOGIC_VECTOR(31 DOWNTO 0);
	SIGNAL Rtype    		  : R_INSTRUCTION;
	SIGNAL Jtype    		  : J_INSTRUCTION;
	SIGNAL Itype    		  : I_INSTRUCTION;
	SIGNAL RTNadrs    	  : STD_LOGIC_VECTOR(31 DOWNTO 0);
	SIGNAL DselMUXout      : STD_LOGIC_VECTOR(4 DOWNTO 0);
	SIGNAL ALUinMUXout     : STD_LOGIC_VECTOR(31 DOWNTO 0);
	SIGNAL DinMUXout    	  : STD_LOGIC_VECTOR(31 DOWNTO 0);
	SIGNAL RegFileAout     : STD_LOGIC_VECTOR(31 DOWNTO 0);
	SIGNAL RegFileBout     : STD_LOGIC_VECTOR(31 DOWNTO 0);
	SIGNAL ALUout   		  : STD_LOGIC_VECTOR(31 DOWNTO 0);
	SIGNAL ALUsftMUXout    : STD_LOGIC_VECTOR(4 DOWNTO 0);
	SIGNAL ALUstatCodes    : STAT_SIGNL_REC;
	SIGNAL DataMemData     : STD_LOGIC_VECTOR(31 DOWNTO 0);
	
BEGIN
	RTYPE <= IR_TO_RTYPE(IR);
	ITYPE <= IR_TO_ITYPE(IR);
	JTYPE <= IR_TO_JTYPE(IR);
	
		process (Clk) is
		begin
        if rising_edge(CLK) then
                PC <= NIAGout;
			end if;
		end process;
		
		Decoder_PM		: Decoder    PORT MAP(IR, CtrlSgnls);
		RegFile_PM     : RegFile   PORT MAP(RTYPE.R_RT, RTYPE.R_RS, DselMUXout, DinMUXout, CtrlSgnls.RF_STRB, RegFileAout, RegFileBout, Clk);
		NIAG_PM        : NIAG      PORT MAP(JTYPE.J_INDEX, XtndrOut, RegFileBout, CtrlSgnls.IR_XLSFT, PC, CtrlSgnls.NIAG_COND, CtrlSgnls.NIAG_SEL, ALUstatCodes, NIAGout, RTNadrs);
		ALU_PM			: ALU			PORT MAP(ALUinMUXout, RegFileBout, CtrlSgnls.ALU_FUNC, ALUsftMUXout, ALUout, ALUstatCodes);
		ROM_PM			: ROM			PORT MAP(PC, IR);
		RAM_PM			: RAM			PORT MAP(ALUout, CtrlSgnls.DM_STRB, CtrlSgnls.DM_rw, CtrlSgnls.DM_en, Clk, DataMemData);
		ALUinMUX_PM    : ALUinMUX  PORT MAP(RegFileAout, XtndrOut, CtrlSgnls.ALU_ASEL, ALUinMUXout);
		ImmedXtnd_PM   : ImmedXtnd PORT MAP(ITYPE.I_IMMED, CtrlSgnls.IR_XSEL, XtndrOut);
		DselMUX_PM     : DselMUX   PORT MAP(RTYPE.R_RD, RTYPE.R_RT, "11111", CtrlSgnls.RF_WSEL, DselMUXout);
		DinMUX_PM		: DinMUX    PORT MAP(ALUout, DataMemData, RTNadrs, CtrlSgnls.RF_DSEL, DinMUXout);
		ALUsftMUX_PM   : ALUsftMUX PORT MAP(RTYPE.R_SA, RegFileBout(4 Downto 0), CtrlSgnls.ALU_SSEL, ALUsftMUXout);
		TriBuffer_PM   : TriBuffer PORT MAP(CtrlSgnls.RF_OE, RegFileAout, DataMemData);

END ARCHITECTURE; 