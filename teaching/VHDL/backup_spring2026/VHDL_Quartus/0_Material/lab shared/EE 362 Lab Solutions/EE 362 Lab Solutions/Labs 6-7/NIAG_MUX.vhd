--------------------------------------------------------------------------------------
--  Component:	NIAG_MUX
--
--       File:	NIAG_MUX.vhd
--	
--    Project:	LabCPU
--
--     Author:	A.K. Petersen
--
--    Purpose: define the PC MUX
--
--     Inputs:	 NxtAdrs: Next Sequential Address
--			   AbsltAdrs: absolute address
--               RelAdrs: relative address
--               RegAdrs: register address
--                  Cond: logical condition being tested
--                   Sel: next instruction address selection
--                  Stat: ALU status signals
--
--    Outputs: InstrAdrs: next instruction address
--
--  Copyright 2021 by A.K. Petersen, New Mexico State University, all rights reserved
--
-------------------------------------------------------------------------------------

LIBRARY IEEE;
USE IEEE.STD_LOGIC_1164.ALL;
USE IEEE.NUMERIC_STD.ALL;

LIBRARY EE_362_ALU_Pkg;
USE EE_362_ALU.ALU_Pkg.all;

LIBRARY EE_362_Decoder;
use EE_362_Decoder.DecodeLogic_Pkg.all;

ENTITY NIAG_MUX IS
	PORT(	NxtAdrs		:	IN		STD_LOGIC_VECTOR(31 DOWNTO 0);						-- Next Sequential Address
			AbsltAdrs	:	IN		STD_LOGIC_VECTOR(31 DOWNTO 0);						-- Absolute Address
			RelAdrs		:	IN		STD_LOGIC_VECTOR(31 DOWNTO 0);						-- Relative address
			RegAdrs		:	IN		STD_LOGIC_VECTOR(31 DOWNTO 0);						-- Register Address
			Cond			:	IN		STD_LOGIC_VECTOR(2  DOWNTO 0);						-- Relative address condition 
			Sel			:	IN		STD_LOGIC_VECTOR(1  DOWNTO 0);						-- 
			Stat			:	IN		STAT_SIGNL_REC;											-- ALU condition codes
			InstrAdrs	:	OUT	STD_LOGIC_VECTOR(31 DOWNTO 0));						-- Next insrtruction address
END ENTITY;

ARCHITECTURE Behavioral OF NIAG_MUX IS
	SIGNAL MUX_Sel		:	STD_LOGIC_VECTOR(1 DOWNTO 0);
	
	BEGIN
--		Mux_Sel <= Sel;																					-- takes care of REG, ABS, and NSA
		PROCESS (Cond, Mux_Sel, Stat) IS
		BEGIN
			IF Mux_Sel /= NIAG_SEL_FLOAT THEN																-- do anything?
				IF Mux_Sel = NIAG_SEL_REL THEN																-- yes: branch?
					MUX_Sel <= NIAG_SEL_NSA;															-- assume no branch
					
					CASE Cond IS																		-- test branch condition
						WHEN NIAG_COND_EQ	=> IF Stat.ALU_zero = ALU_STAT_ZERO THEN	--    =
													MUX_Sel <= NIAG_SEL_REL;
												END IF;
													
						WHEN NIAG_COND_NEQ	=> IF Stat.ALU_zero = ALU_STAT_N_ZERO THEN	--    /=
													MUX_Sel <= NIAG_SEL_REL;
												END IF;
													
						WHEN NIAG_COND_GTZ	=> IF (Stat.ALU_zero = ALU_STAT_N_ZERO) AND	--    >0
												  (Stat.ALU_sign = ALU_STAT_POS) THEN
													MUX_Sel <= NIAG_SEL_REL;
												END IF;
												
						WHEN NIAG_COND_LTZ	=> IF (Stat.ALU_zero = ALU_STAT_N_ZERO) AND	--    <0
												  (Stat.ALU_sign = ALU_STAT_NEG) THEN
													MUX_Sel <= NIAG_SEL_REL;
												END IF;
													
						WHEN NIAG_COND_GEZ	=> IF (Stat.ALU_zero = ALU_STAT_ZERO) AND	--    >=0
												  (Stat.ALU_sign = ALU_STAT_POS) THEN
												 	MUX_Sel <= NIAG_SEL_REL;
												END IF;
													
						WHEN NIAG_COND_LEZ	=> IF (Stat.ALU_zero = ALU_STAT_ZERO) AND	--    <=
											  	  (Stat.ALU_sign = ALU_STAT_NEG) THEN
													MUX_Sel <= NIAG_SEL_REL;
												END IF;
													
						WHEN others			=> MUX_Sel <= NIAG_SEL_NSA;					--    everything else			
					END CASE;
				END IF;
			END IF;	
		END PROCESS;
		
		WITH MUX_Sel SELECT
			InstrAdrs	<= 	AbsltAdrs	WHEN 	NIAG_SEL_ABS,
							RelAdrs		WHEN 	NIAG_SEL_REL,
							RegAdrs		WHEN 	NIAG_SEL_REG,
							UNAFFECTED	WHEN	NIAG_SEL_FLOAT,
							NxtAdrs		WHEN 	OTHERS;
END ARCHITECTURE;
