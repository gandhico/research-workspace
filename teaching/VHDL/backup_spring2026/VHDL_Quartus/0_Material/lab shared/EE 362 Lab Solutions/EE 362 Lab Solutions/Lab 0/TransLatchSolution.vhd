--------------------------------------------------------------------------------------
--  Component:	TransLatchSolution
--
--       File:	TransLatchSolution.vhd
--	
--    Project:	LabCPU
--
--     Author:	A.K. Petersen
--
--    Purpose: define a one-bit transparent latch
--
--     Inputs: Clock: while 1 latch is transparent
--                    while 0 latch is opaque
--             Reset: while 1 latch forced to 0, ignores Clock and Din
--                    while 0 latch is free to respond to Clock and Din
--               Din: value to store in latch
--
--    Outputs:  Dout: value currently stored in latch
--
--  Copyright 2021 by A.K. Petersen, New Mexico State University, all rights reserved
--
-------------------------------------------------------------------------------------
 
ENTITY TransLatch IS
	PORT(	Clock	:	IN		BIT;
			Reset	:	IN		BIT;
			Din		:	IN		BIT;
			Dout	:	OUT		BIT
		  );
END ENTITY;

ARCHITECTURE Behavioral OF TransLatch IS
	SIGNAL	Content	:	BIT;
BEGIN
	Dout <= Content;
	
	PROCESS(Clock, Reset, Din)
	BEGIN
		IF Reset='0' THEN
			Content <= '0';
		ELSIF Clock='1' THEN
			Content <= Din;
		END IF;
	END PROCESS;
END ARCHITECTURE;

PACKAGE TransLatchPackage IS
	COMPONENT TransLatch IS
		PORT(	Clock	:	IN		BIT;
				Reset	:	IN		BIT;
				Din		:	IN		BIT;
				Dout	:	OUT		BIT);
	END COMPONENT;
END PACKAGE;
