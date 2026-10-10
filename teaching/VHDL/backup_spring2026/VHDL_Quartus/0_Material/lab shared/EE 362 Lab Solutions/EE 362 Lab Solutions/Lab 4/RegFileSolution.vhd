-------------------------------------------------------------------------------------
--Description:	RegFileSolution
--
--       File:	RegFileSolution.vhd
--	
--    Project:	LabCPU
--
--     Author:	A.K. Petersen
--
--    Purpose: Define a 32-bit, tri-ported, register file
--
--     Inputs:    Asel: 5-bit  Aout select bus
--                Bsel: 5-bit  Bout select bus
--                Dsel: 5-bit  Bout select bus
--                 Din: 32-bit data input bus
--                Func: data transfer function
--               Field: data portion to target
--				  Strb: Data input save strobe
--
--    Outputs:    Aout:	32-bit output selected by Asel
--                Bout: 32-bit output selected by Bsel
--
--  Copyright 2021 by A.K. Petersen, New Mexico State University, all rights reserved
--
-------------------------------------------------------------------------------------
 
library IEEE;
use IEEE.STD_LOGIC_1164.ALL;

library EE_362_Decoder;
use EE_362_Decoder.DecodeLogic_Pkg.all;


ENTITY RegFile IS
	PORT(	Asel	:	IN		STD_LOGIC_VECTOR(4  DOWNTO 0);
			Bsel	:	IN		STD_LOGIC_VECTOR(4  DOWNTO 0);
			Dsel	:	IN		STD_LOGIC_VECTOR(4  DOWNTO 0);
			 Din	:	IN		STD_LOGIC_VECTOR(31 DOWNTO 0);
			func	:	IN		std_logic_vector(1 downto 0);
			field	:	IN		std_logic_vector(2 downto 0);
			Strb	:	IN		STD_LOGIC;
			Aout	:	OUT		STD_LOGIC_VECTOR(31 DOWNTO 0);
			Bout	:	OUT		STD_LOGIC_VECTOR(31 DOWNTO 0));
END ENTITY;


ARCHITECTURE Behavioral OF RegFile IS
	SIGNAL	Reg00	:	STD_LOGIC_VECTOR(31  DOWNTO 0):= (others => '0');	-- constant zero
	SIGNAL	Reg01	:	STD_LOGIC_VECTOR(31  DOWNTO 0);
	SIGNAL	Reg02	:	STD_LOGIC_VECTOR(31  DOWNTO 0);
	SIGNAL	Reg03	:	STD_LOGIC_VECTOR(31  DOWNTO 0);
	SIGNAL	Reg04	:	STD_LOGIC_VECTOR(31  DOWNTO 0);
	SIGNAL	Reg05	:	STD_LOGIC_VECTOR(31  DOWNTO 0);
	SIGNAL	Reg06	:	STD_LOGIC_VECTOR(31  DOWNTO 0);
	SIGNAL	Reg07	:	STD_LOGIC_VECTOR(31  DOWNTO 0);
	SIGNAL	Reg08	:	STD_LOGIC_VECTOR(31  DOWNTO 0);
	SIGNAL	Reg09	:	STD_LOGIC_VECTOR(31  DOWNTO 0);
	SIGNAL	Reg0A	:	STD_LOGIC_VECTOR(31  DOWNTO 0);
	SIGNAL	Reg0B	:	STD_LOGIC_VECTOR(31  DOWNTO 0);
	SIGNAL	Reg0C	:	STD_LOGIC_VECTOR(31  DOWNTO 0);
	SIGNAL	Reg0D	:	STD_LOGIC_VECTOR(31  DOWNTO 0);
	SIGNAL	Reg0E	:	STD_LOGIC_VECTOR(31  DOWNTO 0);
	SIGNAL	Reg0F	:	STD_LOGIC_VECTOR(31  DOWNTO 0);
	SIGNAL	Reg10	:	STD_LOGIC_VECTOR(31  DOWNTO 0);
	SIGNAL	Reg11	:	STD_LOGIC_VECTOR(31  DOWNTO 0);
	SIGNAL	Reg12	:	STD_LOGIC_VECTOR(31  DOWNTO 0);
	SIGNAL	Reg13	:	STD_LOGIC_VECTOR(31  DOWNTO 0);
	SIGNAL	Reg14	:	STD_LOGIC_VECTOR(31  DOWNTO 0);
	SIGNAL	Reg15	:	STD_LOGIC_VECTOR(31  DOWNTO 0);
	SIGNAL	Reg16	:	STD_LOGIC_VECTOR(31  DOWNTO 0);
	SIGNAL	Reg17	:	STD_LOGIC_VECTOR(31  DOWNTO 0);
	SIGNAL	Reg18	:	STD_LOGIC_VECTOR(31  DOWNTO 0);
	SIGNAL	Reg19	:	STD_LOGIC_VECTOR(31  DOWNTO 0);
	SIGNAL	Reg1A	:	STD_LOGIC_VECTOR(31  DOWNTO 0);
	SIGNAL	Reg1B	:	STD_LOGIC_VECTOR(31  DOWNTO 0);
	SIGNAL	Reg1C	:	STD_LOGIC_VECTOR(31  DOWNTO 0);
	SIGNAL	Reg1D	:	STD_LOGIC_VECTOR(31  DOWNTO 0);
	SIGNAL	Reg1E	:	STD_LOGIC_VECTOR(31  DOWNTO 0);
	SIGNAL	Reg1F	:	STD_LOGIC_VECTOR(31  DOWNTO 0);

	BEGIN
 
   WITH Asel SELECT Aout <=  VAL_32_ZERO		WHEN RF_REG_00,        -- assign the A output value
							 Reg01				WHEN RF_REG_01,
							 Reg02				WHEN RF_REG_02,
							 Reg03				WHEN RF_REG_03,
							 Reg04				WHEN RF_REG_04,
							 Reg05				WHEN RF_REG_05,
							 Reg06				WHEN RF_REG_06,
							 Reg07				WHEN RF_REG_07,
							 Reg08				WHEN RF_REG_08,
 							 Reg09				WHEN RF_REG_09,
							 Reg0A				WHEN RF_REG_0A,
							 Reg0B				WHEN RF_REG_0B,
							 Reg0C				WHEN RF_REG_0C,
							 Reg0D				WHEN RF_REG_0D,
							 Reg0E				WHEN RF_REG_0E,
							 Reg0F				WHEN RF_REG_0F,
							 Reg10				WHEN RF_REG_10,
							 Reg11				WHEN RF_REG_11,
							 Reg12				WHEN RF_REG_12,
							 Reg13				WHEN RF_REG_13,
							 Reg14				WHEN RF_REG_14,
							 Reg15				WHEN RF_REG_15,
							 Reg16				WHEN RF_REG_16,
							 Reg17				WHEN RF_REG_17,
							 Reg18				WHEN RF_REG_18,
							 Reg19				WHEN RF_REG_19,
							 Reg1A				WHEN RF_REG_1A,
							 Reg1B				WHEN RF_REG_1B,
							 Reg1C				WHEN RF_REG_1C,
							 Reg1D				WHEN RF_REG_1D,
							 Reg1E				WHEN RF_REG_1E,
							 Reg1F				WHEN RF_REG_1F,
							 (Others => 'Z')	WHEN OTHERS;
						  
						  

   WITH Bsel SELECT Bout <=  VAL_32_ZERO		WHEN RF_REG_00,        -- assign the B output value
							 Reg01				WHEN RF_REG_01,
							 Reg02				WHEN RF_REG_02,
							 Reg03				WHEN RF_REG_03,
							 Reg04				WHEN RF_REG_04,
							 Reg05				WHEN RF_REG_05,
							 Reg06				WHEN RF_REG_06,
							 Reg07				WHEN RF_REG_07,
							 Reg08				WHEN RF_REG_08,
 							 Reg09				WHEN RF_REG_09,
							 Reg0A				WHEN RF_REG_0A,
							 Reg0B				WHEN RF_REG_0B,
							 Reg0C				WHEN RF_REG_0C,
							 Reg0D				WHEN RF_REG_0D,
							 Reg0E				WHEN RF_REG_0E,
							 Reg0F				WHEN RF_REG_0F,
							 Reg10				WHEN RF_REG_10,
							 Reg11				WHEN RF_REG_11,
							 Reg12				WHEN RF_REG_12,
							 Reg13				WHEN RF_REG_13,
							 Reg14				WHEN RF_REG_14,
							 Reg15				WHEN RF_REG_15,
							 Reg16				WHEN RF_REG_16,
							 Reg17				WHEN RF_REG_17,
							 Reg18				WHEN RF_REG_18,
 							 Reg19				WHEN RF_REG_19,
							 Reg1A				WHEN RF_REG_1A,
							 Reg1B				WHEN RF_REG_1B,
							 Reg1C				WHEN RF_REG_1C,
							 Reg1D				WHEN RF_REG_1D,
							 Reg1E				WHEN RF_REG_1E,
							 Reg1F				WHEN RF_REG_1F,
							 (Others => 'Z')	WHEN OTHERS;
						  
                    
   PROCESS(Strb)                              -- load the selected register
		BEGIN
		 IF falling_edge(Strb) THEN	 
			CASE DSel IS
						WHEN RF_REG_00 => Reg00 <= VAL_32_ZERO;
						WHEN RF_REG_01 => Reg01 <= Din;
						WHEN RF_REG_02 => Reg02 <= Din;
						WHEN RF_REG_03 => Reg03 <= Din;
						WHEN RF_REG_04 => Reg04 <= Din;
						WHEN RF_REG_05 => Reg05 <= Din;
						WHEN RF_REG_06 => Reg06 <= Din;
						WHEN RF_REG_07 => Reg07 <= Din;
						WHEN RF_REG_08 => Reg08 <= Din;
						WHEN RF_REG_09 => Reg09 <= Din;
						WHEN RF_REG_0A => Reg0A <= Din;
						WHEN RF_REG_0B => Reg0B <= Din;
						WHEN RF_REG_0C => Reg0C <= Din;
						WHEN RF_REG_0D => Reg0D <= Din;
						WHEN RF_REG_0E => Reg0E <= Din;
						WHEN RF_REG_0F => Reg0F <= Din;
						WHEN RF_REG_10 => Reg10 <= Din;
						WHEN RF_REG_11 => Reg11 <= Din;
						WHEN RF_REG_12 => Reg12 <= Din;
						WHEN RF_REG_13 => Reg13 <= Din;
						WHEN RF_REG_14 => Reg14 <= Din;
						WHEN RF_REG_15 => Reg15 <= Din;
						WHEN RF_REG_16 => Reg16 <= Din;
						WHEN RF_REG_17 => Reg17 <= Din;
						WHEN RF_REG_18 => Reg18 <= Din;
						WHEN RF_REG_19 => Reg19 <= Din;
						WHEN RF_REG_1A => Reg1A <= Din;
						WHEN RF_REG_1B => Reg1B <= Din;
						WHEN RF_REG_1C => Reg1C <= Din;
						WHEN RF_REG_1D => Reg1D <= Din;
						WHEN RF_REG_1E => Reg1E <= Din;
						WHEN RF_REG_1F => Reg1F <= Din;
						WHEN OTHERS    => Reg00 <= VAL_32_ZERO;
			END CASE;
		 END IF;
  END PROCESS;
END ARCHITECTURE;
