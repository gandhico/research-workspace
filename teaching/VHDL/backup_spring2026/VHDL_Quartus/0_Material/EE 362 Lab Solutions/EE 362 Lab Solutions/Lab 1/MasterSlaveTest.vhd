-------------------------------------------------------------------------------------
--Description:	MasterSlaveTest
--
--       File:	MasterSlaveTest.vhd
--	
--    Project:	LabCPU
--
--     Author:	A.K. Petersen
--
--    Purpose: Test stub for MasterSlave component
--
--     Inputs: Clock: signal to drive MasterSlave Clock input
--             Reset: signal to drive MasterSlave Reset input
--               Din: signal to drive MasterSlave Din input
--
--    Outputs:  Dout: signal driven by MasterSlave Dout output
--
--  Copyright 2021 by A.K. Petersen, New Mexico State University, all rights reserved
--
-------------------------------------------------------------------------------------
 
LIBRARY work;
USE work.MasterSlavePackage.MasterSlave;

 ENTITY MasterSlaveTest IS
	PORT(	Clock	:	IN		BIT;
			Reset	:	IN		BIT;
			Din		:	IN		BIT;
			Dout	:	OUT		BIT);
END ENTITY;

ARCHITECTURE Behavioral OF MasterSlaveTest IS
BEGIN
	TestComponent : MasterSlave PORT MAP(Clock, Reset, Din, Dout);
END ARCHITECTURE;


	
