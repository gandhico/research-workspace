--------------------------------------------------------------------------------------
--  Component:	NIAG_Rel
--
--       File:	NIAG_Rel.vhd
--	
--    Project:	LabCPU
--
--     Author:	A.K. Petersen
--
--    Purpose: define the relative instruction address
--
--     Inputs:	 Immed: Immediate field from IR
--               Xshft: Immed value shift selection
--                 NSA: Next Sequential Address
--
--    Outputs: RelAdrs: relative instruction's address
--
--  Copyright 2021 by A.K. Petersen, New Mexico State University, all rights reserved
--
-------------------------------------------------------------------------------------

LIBRARY IEEE;
USE IEEE.STD_LOGIC_1164.ALL;
USE IEEE.NUMERIC_STD.ALL;

LIBRARY EE_362_Decoder;
use EE_362_Decoder.DecodeLogic_Pkg.all;

ENTITY NIAG_Rel IS
	PORT(	Immed 	:	IN		STD_LOGIC_VECTOR(31 DOWNTO 0);
			Xshft	:	IN		STD_LOGIC;
			NSA		:	IN		STD_LOGIC_VECTOR(31 DOWNTO 0);
			RelAdrs	:	OUT		STD_LOGIC_VECTOR(31 DOWNTO 0));
END ENTITY;

ARCHITECTURE Behavioral OF NIAG_Rel IS
	SIGNAL Aligned	:	STD_LOGIC_VECTOR(31 DOWNTO 0);
		
	BEGIN
		PROCESS (Immed, Xshft) IS					-- word align immed (or not)
		BEGIN
			IF Xshft = IR_XLSFT_TWO THEN
				Aligned <= Immed(31 DOWNTO 2) & "00";
			ELSE
				Aligned <= Immed;
			END IF;
			
			RelAdrs <= std_logic_vector(unsigned(Aligned) + unsigned(Immed));
		END PROCESS;
END ARCHITECTURE;
