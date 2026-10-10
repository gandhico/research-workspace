-------------------------------------------------------------------------------------
--Description:	TestDecoder
--
--       File:	TestDecoderSolution.vhd
--	
--    Project:	LabCPU
--
--     Author:	A.K. Petersen
--
--    Purpose: Test stub for the Decode Logic component
--
--     Inputs:  Instruction : instruction to be decoded
--
--	  Outputs:    CtrlSgnls : control signals
--
--  Copyright 2021 by A.K. Petersen, New Mexico State University, all rights reserved
--
-------------------------------------------------------------------------------------
 
library IEEE;
use IEEE.STD_LOGIC_1164.ALL;

library EE_362_Decoder;
use EE_362_Decoder.DecodeLogic_Pkg.all;

library EE_362_ALU;
USE EE_362_ALU.ALU_Pkg.all;


ENTITY TestDecoder IS
PORT(	Instruction	:	IN		STD_LOGIC_VECTOR(31 DOWNTO 0);
		CtrlSgnls	:	OUT		CTRL_SIGNL_REC);
END ENTITY;

ARCHITECTURE Behavioral OF TestDecoder IS
	BEGIN
		TestComponent : Decoder  PORT MAP(Instruction, CtrlSgnls);
END ARCHITECTURE;
