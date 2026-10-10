Library IEEE;
use IEEE.std_logic_1164.all;

Library EE_212_Memory;
use EE_212_Memory.Memory_pkg.all;

Library EE_212_Decoder;
use EE_212_Decoder.DecodeLogic_pkg.all;

use IEEE.NUMERIC_STD.All;

ENTITY RAM is

PORT(			Addr	:	IN		STD_LOGIC_VECTOR(31 DOWNTO 0);					--   Address
				Strb	:	IN		STD_LOGIC;								      		--   Strobe
				rw		:	IN		STD_LOGIC;								      		--   Read/Write
				en		:	IN		STD_LOGIC;							      			--   Enable
				clk   :  IN    STD_LOGIC;
				Data	:	INOUT	STD_LOGIC_VECTOR(31 DOWNTO 0)			    		--   Data in and out
    );
		 
END ENTITY;

ARCHITECTURE behavioral of RAM is

SIGNAL RAM_CONTENT: RAM_MEMORY :=(
	0 => X"FF",
	1 => X"FF",
	2 => X"FF",
	3 => X"FF",
	4 => X"FF",
	5 => X"FF",
	6 => X"FF",
	7 => X"FF",
	8 => X"FF",
	9 => X"FF",
	10=> X"FF",
	11=> X"FF",
	12=> X"FF",
	13=> X"FF",
	14=> X"FF",
	15=> X"FF",
	
	OTHERS => (OTHERS => '0'));   --16 to 511
	
	SIGNAL Data_signal: STD_LOGIC_VECTOR(31 Downto 0);
	
begin

	Process(clk, en, Data, Strb, rw, Addr, RAM_CONTENT, data_signal)
		begin
	
			if en = DM_EN_ENABLE then
				if rw = DM_RW_WR then
					if (clk'event and clk='1' and strb='1') then
					
						RAM_CONTENT(TO_INTEGER(UNSIGNED(Addr)+0)) <= Data(31 Downto 24);
						RAM_CONTENT(TO_INTEGER(UNSIGNED(Addr)+1)) <= Data(23 Downto 16);
						RAM_CONTENT(TO_INTEGER(UNSIGNED(Addr)+2)) <= Data(15 Downto 8);
						RAM_CONTENT(TO_INTEGER(UNSIGNED(Addr)+3)) <= Data(7  Downto 0);
				
						data <= (others => 'Z');
						
					end if;
				elsif rw = DM_RW_RD then
				
					Data_Signal(31 Downto 24) <= RAM_CONTENT(TO_INTEGER(UNSIGNED(Addr)+0));
					Data_Signal(23 Downto 16) <= RAM_CONTENT(TO_INTEGER(UNSIGNED(Addr)+1));
					Data_Signal(15 Downto  8) <= RAM_CONTENT(TO_INTEGER(UNSIGNED(Addr)+2));
					Data_Signal(7  Downto  0) <= RAM_CONTENT(TO_INTEGER(UNSIGNED(Addr)+3));
				
					Data <= Data_Signal;
				else
					Data <= (others => 'Z');
				end if;
			elsif en = DM_EN_DISABLE then
				data <= (others => 'Z');
			end if;
		end process;
	
END Architecture;