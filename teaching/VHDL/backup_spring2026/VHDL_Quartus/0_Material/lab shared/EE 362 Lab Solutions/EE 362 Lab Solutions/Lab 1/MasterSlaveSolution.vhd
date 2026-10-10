-------------------------------------------------------------------------------------
--  Component:	MasterSlaveSolution
--
--       File:	MasterSlaveSolution.vhd
--	
--    Project:	LabCPU
--
--     Author:	A.K. Petersen
--
--    Purpose: define a one-bit master-slave rising edge flip-flop
--
--     Inputs: Clock: rising edge cause flip flop to strobe data
--             Reset: while 1 flip flop forced to 0, ignores Clock and Din
--                    while 0 flip flop is free to respond to Clock and Din
--               Din: value to store in flip flop
--
--    Outputs:  Dout: value currently stored in flip flop
--
--  Copyright 2021 by A.K. Petersen, New Mexico State University, all rights reserved
--
-------------------------------------------------------------------------------------
 
LIBRARY work;
USE work.TransLatchPackage.TransLatch;

 ENTITY MasterSlave IS
	PORT(	Clock	:	IN		BIT;
			Reset	:	IN		BIT;
			Din		:	IN		BIT;
			Dout	:	OUT		BIT
		  );
END ENTITY;

ARCHITECTURE Behavioral OF MasterSlave IS
	SIGNAL	MasterOut	:	BIT;
	SIGNAL	NotClock	:	BIT;
BEGIN
	NotClock <= NOT(Clock);

	Master	: TransLatch PORT MAP(NotClock, Reset, Din, MasterOut);
	Slave	: TransLatch PORT MAP(Clock, Reset, MasterOut, Dout);
END ARCHITECTURE;

PACKAGE MasterSlavePackage IS
	COMPONENT MasterSlave IS
		PORT(	Clock	:	IN		BIT;
				Reset	:	IN		BIT;
				Din		:	IN		BIT;
				Dout	:	OUT		BIT
			  );
	END COMPONENT;
END PACKAGE;
