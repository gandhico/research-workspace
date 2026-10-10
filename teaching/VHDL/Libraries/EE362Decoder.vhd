--------------------------------------------------------------------------------------
--    Library:	EE_362_Decoder
--
--       File:	EE_362_Decoder.vhd
--	
--    Project:	LabCPU
--
--     Author:	A.K. Petersen
--
--    Purpose: define constants and components for the Instruction Decode Logic
--
--  Copyright 2021 by A.K. Petersen, New Mexico State University, all rights reserved
--
-------------------------------------------------------------------------------------

library IEEE;
use IEEE.STD_LOGIC_1164.ALL;

library EE_362_ALU;
use EE_362_ALU.ALU_Pkg.all;

PACKAGE DecodeLogic_Pkg IS
																											-- special opcodes:
	CONSTANT	CPU_OPCODE_SPECIAL		:			STD_LOGIC_VECTOR(5 DOWNTO 0) 	:= "000000";			--   R-type format
	CONSTANT	CPU_OPCODE_SPECIAL2		:			STD_LOGIC_VECTOR(5 DOWNTO 0) 	:= "011100";			--   Multiply
	CONSTANT	CPU_OPCODE_REGIMM		:			STD_LOGIC_VECTOR(5 DOWNTO 0) 	:= "000001";			--   Branch
																									
																											-- instruction opcodes
																											--	 add signed word
	CONSTANT	CPU_ADD_OPCODE			:			STD_LOGIC_VECTOR(5 DOWNTO 0) 	:= CPU_OPCODE_SPECIAL;	--     IR opcode value
	CONSTANT	CPU_ADD_FUNC			:			STD_LOGIC_VECTOR(5 DOWNTO 0) 	:= "100000";			--	   IR func value

	CONSTANT	CPU_ADDI_OPCODE			:			STD_LOGIC_VECTOR(5 DOWNTO 0) 	:= "001000";			--	 add immed signed word


	CONSTANT	CPU_ADDU_OPCODE			:			STD_LOGIC_VECTOR(5 DOWNTO 0) 	:= CPU_OPCODE_SPECIAL;	--	 add unnsigned word
	CONSTANT	CPU_ADDU_FUNC			:			STD_LOGIC_VECTOR(5 DOWNTO 0) 	:= "100001";
	
	CONSTANT	CPU_ADDIU_OPCODE		:			STD_LOGIC_VECTOR(5 DOWNTO 0) 	:= "001001";			--	 add immed unnsigned word
	
	CONSTANT	CPU_AND_OPCODE			:			STD_LOGIC_VECTOR(5 DOWNTO 0) 	:= CPU_OPCODE_SPECIAL;	--	 and word
	CONSTANT	CPU_AND_FUNC			:			STD_LOGIC_VECTOR(5 DOWNTO 0) 	:= "100100";

	CONSTANT	CPU_ANDI_OPCODE			:			STD_LOGIC_VECTOR(5 DOWNTO 0) 	:= "001100";			--	 and immediate word

	CONSTANT	CPU_BEQ_OPCODE			:			STD_LOGIC_VECTOR(5 DOWNTO 0) 	:= "000100";			--	 branch on =

	CONSTANT	CPU_BGEZ_OPCODE			:			STD_LOGIC_VECTOR(5 DOWNTO 0) 	:= CPU_OPCODE_REGIMM;	--	 branch on >=0
	CONSTANT	CPU_BGEZ_RT				:			STD_LOGIC_VECTOR(4 DOWNTO 0) 	:= "00001";

	CONSTANT	CPU_BGEZAL_OPCODE		:			STD_LOGIC_VECTOR(5 DOWNTO 0) 	:= CPU_OPCODE_REGIMM;	--	 branch & link on >=0
	CONSTANT	CPU_BGEZAL_RT			:			STD_LOGIC_VECTOR(4 DOWNTO 0) 	:= "10001";

	CONSTANT	CPU_BGTZ_OPCODE			:			STD_LOGIC_VECTOR(5 DOWNTO 0) 	:= "000111";			--	 branch on >0

	CONSTANT	CPU_BLEZ_OPCODE			:			STD_LOGIC_VECTOR(5 DOWNTO 0) 	:= "000110";			--	 branch on <=0

	CONSTANT	CPU_BLTZ_OPCODE			:			STD_LOGIC_VECTOR(5 DOWNTO 0) 	:= CPU_OPCODE_REGIMM;	--	 branch on <0
	CONSTANT	CPU_BLTZ_RT				:			STD_LOGIC_VECTOR(4 DOWNTO 0) 	:= "00000";

	CONSTANT	CPU_BLTZAL_OPCODE		:			STD_LOGIC_VECTOR(5 DOWNTO 0) 	:= CPU_OPCODE_REGIMM;	--	 branch & link on <0
	CONSTANT	CPU_BLTZAL_RT			:			STD_LOGIC_VECTOR(4 DOWNTO 0) 	:= "10000";

	CONSTANT	CPU_BNE_OPCODE			:			STD_LOGIC_VECTOR(5 DOWNTO 0) 	:= "000101";			--	 branch on !=
	CONSTANT	CPU_BNE_RT				:			STD_LOGIC_VECTOR(4 DOWNTO 0) 	:= "-----";

	CONSTANT	CPU_DIV_OPCODE			:			STD_LOGIC_VECTOR(5 DOWNTO 0) 	:= CPU_OPCODE_SPECIAL;	--	 divide +/- word
	CONSTANT	CPU_DIV_FUNC			:			STD_LOGIC_VECTOR(5 DOWNTO 0) 	:= "011010";

	CONSTANT	CPU_DIVU_OPCODE			:			STD_LOGIC_VECTOR(5 DOWNTO 0) 	:= CPU_OPCODE_SPECIAL;	--  divide un+/- word
	CONSTANT	CPU_DIVU_FUNC			:			STD_LOGIC_VECTOR(5 DOWNTO 0) 	:= "011011";

	CONSTANT	CPU_J_OPCODE			:			STD_LOGIC_VECTOR(5 DOWNTO 0) 	:= "000010";			--  jump

	CONSTANT	CPU_JAL_OPCODE			:			STD_LOGIC_VECTOR(5 DOWNTO 0) 	:= "000011";			--  jump and link

	CONSTANT	CPU_JALR_OPCODE			:			STD_LOGIC_VECTOR(5 DOWNTO 0) 	:= CPU_OPCODE_SPECIAL;	--  jump & link register
	CONSTANT	CPU_JALR_FUNC			:			STD_LOGIC_VECTOR(5 DOWNTO 0) 	:= "001001";

	CONSTANT	CPU_JR_OPCODE			:			STD_LOGIC_VECTOR(5 DOWNTO 0) 	:= CPU_OPCODE_SPECIAL;	--  jump register
	CONSTANT	CPU_JR_FUNC				:			STD_LOGIC_VECTOR(5 DOWNTO 0) 	:= "001000";

	CONSTANT	CPU_LB_OPCODE			:			STD_LOGIC_VECTOR(5 DOWNTO 0) 	:= "100000";			--  load +/- byte

	CONSTANT	CPU_LBU_OPCODE			:			STD_LOGIC_VECTOR(5 DOWNTO 0) 	:= "100100";			--  load + byte

	CONSTANT	CPU_LH_OPCODE			:			STD_LOGIC_VECTOR(5 DOWNTO 0) 	:= "100001";			--  load +/- half word

	CONSTANT	CPU_LHU_OPCODE			:			STD_LOGIC_VECTOR(5 DOWNTO 0) 	:= "100101";			--  load + half word

	CONSTANT	CPU_LUI_OPCODE			:			STD_LOGIC_VECTOR(5 DOWNTO 0) 	:= "001111";			--  load upper immediate

	CONSTANT	CPU_LW_OPCODE			:			STD_LOGIC_VECTOR(5 DOWNTO 0) 	:= "100011";			--  load word


	CONSTANT	CPU_MFHI_OPCODE			:			STD_LOGIC_VECTOR(5 DOWNTO 0) 	:= CPU_OPCODE_SPECIAL;	--  move from HI
	CONSTANT	CPU_MFHI_FUNC			:			STD_LOGIC_VECTOR(5 DOWNTO 0) 	:= "010000";

	CONSTANT	CPU_MFLO_OPCODE			:			STD_LOGIC_VECTOR(5 DOWNTO 0) 	:= CPU_OPCODE_SPECIAL;	--  move from LO
	CONSTANT	CPU_MFLO_FUNC			:			STD_LOGIC_VECTOR(5 DOWNTO 0) 	:= "010010";

	CONSTANT	CPU_MTHI_OPCODE			:			STD_LOGIC_VECTOR(5 DOWNTO 0) 	:= CPU_OPCODE_SPECIAL;	--  move to HI
	CONSTANT	CPU_MTHI_FUNC			:			STD_LOGIC_VECTOR(5 DOWNTO 0) 	:= "010001";

	CONSTANT	CPU_MTLO_OPCODE			:			STD_LOGIC_VECTOR(5 DOWNTO 0) 	:= CPU_OPCODE_SPECIAL;	--  move to LO
	CONSTANT	CPU_MTLO_FUNC			:			STD_LOGIC_VECTOR(5 DOWNTO 0) 	:= "010011";

	CONSTANT	CPU_MUL_OPCODE			:			STD_LOGIC_VECTOR(5 DOWNTO 0) 	:= CPU_OPCODE_SPECIAL2;	--  multiply half word
	CONSTANT	CPU_MUL_FUNC			:			STD_LOGIC_VECTOR(5 DOWNTO 0) 	:= "000010";

	CONSTANT	CPU_MULT_OPCODE			:			STD_LOGIC_VECTOR(5 DOWNTO 0) 	:= CPU_OPCODE_SPECIAL;	--  multiply +/- word
	CONSTANT	CPU_MULT_FUNC			:			STD_LOGIC_VECTOR(5 DOWNTO 0) 	:= "011000";

	CONSTANT	CPU_MULTU_OPCODE		:			STD_LOGIC_VECTOR(5 DOWNTO 0) 	:= CPU_OPCODE_SPECIAL;	--  multipy + word
	CONSTANT	CPU_MULTU_FUNC			:			STD_LOGIC_VECTOR(5 DOWNTO 0) 	:= "011001";
	
	CONSTANT	CPU_NOR_OPCODE			:			STD_LOGIC_VECTOR(5 DOWNTO 0) 	:= CPU_OPCODE_SPECIAL;	--  nor word
	CONSTANT	CPU_NOR_FUNC			:			STD_LOGIC_VECTOR(5 DOWNTO 0) 	:= "100111";

	CONSTANT	CPU_OR_OPCODE			:			STD_LOGIC_VECTOR(5 DOWNTO 0) 	:= CPU_OPCODE_SPECIAL;	--  or word
	CONSTANT	CPU_OR_FUNC				:			STD_LOGIC_VECTOR(5 DOWNTO 0) 	:= "100101";

	CONSTANT	CPU_ORI_OPCODE			:			STD_LOGIC_VECTOR(5 DOWNTO 0) 	:= "001101";			--  or immediate word

	CONSTANT	CPU_SB_OPCODE			:			STD_LOGIC_VECTOR(5 DOWNTO 0) 	:= "101000";			--  store byte

	CONSTANT	CPU_SH_OPCODE			:			STD_LOGIC_VECTOR(5 DOWNTO 0) 	:= "101001";			--  store half word

	CONSTANT	CPU_SLA_OPCODE			:			STD_LOGIC_VECTOR(5 DOWNTO 0) 	:= CPU_OPCODE_SPECIAL;	--  shift left +/-
	CONSTANT	CPU_SLA_FUNC			:			STD_LOGIC_VECTOR(5 DOWNTO 0) 	:= "000001";

	CONSTANT	CPU_SLAV_OPCODE			:			STD_LOGIC_VECTOR(5 DOWNTO 0) 	:= CPU_OPCODE_SPECIAL;	--  variable SLA
	CONSTANT	CPU_SLAV_FUNC			:			STD_LOGIC_VECTOR(5 DOWNTO 0) 	:= "000101";

	CONSTANT	CPU_SLL_OPCODE			:			STD_LOGIC_VECTOR(5 DOWNTO 0) 	:= CPU_OPCODE_SPECIAL;	--  shift left logical
	CONSTANT	CPU_SLL_FUNC			:			STD_LOGIC_VECTOR(5 DOWNTO 0) 	:= "000000";

	CONSTANT	CPU_SLLV_OPCODE			:			STD_LOGIC_VECTOR(5 DOWNTO 0) 	:= CPU_OPCODE_SPECIAL;	--  variable SLL
	CONSTANT	CPU_SLLV_FUNC			:			STD_LOGIC_VECTOR(5 DOWNTO 0) 	:= "000100";

	CONSTANT	CPU_SLT_OPCODE			:			STD_LOGIC_VECTOR(5 DOWNTO 0) 	:= CPU_OPCODE_SPECIAL;	--  set on < (+/-)
	CONSTANT	CPU_SLT_FUNC			:			STD_LOGIC_VECTOR(5 DOWNTO 0) 	:= "101010";

	CONSTANT	CPU_SLTI_OPCODE			:			STD_LOGIC_VECTOR(5 DOWNTO 0) 	:= "001010";			--  set on < immed (+/-)

	CONSTANT	CPU_SLTIU_OPCODE		:			STD_LOGIC_VECTOR(5 DOWNTO 0) 	:= "001011";			--  set on < immed (+)

	CONSTANT	CPU_SLTU_OPCODE			:			STD_LOGIC_VECTOR(5 DOWNTO 0) 	:= CPU_OPCODE_SPECIAL;	--  set on < (+)
	CONSTANT	CPU_SLTU_FUNC			:			STD_LOGIC_VECTOR(5 DOWNTO 0) 	:= "101011";

	CONSTANT	CPU_SRA_OPCODE			:			STD_LOGIC_VECTOR(5 DOWNTO 0) 	:= CPU_OPCODE_SPECIAL;	--  shift right +/-
	CONSTANT	CPU_SRA_FUNC			:			STD_LOGIC_VECTOR(5 DOWNTO 0) 	:= "000011";

	CONSTANT	CPU_SRAV_OPCODE			:			STD_LOGIC_VECTOR(5 DOWNTO 0) 	:= CPU_OPCODE_SPECIAL;	--  variable SRA
	CONSTANT	CPU_SRAV_FUNC			:			STD_LOGIC_VECTOR(5 DOWNTO 0) 	:= "000111";

	CONSTANT	CPU_SRL_OPCODE			:			STD_LOGIC_VECTOR(5 DOWNTO 0) 	:= CPU_OPCODE_SPECIAL;	--  shift right logical
	CONSTANT	CPU_SRL_FUNC			:			STD_LOGIC_VECTOR(5 DOWNTO 0) 	:= "000010";

	CONSTANT	CPU_SRLV_OPCODE			:			STD_LOGIC_VECTOR(5 DOWNTO 0) 	:= CPU_OPCODE_SPECIAL;	--  variable SRL
	CONSTANT	CPU_SRLV_FUNC			:			STD_LOGIC_VECTOR(5 DOWNTO 0) 	:= "000110";

	CONSTANT	CPU_SUB_OPCODE			:			STD_LOGIC_VECTOR(5 DOWNTO 0) 	:= CPU_OPCODE_SPECIAL;	--  subtract +/- word
	CONSTANT	CPU_SUB_FUNC			:			STD_LOGIC_VECTOR(5 DOWNTO 0) 	:= "100010";

	CONSTANT	CPU_SUBU_OPCODE			:			STD_LOGIC_VECTOR(5 DOWNTO 0) 	:= CPU_OPCODE_SPECIAL;	--  subtract + word
	CONSTANT	CPU_SUBU_FUNC			:			STD_LOGIC_VECTOR(5 DOWNTO 0) 	:= "100011";

	CONSTANT	CPU_SW_OPCODE			:			STD_LOGIC_VECTOR(5 DOWNTO 0) 	:= "101011";			--  store word

	CONSTANT	CPU_XOR_OPCODE			:			STD_LOGIC_VECTOR(5 DOWNTO 0) 	:= CPU_OPCODE_SPECIAL;	--  xor word
	CONSTANT	CPU_XOR_FUNC			:			STD_LOGIC_VECTOR(5 DOWNTO 0) 	:= "100110";

	CONSTANT	CPU_XORI_OPCODE			:			STD_LOGIC_VECTOR(5 DOWNTO 0) 	:= "001110";			--  XOR immediate word
	
																											--  Control Signals:
																											--   ALU:
																											--    A input select:
	CONSTANT	ALU_ASEL_FLOAT			:			STD_LOGIC						:= 'Z';					--     float
	CONSTANT	ALU_ASEL_AOUT			:			STD_LOGIC						:= '0';					--     RF A output
	CONSTANT	ALU_ASEL_IMMED			:			STD_LOGIC						:= '1';					--     IR immediate
	
																											--    Shift source:
	CONSTANT	ALU_SSEL_FLOAT			:			STD_LOGIC						:= 'Z';					--     float
	CONSTANT	ALU_SSEL_RS				:			STD_LOGIC						:= '0';					--     IR shift
	CONSTANT	ALU_SSEL_BOUT			:			STD_LOGIC						:= '1';					--     RF B output
	
																											--   Data Memory:
																											--    Strobe values:
	CONSTANT	DM_STRB_FLOAT			:			STD_LOGIC						:= 'Z';					--     float
	CONSTANT	DM_STRB_HOLD			:			STD_LOGIC						:= '0';					--     hold data
	CONSTANT	DM_STRB_STORE			:			STD_LOGIC						:= '1';					--     store data
	
																											--   Read/write values:
	CONSTANT	DM_RW_FLOAT				:			STD_LOGIC						:= 'Z';					--    float
	CONSTANT	DM_RW_WR				:			STD_LOGIC						:= '0';					--    write
	CONSTANT	DM_RW_RD				:			STD_LOGIC						:= '1';					--    read
	
																											--   Output enable:
	CONSTANT	DM_EN_FLOAT				:			STD_LOGIC						:= 'Z';					--    float
	CONSTANT	DM_EN_DISABLE			:			STD_LOGIC						:= '0';					--   	disable
	CONSTANT	DM_EN_ENABLE			:			STD_LOGIC						:= '1';					--    enable
	
																											--  Next instruction:
																											--   selection values:
	CONSTANT	NIAG_SEL_FLOAT			:			STD_LOGIC_VECTOR(1 DOWNTO 0)	:= "ZZ";				--    float
	CONSTANT	NIAG_SEL_NSA			:			STD_LOGIC_VECTOR(1 DOWNTO 0)	:= "00";				--    Sequential
	CONSTANT	NIAG_SEL_REL			:			STD_LOGIC_VECTOR(1 DOWNTO 0)	:= "01";				--    Relative
	CONSTANT	NIAG_SEL_REG			:			STD_LOGIC_VECTOR(1 DOWNTO 0)	:= "10";				--    Register
	CONSTANT	NIAG_SEL_ABS			:			STD_LOGIC_VECTOR(1 DOWNTO 0)	:= "11";				--    Absolute

																											--   PC strobe values:
	CONSTANT	NIAG_STRB_FLOAT			:			STD_LOGIC						:= 'Z';					--    float
	CONSTANT	NIAG_STRB_HOLD			:			STD_LOGIC						:= '0';					--    don't load
	CONSTANT	NIAG_STRB_STROBE		:			STD_LOGIC						:= '1';					--    load
	
																											--   condition values:
	CONSTANT	NIAG_COND_FLOAT			:			STD_LOGIC_VECTOR(2 DOWNTO 0)	:= "ZZZ";				--    float
	CONSTANT	NIAG_COND_NONE			:			STD_LOGIC_VECTOR(2 DOWNTO 0)	:= "000";				--    Unconditional
	CONSTANT	NIAG_COND_EQ			:			STD_LOGIC_VECTOR(2 DOWNTO 0)	:= "001";				--    rs  = rt
	CONSTANT	NIAG_COND_NEQ			:			STD_LOGIC_VECTOR(2 DOWNTO 0)	:= "010";				--    rs != rt
	CONSTANT	NIAG_COND_GTZ			:			STD_LOGIC_VECTOR(2 DOWNTO 0)	:= "011";				--    rs >  0	
	CONSTANT	NIAG_COND_GEZ			:			STD_LOGIC_VECTOR(2 DOWNTO 0)	:= "100";				--    rs >= 0
	CONSTANT	NIAG_COND_LTZ			:			STD_LOGIC_VECTOR(2 DOWNTO 0)	:= "101";				--    rs <  0
	CONSTANT	NIAG_COND_LEZ			:			STD_LOGIC_VECTOR(2 DOWNTO 0)	:= "110";				--    rs <= 0

																											--  Instruction reg:
																											--   strobe values:
	CONSTANT	IR_STRB_FLOAT			:			STD_LOGIC						:= 'Z';					--    float
	CONSTANT	IR_STRB_HOLD			:			STD_LOGIC						:= '0';					--    don't load
	CONSTANT	IR_STRB_STROBE			:			STD_LOGIC						:= '1';					--    load

																											--  extension methods:
	CONSTANT	IR_XSEL_FLOAT			:			STD_LOGIC						:= 'Z';					--   float
	CONSTANT	IR_XSEL_ZERO			:			STD_LOGIC						:= '0';					--   zero pad
	CONSTANT	IR_XSEL_SIGN			:			STD_LOGIC						:= '1';					--   sign extend
	
																											--   shift methods:
	CONSTANT	IR_XLSFT_FLOAT			:			STD_LOGIC						:= 'Z';					--    float
	CONSTANT	IR_XLSFT_NONE			:			STD_LOGIC						:= '0';					--    don't shift
	CONSTANT	IR_XLSFT_TWO			:			STD_LOGIC						:= '1';					--    shift left 2
	
																											--  Register file:
																											--   data in source:
	CONSTANT	RF_DSEL_FLOAT			:			STD_LOGIC_VECTOR(1 DOWNTO 0)	:= "ZZ";				--    float
	CONSTANT	RF_DSEL_ALU				:			STD_LOGIC_VECTOR(1 DOWNTO 0)	:= "00";				--    ALU result bus
	CONSTANT	RF_DSEL_MEM				:			STD_LOGIC_VECTOR(1 DOWNTO 0)	:= "01";				--    memory data bus
	CONSTANT	RF_DSEL_RET				:			STD_LOGIC_VECTOR(1 DOWNTO 0)	:= "10";				--    return address
	
																											--   strobe values:
	CONSTANT	RF_STRB_FLOAT			:			STD_LOGIC						:= 'Z';					--    float
	CONSTANT	RF_STRB_HOLD			:			STD_LOGIC						:= '0';					--    don't strobe
	CONSTANT	RF_STRB_STROBE			:			STD_LOGIC						:= '1';					--    strobe

																											--   destination source:
	CONSTANT	RF_WSEL_FLOAT			:			STD_LOGIC_VECTOR(1 DOWNTO 0)	:= "ZZ";				--    float
	CONSTANT	RF_WSEL_RD				:			STD_LOGIC_VECTOR(1 DOWNTO 0)	:= "00";				--    IR reg RD field
	CONSTANT	RF_WSEL_RT				:			STD_LOGIC_VECTOR(1 DOWNTO 0)	:= "01";				--    IR reg RT field
	CONSTANT	RF_WSEL_RET				:			STD_LOGIC_VECTOR(1 DOWNTO 0)	:= "10";				--    return address
																								 
																											--   output enable:
	CONSTANT	RF_OE_FLOAT				:			STD_LOGIC						:= 'Z';					--    float
	CONSTANT	RF_OE_HiZ				:			STD_LOGIC						:= '0';					--    disable output
	CONSTANT	RF_OE_DRIVE				:			STD_LOGIC						:= '1';					--    enable output
																									
																											--   register labels:
	CONSTANT	RF_REG_00				:			STD_LOGIC_VECTOR(4 DOWNTO 0)	:= "00000";				--    00
	CONSTANT	RF_REG_01				:			STD_LOGIC_VECTOR(4 DOWNTO 0)	:= "00001";				--    01
	CONSTANT	RF_REG_02				:			STD_LOGIC_VECTOR(4 DOWNTO 0)	:= "00010";				--    02
	CONSTANT	RF_REG_03				:			STD_LOGIC_VECTOR(4 DOWNTO 0)	:= "00011";				--    03
	CONSTANT	RF_REG_04				:			STD_LOGIC_VECTOR(4 DOWNTO 0)	:= "00100";				--    04
	CONSTANT	RF_REG_05				:			STD_LOGIC_VECTOR(4 DOWNTO 0)	:= "00101";				--    05
	CONSTANT	RF_REG_06				:			STD_LOGIC_VECTOR(4 DOWNTO 0)	:= "00110";				--    06
	CONSTANT	RF_REG_07				:			STD_LOGIC_VECTOR(4 DOWNTO 0)	:= "00111";				--    07
	CONSTANT	RF_REG_08				:			STD_LOGIC_VECTOR(4 DOWNTO 0)	:= "01000";				--    08
	CONSTANT	RF_REG_09				:			STD_LOGIC_VECTOR(4 DOWNTO 0)	:= "01001";				--    09
	CONSTANT	RF_REG_0A				:			STD_LOGIC_VECTOR(4 DOWNTO 0)	:= "01010";				--    0A
	CONSTANT	RF_REG_0B				:			STD_LOGIC_VECTOR(4 DOWNTO 0)	:= "01011";				--    0B
	CONSTANT	RF_REG_0C				:			STD_LOGIC_VECTOR(4 DOWNTO 0)	:= "01100";				--    0C
	CONSTANT	RF_REG_0D				:			STD_LOGIC_VECTOR(4 DOWNTO 0)	:= "01101";				--    0D
	CONSTANT	RF_REG_0E				:			STD_LOGIC_VECTOR(4 DOWNTO 0)	:= "01110";				--    0E
	CONSTANT	RF_REG_0F				:			STD_LOGIC_VECTOR(4 DOWNTO 0)	:= "01111";				--    0F
	CONSTANT	RF_REG_10				:			STD_LOGIC_VECTOR(4 DOWNTO 0)	:= "10000";				--    10
	CONSTANT	RF_REG_11				:			STD_LOGIC_VECTOR(4 DOWNTO 0)	:= "10001";				--    11
	CONSTANT	RF_REG_12				:			STD_LOGIC_VECTOR(4 DOWNTO 0)	:= "10010";				--    12
	CONSTANT	RF_REG_13				:			STD_LOGIC_VECTOR(4 DOWNTO 0)	:= "10011";				--    13
	CONSTANT	RF_REG_14				:			STD_LOGIC_VECTOR(4 DOWNTO 0)	:= "10100";				--    14
	CONSTANT	RF_REG_15				:			STD_LOGIC_VECTOR(4 DOWNTO 0)	:= "10101";				--    15
	CONSTANT	RF_REG_16				:			STD_LOGIC_VECTOR(4 DOWNTO 0)	:= "10110";				--    16
	CONSTANT	RF_REG_17				:			STD_LOGIC_VECTOR(4 DOWNTO 0)	:= "10111";				--    17
	CONSTANT	RF_REG_18				:			STD_LOGIC_VECTOR(4 DOWNTO 0)	:= "11000";				--    18
	CONSTANT	RF_REG_19				:			STD_LOGIC_VECTOR(4 DOWNTO 0)	:= "11001";				--    19
	CONSTANT	RF_REG_1A				:			STD_LOGIC_VECTOR(4 DOWNTO 0)	:= "11010";				--    1A
	CONSTANT	RF_REG_1B				:			STD_LOGIC_VECTOR(4 DOWNTO 0)	:= "11011";				--    1B
	CONSTANT	RF_REG_1C				:			STD_LOGIC_VECTOR(4 DOWNTO 0)	:= "11100";				--    1C
	CONSTANT	RF_REG_1D				:			STD_LOGIC_VECTOR(4 DOWNTO 0)	:= "11101";				--    1D
	CONSTANT	RF_REG_1E				:			STD_LOGIC_VECTOR(4 DOWNTO 0)	:= "11110";				--    1E
	CONSTANT	RF_REG_1F				:			STD_LOGIC_VECTOR(4 DOWNTO 0)	:= "11111";				--    1F

																											--   Misc constants:
	CONSTANT	VAL_32_ZERO				:			STD_LOGIC_VECTOR(31 DOWNTO 0)	:= (Others => '0');		--    32-bit zero
	CONSTANT	VAL_32_FLOAT			:			STD_LOGIC_VECTOR(31 DOWNTO 0)	:= (Others => 'Z');		--    32-bit float
	CONSTANT	VAL_5_FLOAT				:			STD_LOGIC_VECTOR(4  DOWNTO 0)	:= (Others => 'Z');		--    5-bit float

	TYPE CTRL_SIGNL_REC is record																			-- Control signals
				ALU_func				:			STD_LOGIC_VECTOR(4 DOWNTO 0);			  				--  ALU function code
				ALU_Asel				:			STD_LOGIC;												--  ALU A inputsourceselect                
				ALU_Ssel				:			STD_LOGIC;												--  ALU shift amount source                
				DM_strb					:			STD_LOGIC;												--  Data memory data strobe
				DM_rw					:			STD_LOGIC;												--  Data memory read/write                
				IR_Xsel					:			STD_LOGIC;									  			--  IR immediate field extend method select
				IR_Xlsft				:			STD_LOGIC;									  			--  IR immediate field left shift method
				IR_strb					:			STD_LOGIC;												--  Instruction Register strobe
				NIAG_sel				:			STD_LOGIC_VECTOR(1 DOWNTO 0);			  				--  Program counter select
				NIAG_strb				:			STD_LOGIC;												--  Program counter strobe
				DM_en					:			STD_LOGIC;												--  Data memory enable
				NIAG_cond				:			STD_LOGIC_VECTOR(2 DOWNTO 0);							--  Program counter condition
				RF_Dsel					:			STD_LOGIC_VECTOR(1 DOWNTO 0);							--  Register file data input select
				RF_strb					:			STD_LOGIC;												--  Register file strobe
				RF_Wsel					:			STD_LOGIC_VECTOR(1 DOWNTO 0);							--  Register file write destination select
				RF_oe					:			STD_LOGIC;												--  Register file output enable
	END RECORD;  
 
																									
	TYPE R_INSTRUCTION is record																			--  R-type instruction format
				R_OPCODE				:			STD_LOGIC_VECTOR(5 DOWNTO 0);						    --   opcode
				R_RS					:			STD_LOGIC_VECTOR(4 DOWNTO 0);							--   rs field (source 0)                
				R_RT					:			STD_LOGIC_VECTOR(4 DOWNTO 0);							--   rt field (source 1)
				R_RD					:			STD_LOGIC_VECTOR(4 DOWNTO 0);							--   rd field (destination)
				R_SA					:			STD_LOGIC_VECTOR(4 DOWNTO 0);							--   sa field (shift)                
				R_FUNC					:			STD_LOGIC_VECTOR(5 DOWNTO 0);							--   func field (aux opcode)
	END RECORD;  
																									
	TYPE I_INSTRUCTION is record																			--  I-type instruction format
				I_OPCODE				:			STD_LOGIC_VECTOR(5 DOWNTO 0);					   		--   opcode
				I_RS					:			STD_LOGIC_VECTOR(4 DOWNTO 0);							--   rs field (source 0)                
				I_RT					:			STD_LOGIC_VECTOR(4 DOWNTO 0);							--   rt field (source 1)
				I_IMMED					:			STD_LOGIC_VECTOR(15 DOWNTO 0);							--   IMMED field (immediate)
	END RECORD;  																									

	TYPE J_INSTRUCTION is record																			--  J-typeinstruction format
				J_OPCODE				:			STD_LOGIC_VECTOR(5 DOWNTO 0);							--   opcode
				J_INDEX					:			STD_LOGIC_VECTOR(25 DOWNTO 0);							--   index field (addrress)                
	END RECORD;  
	
																											--    decoder body (calls the instructions)
	COMPONENT Decoder IS
		PORT(	Instruction				:	IN		STD_LOGIC_VECTOR(31 DOWNTO 0);
				CtrlSgnls				:	OUT		CTRL_SIGNL_REC);
	END COMPONENT;																							--    operation components
																											--    	ADD instruction
	COMPONENT Decode_ADD IS
		PORT(	Instruction				:	IN		STD_LOGIC_VECTOR(31 DOWNTO 0);
				CtrlSgnls				:	OUT		CTRL_SIGNL_REC);
	END COMPONENT;
																											--    	ADDI instruction
	COMPONENT Decode_ADDI IS
		PORT(	Instruction				:	IN		STD_LOGIC_VECTOR(31 DOWNTO 0);
				CtrlSgnls				:	OUT		CTRL_SIGNL_REC);
	END COMPONENT;
																											--    	ADDIU instruction
	COMPONENT Decode_ADDIU IS
		PORT(	Instruction				:	IN		STD_LOGIC_VECTOR(31 DOWNTO 0);
				CtrlSgnls				:	OUT		CTRL_SIGNL_REC);
	END COMPONENT;
																											--    	ADDU instruction
	COMPONENT Decode_ADDU IS
		PORT(	Instruction				:	IN		STD_LOGIC_VECTOR(31 DOWNTO 0);
				CtrlSgnls				:	OUT		CTRL_SIGNL_REC);
	END COMPONENT;
																											--    	AND instruction
	COMPONENT Decode_AND IS
		PORT(	Instruction				:	IN		STD_LOGIC_VECTOR(31 DOWNTO 0);
				CtrlSgnls				:	OUT		CTRL_SIGNL_REC);
	END COMPONENT;
																											--    	ANDI instruction
	COMPONENT Decode_ANDI IS
		PORT(	Instruction				:	IN		STD_LOGIC_VECTOR(31 DOWNTO 0);
				CtrlSgnls				:	OUT		CTRL_SIGNL_REC);
	END COMPONENT;
																											--    	BEQ instruction
	COMPONENT Decode_BEQ IS
		PORT(	Instruction				:	IN		STD_LOGIC_VECTOR(31 DOWNTO 0);
				CtrlSgnls				:	OUT		CTRL_SIGNL_REC);
	END COMPONENT;
																											--    	BGEZ instruction
	COMPONENT Decode_BGEZ IS
		PORT(	Instruction				:	IN		STD_LOGIC_VECTOR(31 DOWNTO 0);
				CtrlSgnls				:	OUT		CTRL_SIGNL_REC);
	END COMPONENT;
																											--    	BGEZAL instruction
	COMPONENT Decode_BGEZAL IS
		PORT(	Instruction				:	IN		STD_LOGIC_VECTOR(31 DOWNTO 0);
				CtrlSgnls				:	OUT		CTRL_SIGNL_REC);
	END COMPONENT;
																											--    	BGTZ instruction
	COMPONENT Decode_BGTZ IS
		PORT(	Instruction				:	IN		STD_LOGIC_VECTOR(31 DOWNTO 0);
				CtrlSgnls				:	OUT		CTRL_SIGNL_REC);
	END COMPONENT;
																											--    	BLEZ instruction
	COMPONENT Decode_BLEZ IS
		PORT(	Instruction				:	IN		STD_LOGIC_VECTOR(31 DOWNTO 0);
				CtrlSgnls				:	OUT		CTRL_SIGNL_REC);
	END COMPONENT;
																											--    	BLTZ instruction
	COMPONENT Decode_BLTZ IS
		PORT(	Instruction				:	IN		STD_LOGIC_VECTOR(31 DOWNTO 0);
				CtrlSgnls				:	OUT		CTRL_SIGNL_REC);
	END COMPONENT;
																											--    	BLTZAL instruction
	COMPONENT Decode_BLTZAL IS
		PORT(	Instruction				:	IN		STD_LOGIC_VECTOR(31 DOWNTO 0);
				CtrlSgnls				:	OUT		CTRL_SIGNL_REC);
	END COMPONENT;
																											--    	BNE instruction
	COMPONENT Decode_BNE IS
		PORT(	Instruction				:	IN		STD_LOGIC_VECTOR(31 DOWNTO 0);
				CtrlSgnls				:	OUT		CTRL_SIGNL_REC);
	END COMPONENT;
																											--    	DIV instruction
	COMPONENT Decode_DIV IS
		PORT(	Instruction				:	IN		STD_LOGIC_VECTOR(31 DOWNTO 0);
				CtrlSgnls				:	OUT		CTRL_SIGNL_REC);
	END COMPONENT;
																											--    	DIVU instruction
	COMPONENT Decode_DIVU IS
		PORT(	Instruction				:	IN		STD_LOGIC_VECTOR(31 DOWNTO 0);
				CtrlSgnls				:	OUT		CTRL_SIGNL_REC);
	END COMPONENT;
																											--    	J instruction
	COMPONENT Decode_J IS
		PORT(	Instruction				:	IN		STD_LOGIC_VECTOR(31 DOWNTO 0);
				CtrlSgnls				:	OUT		CTRL_SIGNL_REC);
	END COMPONENT;
																											--    	JAL instruction
	COMPONENT Decode_JAL IS
		PORT(	Instruction				:	IN		STD_LOGIC_VECTOR(31 DOWNTO 0);
				CtrlSgnls				:	OUT		CTRL_SIGNL_REC);
	END COMPONENT;
																											--    	JALR instruction
	COMPONENT Decode_JALR IS
		PORT(	Instruction				:	IN		STD_LOGIC_VECTOR(31 DOWNTO 0);
				CtrlSgnls				:	OUT		CTRL_SIGNL_REC);
	END COMPONENT;
																											--    	JR instruction
	COMPONENT Decode_JR IS
		PORT(	Instruction				:	IN		STD_LOGIC_VECTOR(31 DOWNTO 0);
				CtrlSgnls				:	OUT		CTRL_SIGNL_REC);
	END COMPONENT;
																											--    	LB instruction
	COMPONENT Decode_LB IS
		PORT(	Instruction				:	IN		STD_LOGIC_VECTOR(31 DOWNTO 0);
				CtrlSgnls				:	OUT		CTRL_SIGNL_REC);
	END COMPONENT;
																											--    	LBU instruction
	COMPONENT Decode_LBU IS
		PORT(	Instruction				:	IN		STD_LOGIC_VECTOR(31 DOWNTO 0);
				CtrlSgnls				:	OUT		CTRL_SIGNL_REC);
	END COMPONENT;
																											--    	LH instruction
	COMPONENT Decode_LH IS
		PORT(	Instruction				:	IN		STD_LOGIC_VECTOR(31 DOWNTO 0);
				CtrlSgnls				:	OUT		CTRL_SIGNL_REC);
	END COMPONENT;
																											--    	LHU instruction
	COMPONENT Decode_LHU IS
		PORT(	Instruction				:	IN		STD_LOGIC_VECTOR(31 DOWNTO 0);
				CtrlSgnls				:	OUT		CTRL_SIGNL_REC);
	END COMPONENT;
																											--    	LUI instruction
	COMPONENT Decode_LUI IS
		PORT(	Instruction				:	IN		STD_LOGIC_VECTOR(31 DOWNTO 0);
				CtrlSgnls				:	OUT		CTRL_SIGNL_REC);
	END COMPONENT;
																											--    	LW instruction
	COMPONENT Decode_LW IS
		PORT(	Instruction				:	IN		STD_LOGIC_VECTOR(31 DOWNTO 0);
				CtrlSgnls				:	OUT		CTRL_SIGNL_REC);
	END COMPONENT;
																											--    	LWL instruction
	COMPONENT Decode_MFHI IS
		PORT(	Instruction				:	IN		STD_LOGIC_VECTOR(31 DOWNTO 0);
				CtrlSgnls				:	OUT		CTRL_SIGNL_REC);
	END COMPONENT;
																											--    	MFLO instruction
	COMPONENT Decode_MFLO IS
		PORT(	Instruction				:	IN		STD_LOGIC_VECTOR(31 DOWNTO 0);
				CtrlSgnls				:	OUT		CTRL_SIGNL_REC);
	END COMPONENT;
																											--    	MOVN instruction
	COMPONENT Decode_MOVN IS
		PORT(	Instruction				:	IN		STD_LOGIC_VECTOR(31 DOWNTO 0);
				CtrlSgnls				:	OUT		CTRL_SIGNL_REC);
	END COMPONENT;
																											--    	MOVZ instruction
	COMPONENT Decode_MOVZ IS
		PORT(	Instruction				:	IN		STD_LOGIC_VECTOR(31 DOWNTO 0);
				CtrlSgnls				:	OUT		CTRL_SIGNL_REC);
	END COMPONENT;
																											--    	MSUB instruction
	COMPONENT Decode_MTHI IS
		PORT(	Instruction				:	IN		STD_LOGIC_VECTOR(31 DOWNTO 0);
				CtrlSgnls				:	OUT		CTRL_SIGNL_REC);
	END COMPONENT;
																											--    	MTLO instruction
	COMPONENT Decode_MTLO IS
		PORT(	Instruction				:	IN		STD_LOGIC_VECTOR(31 DOWNTO 0);
				CtrlSgnls				:	OUT		CTRL_SIGNL_REC);
	END COMPONENT;
																											--    	MUL instruction
	COMPONENT Decode_MUL IS
		PORT(	Instruction				:	IN		STD_LOGIC_VECTOR(31 DOWNTO 0);
				CtrlSgnls				:	OUT		CTRL_SIGNL_REC);
	END COMPONENT;
																											--    	MULT instruction
	COMPONENT Decode_MULT IS
		PORT(	Instruction				:	IN		STD_LOGIC_VECTOR(31 DOWNTO 0);
				CtrlSgnls				:	OUT		CTRL_SIGNL_REC);
	END COMPONENT;
																											--    	MULTU instruction
	COMPONENT Decode_MULTU IS
		PORT(	Instruction				:	IN		STD_LOGIC_VECTOR(31 DOWNTO 0);
				CtrlSgnls				:	OUT		CTRL_SIGNL_REC);
	END COMPONENT;
																											--    	NOR instruction
	COMPONENT Decode_NOR IS
		PORT(	Instruction				:	IN		STD_LOGIC_VECTOR(31 DOWNTO 0);
				CtrlSgnls				:	OUT		CTRL_SIGNL_REC);
	END COMPONENT;
																											--    	NOT instruction
	COMPONENT Decode_NOT IS
		PORT(	Instruction				:	IN		STD_LOGIC_VECTOR(31 DOWNTO 0);
				CtrlSgnls				:	OUT		CTRL_SIGNL_REC);
	END COMPONENT;
																											--    	OR instruction
	COMPONENT Decode_OR IS	
		PORT(	Instruction				:	IN		STD_LOGIC_VECTOR(31 DOWNTO 0);
				CtrlSgnls				:	OUT		CTRL_SIGNL_REC);
	END COMPONENT;
																											--    	ORI instruction
	COMPONENT Decode_ORI IS
		PORT(	Instruction				:	IN		STD_LOGIC_VECTOR(31 DOWNTO 0);
				CtrlSgnls				:	OUT		CTRL_SIGNL_REC);
	END COMPONENT;
																											--    	SB instruction
	COMPONENT Decode_SB IS
		PORT(	Instruction				:	IN		STD_LOGIC_VECTOR(31 DOWNTO 0);
				CtrlSgnls				:	OUT		CTRL_SIGNL_REC);
	END COMPONENT;
																											--    	SC instruction
	COMPONENT Decode_SC IS
		PORT(	Instruction				:	IN		STD_LOGIC_VECTOR(31 DOWNTO 0);
				CtrlSgnls				:	OUT		CTRL_SIGNL_REC);
	END COMPONENT;
																											--    	SH instruction
	COMPONENT Decode_SH IS
		PORT(	Instruction				:	IN		STD_LOGIC_VECTOR(31 DOWNTO 0);
				CtrlSgnls				:	OUT		CTRL_SIGNL_REC);
	END COMPONENT;
																											--    	SLA instruction
	COMPONENT Decode_SLA IS
		PORT(	Instruction				:	IN		STD_LOGIC_VECTOR(31 DOWNTO 0);
				CtrlSgnls				:	OUT		CTRL_SIGNL_REC);
	END COMPONENT;
																											--    	SLAV instruction
	COMPONENT Decode_SLAV IS
		PORT(	Instruction				:	IN		STD_LOGIC_VECTOR(31 DOWNTO 0);
				CtrlSgnls				:	OUT		CTRL_SIGNL_REC);
	END COMPONENT;
																											--    	SLL instruction
	COMPONENT Decode_SLL IS
		PORT(	Instruction				:	IN		STD_LOGIC_VECTOR(31 DOWNTO 0);
				CtrlSgnls				:	OUT		CTRL_SIGNL_REC);
	END COMPONENT;
																											--    	SLLV instruction
	COMPONENT Decode_SLLV IS
		PORT(	Instruction				:	IN		STD_LOGIC_VECTOR(31 DOWNTO 0);
				CtrlSgnls				:	OUT		CTRL_SIGNL_REC);
	END COMPONENT;
																											--    	SLT instruction
	COMPONENT Decode_SLT IS
		PORT(	Instruction				:	IN		STD_LOGIC_VECTOR(31 DOWNTO 0);
				CtrlSgnls				:	OUT		CTRL_SIGNL_REC);
	END COMPONENT;
																											--    	SLTI instruction
	COMPONENT Decode_SLTI IS
		PORT(	Instruction				:	IN		STD_LOGIC_VECTOR(31 DOWNTO 0);
				CtrlSgnls				:	OUT		CTRL_SIGNL_REC);
	END COMPONENT;
																											--    	SLTIU instruction
	COMPONENT Decode_SLTIU IS
		PORT(	Instruction				:	IN		STD_LOGIC_VECTOR(31 DOWNTO 0);
				CtrlSgnls				:	OUT		CTRL_SIGNL_REC);
	END COMPONENT;
																											--    	SLTU instruction
	COMPONENT Decode_SLTU IS
		PORT(	Instruction				:	IN		STD_LOGIC_VECTOR(31 DOWNTO 0);
				CtrlSgnls				:	OUT		CTRL_SIGNL_REC);
	END COMPONENT;
																											--    	SRA instruction
	COMPONENT Decode_SRA IS
		PORT(	Instruction				:	IN		STD_LOGIC_VECTOR(31 DOWNTO 0);
				CtrlSgnls				:	OUT		CTRL_SIGNL_REC);
	END COMPONENT;
																											--    	SRAV instruction
	COMPONENT Decode_SRAV IS
		PORT(	Instruction				:	IN		STD_LOGIC_VECTOR(31 DOWNTO 0);
				CtrlSgnls				:	OUT		CTRL_SIGNL_REC);
	END COMPONENT;
																											--    	SRL instruction
	COMPONENT Decode_SRL IS
		PORT(	Instruction				:	IN		STD_LOGIC_VECTOR(31 DOWNTO 0);
				CtrlSgnls				:	OUT		CTRL_SIGNL_REC);
	END COMPONENT;
																											--    	SRLV instruction
	COMPONENT Decode_SRLV IS
		PORT(	Instruction				:	IN		STD_LOGIC_VECTOR(31 DOWNTO 0);
				CtrlSgnls				:	OUT		CTRL_SIGNL_REC);
	END COMPONENT;
																											--    	SUB instruction
	COMPONENT Decode_SUB IS
		PORT(	Instruction				:	IN		STD_LOGIC_VECTOR(31 DOWNTO 0);
				CtrlSgnls				:	OUT		CTRL_SIGNL_REC);
	END COMPONENT;
																											--    	SUBU instruction
	COMPONENT Decode_SUBU IS
		PORT(	Instruction				:	IN		STD_LOGIC_VECTOR(31 DOWNTO 0);
				CtrlSgnls				:	OUT		CTRL_SIGNL_REC);
	END COMPONENT;
																											--    	SW instruction
	COMPONENT Decode_SW IS
		PORT(	Instruction				:	IN		STD_LOGIC_VECTOR(31 DOWNTO 0);
				CtrlSgnls				:	OUT		CTRL_SIGNL_REC);
	END COMPONENT;
																											--    	SWL instruction
	COMPONENT Decode_XOR IS
		PORT(	Instruction				:	IN		STD_LOGIC_VECTOR(31 DOWNTO 0);
				CtrlSgnls				:	OUT		CTRL_SIGNL_REC);
	END COMPONENT;
																											--    	XORI instruction
	COMPONENT Decode_XORI IS
		PORT(	Instruction				:	IN		STD_LOGIC_VECTOR(31 DOWNTO 0);
				CtrlSgnls				:	OUT		CTRL_SIGNL_REC);
	END COMPONENT;

	FUNCTION	CtrlSgnls_Float RETURN CTRL_SIGNL_REC;
	FUNCTION	IR_to_Rtype(Instruction : STD_LOGIC_VECTOR(31 DOWNTO 0)) RETURN R_INSTRUCTION;
	FUNCTION	IR_to_Itype(Instruction : STD_LOGIC_VECTOR(31 DOWNTO 0)) RETURN I_INSTRUCTION;
	FUNCTION	IR_to_Jtype(Instruction : STD_LOGIC_VECTOR(31 DOWNTO 0)) RETURN J_INSTRUCTION;
	
END Package;


PACKAGE BODY DecodeLogic_Pkg IS
	
	FUNCTION	CtrlSgnls_Float RETURN CTRL_SIGNL_REC IS
		BEGIN
			RETURN(	 ALU_func 		=> ALU_FUNC_FLOAT,														--  ALU function code
					 ALU_Asel 		=> ALU_ASEL_FLOAT,														--	ALU A input source select 
  				     ALU_Ssel 		=> ALU_SSEL_FLOAT,														--	ALU shift amount source select
					 DM_strb 		=> DM_STRB_FLOAT,														--	Data memory data strobe
					 DM_rw    		=> DM_RW_FLOAT,															--	Data memory read/write                
					 DM_en    		=> DM_EN_FLOAT,															--	Data memory enable
					 NIAG_sel   	=> NIAG_SEL_FLOAT,														--  Program counter select
					 NIAG_strb  	=> NIAG_STRB_FLOAT,														--	Program counter condition code
					 NIAG_cond  	=> NIAG_COND_FLOAT,														--  Program counter use carry flag
					 IR_Xsel  		=> IR_XSEL_FLOAT,														--  IR immediate field extend method select
					 IR_Xlsft 		=> IR_XLSFT_FLOAT,														--  IR immediate field left shift method
					 IR_strb  		=> IR_STRB_FLOAT,														--	Instruction Register strobe
					 RF_Dsel  		=> RF_DSEL_FLOAT,														--	Register file data input select
					 RF_strb  		=> RF_STRB_FLOAT,														--	Register file strobe
					 RF_Wsel  		=> RF_WSEL_FLOAT,														--	Register file write destination select
					 RF_oe    		=> RF_OE_FLOAT															--	Register file output enable
					);
	END CtrlSgnls_Float;
	
	FUNCTION	IR_to_Rtype(Instruction : STD_LOGIC_VECTOR(31 DOWNTO 0)) RETURN R_INSTRUCTION IS
		BEGIN
			RETURN (  Instruction(31 DOWNTO 26),															--  opcode
					  Instruction(25 DOWNTO 21),															--	rs field (source 0)
					  Instruction(20 DOWNTO 16),															--	rt field (source 1)
					  Instruction(15 DOWNTO 11),															--	rd field (destination)
					  Instruction(10 DOWNTO  6),															--	sa field (shift)
					  Instruction( 5 DOWNTO  0) 															--	func field (aux opcode)
					 );
	END IR_to_Rtype;
	
	FUNCTION	IR_to_Itype(Instruction : STD_LOGIC_VECTOR(31 DOWNTO 0)) RETURN I_INSTRUCTION IS
		BEGIN
			RETURN (  Instruction(31 DOWNTO 26),															--  opcode
					  Instruction(25 DOWNTO 21),															--	rs field (source 0)
					  Instruction(20 DOWNTO 16),															--	rt field (source 1)
					  Instruction(15 DOWNTO  0)																--	immediate field
					 );
	END IR_to_Itype;
	
	FUNCTION	IR_to_Jtype(Instruction : STD_LOGIC_VECTOR(31 DOWNTO 0)) RETURN J_INSTRUCTION IS
		BEGIN
			RETURN (  Instruction(31 DOWNTO 26),															--  opcode
					  Instruction(25 DOWNTO 0)																--	target field
					 );
	END IR_to_Jtype;

END;