-------------------------------------------------------------------------------------
--Description:	RAM
--
--       File:	RamSolution.vhd
--	
--    Project:	LabCPU
--
--     Author:	A.K. Petersen
--
--    Purpose: Define the data memory module
--
--     Inputs:    Addr	: address bus
--			      Strb	: clock
--			      rw	: read/write signal
--                en	: memory enable
--
--     InOuts:    Data: data bus
--
--  Copyright 2021 by A.K. Petersen, New Mexico State University, all rights reserved
--
-------------------------------------------------------------------------------------
 
library IEEE;
use IEEE.STD_LOGIC_1164.ALL;
USE IEEE.NUMERIC_STD.ALL;

library EE_362_Decoder;
use EE_362_Decoder.DecodeLogic_Pkg.all;

library EE_362_Memory;
use EE_362_Memory.Memory_Pkg.all;

ENTITY RAM IS
	PORT(	Addr	:	IN		STD_LOGIC_VECTOR(31 DOWNTO 0);
			Strb	:	IN		STD_LOGIC;
			 rw		:	IN		STD_LOGIC;
			 en		:	IN		STD_LOGIC;
		   Data		:	INOUT	STD_LOGIC_VECTOR(31 DOWNTO 0)
	    );
END ENTITY;


ARCHITECTURE Behavioral OF RAM IS
	SIGNAL	RAM_Content	: RAM_Memory := (3=>X"01", 5=>X"02", 7=>X"03", 9=>X"04", 11=>X"05", 
										13=>X"06", 15=>X"07", others=>X"00");

BEGIN
	PROCESS(en, Data, Strb, rw, Addr)
	BEGIN
		IF en = DM_EN_ENABLE THEN														-- memory enabled?
			IF rw = DM_RW_WR THEN														--  yes: read or write?
				IF rising_edge(Strb) THEN												--    write: strobed?
					RAM_Content(to_integer(UNSIGNED(Addr))+0) <= Data(31 DOWNTO 24);	--     yes:  MSB
					RAM_Content(to_integer(UNSIGNED(Addr))+1) <= Data(23 DOWNTO 16);	--	         next-to-MSB
					RAM_Content(to_integer(UNSIGNED(Addr))+2) <= Data(15 DOWNTO  8);	--           next-to-LSB
					RAM_Content(to_integer(UNSIGNED(Addr))+3) <= Data(7  DOWNTO  0);	--	         LSB
				END IF;	
			ELSE																		--     read:
				Data(31 DOWNTO 24) <= RAM_Content(to_integer(UNSIGNED(Addr))+0);		--       MSB
				Data(23 DOWNTO 16) <= RAM_Content(to_integer(UNSIGNED(Addr))+1);		--       next-to-MSB
				Data(15 DOWNTO  8) <= RAM_Content(to_integer(UNSIGNED(Addr))+2);		--       next-to-LSB
				Data(7  DOWNTO  0) <= RAM_Content(to_integer(UNSIGNED(Addr))+3);		--       LSB
			END IF;	
		ELSE																			-- memory not enabled
			Data <= VAL_32_FLOAT;														--  float everything
		END IF;
	END PROCESS;
END ARCHITECTURE;
