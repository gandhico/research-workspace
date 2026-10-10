-------------------------------------------------------------------------------------
--Description:	TransLatchTest
--
--       File:	TransLatchTest.vhd
--	
--    Project:	LabCPU
--
--     Author:	A.K. Petersen
--
--    Purpose: Test stub for TransLatch component
--
--     Inputs: Clock: signal to drive Latch Clock input
--             Reset: signal to drive Latch Reset input
--               Din: signal to drive Latch Din input
--
--    Outputs:  Dout: signal driven by Latch Dout output
--
--  Copyright 2021 by A.K. Petersen, New Mexico State University, all rights reserved
--
-------------------------------------------------------------------------------------
 
LIBRARY work;
USE work. TransLatchPackage.TransLatch;

 ENTITY TransLatchTest IS
	PORT(	Clock	:	IN		BIT;
			Reset	:	IN		BIT;
			Din		:	IN		BIT;
			Dout	:	OUT		BIT
		  );
END ENTITY;

ARCHITECTURE Behavioral OF TransLatchTest IS
BEGIN
	TestComponent : TransLatch PORT MAP(Clock, Reset, Din, Dout);
END ARCHITECTURE;
