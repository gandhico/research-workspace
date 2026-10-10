--Zuriel Esparza
--7/07/2021

library IEEE;
use IEEE.STD_LOGIC_1164.ALL;

library EE_212_Decoder;
use EE_212_Decoder.DecodeLogic_pkg.all;

Entity RegFile is

		PORT(	Asel	:	IN		STD_LOGIC_VECTOR(4  DOWNTO 0);		--    A select bus
				Bsel	:	IN		STD_LOGIC_VECTOR(4  DOWNTO 0);		--    B select bus
				Dsel	:	IN		STD_LOGIC_VECTOR(4  DOWNTO 0);		--    Data write select bus
				 Din	:	IN		STD_LOGIC_VECTOR(31 DOWNTO 0);		--    Data input value
				Strb	:	IN		STD_LOGIC;									--    strobe
			
				Aout	:	OUT	STD_LOGIC_VECTOR(31 DOWNTO 0);		--    A output value
				Bout	:	OUT	STD_LOGIC_VECTOR(31 DOWNTO 0);		--    B output value
				clk   :  IN    STD_LOGIC);
		
		
end Entity;

Architecture behavioral of RegFile is


signal reg00 	: STD_LOGIC_VECTOR(31 downto 0):=(others=>'0');
signal reg01   : STD_LOGIC_VECTOR(31 downto 0);
signal reg02   : STD_LOGIC_VECTOR(31 downto 0);
signal reg03   : STD_LOGIC_VECTOR(31 downto 0);
signal reg04   : STD_LOGIC_VECTOR(31 downto 0);
signal reg05   : STD_LOGIC_VECTOR(31 downto 0);
signal reg06   : STD_LOGIC_VECTOR(31 downto 0);
signal reg07   : STD_LOGIC_VECTOR(31 downto 0);
signal reg08   : STD_LOGIC_VECTOR(31 downto 0);
signal reg09   : STD_LOGIC_VECTOR(31 downto 0);
signal reg0A   : STD_LOGIC_VECTOR(31 downto 0);
signal reg0B   : STD_LOGIC_VECTOR(31 downto 0);
signal reg0C   : STD_LOGIC_VECTOR(31 downto 0);
signal reg0D   : STD_LOGIC_VECTOR(31 downto 0);
signal reg0E   : STD_LOGIC_VECTOR(31 downto 0);
signal reg0F   : STD_LOGIC_VECTOR(31 downto 0);
signal reg10   : STD_LOGIC_VECTOR(31 downto 0);
signal reg11   : STD_LOGIC_VECTOR(31 downto 0);
signal reg12   : STD_LOGIC_VECTOR(31 downto 0);
signal reg13   : STD_LOGIC_VECTOR(31 downto 0);
signal reg14   : STD_LOGIC_VECTOR(31 downto 0);
signal reg15   : STD_LOGIC_VECTOR(31 downto 0);
signal reg16   : STD_LOGIC_VECTOR(31 downto 0);
signal reg17   : STD_LOGIC_VECTOR(31 downto 0);
signal reg18   : STD_LOGIC_VECTOR(31 downto 0);
signal reg19   : STD_LOGIC_VECTOR(31 downto 0);
signal reg1A   : STD_LOGIC_VECTOR(31 downto 0);
signal reg1B   : STD_LOGIC_VECTOR(31 downto 0);
signal reg1C   : STD_LOGIC_VECTOR(31 downto 0);
signal reg1D   : STD_LOGIC_VECTOR(31 downto 0);
signal reg1E   : STD_LOGIC_VECTOR(31 downto 0);
signal reg1F   : STD_LOGIC_VECTOR(31 downto 0);

	
	begin			--Reading for Aout 
	
		Aout<= reg00 when Asel= RF_REG_00 else
				 reg01 when Asel= RF_REG_01 else
				 reg02 when Asel= RF_REG_02 else
				 reg03 when Asel= RF_REG_03 else
				 reg04 when Asel= RF_REG_04 else
				 reg05 when Asel= RF_REG_05 else
				 reg06 when Asel= RF_REG_06 else
				 reg07 when Asel= RF_REG_07 else
				 reg08 when Asel= RF_REG_08 else
				 reg09 when Asel= RF_REG_09 else
				 reg0A when Asel= RF_REG_0A else
				 reg0B when Asel= RF_REG_0B else
				 reg0C when Asel= RF_REG_0C else
				 reg0D when Asel= RF_REG_0D else
				 reg0E when Asel= RF_REG_0E else
				 reg0F when Asel= RF_REG_0F else
				 reg10 when Asel= RF_REG_10 else
				 reg11 when Asel= RF_REG_11 else
				 reg12 when Asel= RF_REG_12 else
				 reg13 when Asel= RF_REG_13 else
				 reg14 when Asel= RF_REG_14 else
				 reg15 when Asel= RF_REG_15 else
				 reg16 when Asel= RF_REG_16 else
				 reg17 when Asel= RF_REG_17 else
				 reg18 when Asel= RF_REG_18 else
				 reg19 when Asel= RF_REG_19 else
				 reg1A when Asel= RF_REG_1A else
				 reg1B when Asel= RF_REG_1B else
				 reg1C when Asel= RF_REG_1C else
				 reg1D when Asel= RF_REG_1D else
				 reg1E when Asel= RF_REG_1E else
				 reg1F when Asel= RF_REG_1F else
				 (others=>'Z');
					--Reading for Bout
		Bout<= reg00 when Bsel= RF_REG_00 else
				 reg01 when Bsel= RF_REG_01 else
				 reg02 when Bsel= RF_REG_02 else
				 reg03 when Bsel= RF_REG_03 else
				 reg04 when Bsel= RF_REG_04 else
				 reg05 when Bsel= RF_REG_05 else
				 reg06 when Bsel= RF_REG_06 else
				 reg07 when Bsel= RF_REG_07 else
				 reg08 when Bsel= RF_REG_08 else
				 reg09 when Bsel= RF_REG_09 else
				 reg0A when Bsel= RF_REG_0A else
				 reg0B when Bsel= RF_REG_0B else
				 reg0C when Bsel= RF_REG_0C else
				 reg0D when Bsel= RF_REG_0D else
				 reg0E when Bsel= RF_REG_0E else
				 reg0F when Bsel= RF_REG_0F else
				 reg10 when Bsel= RF_REG_10 else
				 reg11 when Bsel= RF_REG_11 else
				 reg12 when Bsel= RF_REG_12 else
				 reg13 when Bsel= RF_REG_13 else
				 reg14 when Bsel= RF_REG_14 else
				 reg15 when Bsel= RF_REG_15 else
				 reg16 when Bsel= RF_REG_16 else
				 reg17 when Bsel= RF_REG_17 else
				 reg18 when Bsel= RF_REG_18 else
				 reg19 when Bsel= RF_REG_19 else
				 reg1A when Bsel= RF_REG_1A else
				 reg1B when Bsel= RF_REG_1B else
				 reg1C when Bsel= RF_REG_1C else
				 reg1D when Bsel= RF_REG_1D else
				 reg1E when Bsel= RF_REG_1E else
				 reg1F when Bsel= RF_REG_1F else
				 (others=>'Z');
	--writting part
	
	process(Asel, Bsel, Dsel, Din, Strb, clk)
		begin
			if (rising_edge(clk) and Strb='1') then
		
				Case Dsel is
					when RF_Reg_01 => reg01 <= Din;
					when RF_Reg_02 => reg02 <= Din;
					when RF_Reg_03 => reg03 <= Din;
					when RF_Reg_04 => reg04 <= Din;
					when RF_Reg_05 => reg05 <= Din;
					when RF_Reg_06 => reg06 <= Din;
					when RF_Reg_07 => reg07 <= Din;
					when RF_Reg_08 => reg08 <= Din;
					when RF_Reg_09 => reg09 <= Din;
					when RF_Reg_0A => reg0A <= Din;
					when RF_Reg_0B => reg0B <= Din;
					when RF_Reg_0C => reg0C <= Din;
					when RF_Reg_0D => reg0D <= Din;
					when RF_Reg_0E => reg0E <= Din;
					when RF_Reg_0F => reg0F <= Din;
					when RF_Reg_10 => reg10 <= Din;
					when RF_Reg_11 => reg11 <= Din;
					when RF_Reg_12 => reg12 <= Din;
					when RF_Reg_13 => reg13 <= Din;
					when RF_Reg_14 => reg14 <= Din;
					when RF_Reg_15 => reg15 <= Din;
					when RF_Reg_16 => reg16 <= Din;
					when RF_Reg_17 => reg17 <= Din;
					when RF_Reg_18 => reg18 <= Din;
					when RF_Reg_19 => reg19 <= Din;
					when RF_Reg_1A => reg1A <= Din;
					when RF_Reg_1B => reg1B <= Din;
					when RF_Reg_1C => reg1C <= Din;
					when RF_Reg_1D => reg1D <= Din;
					when RF_Reg_1E => reg1E <= Din;
					when RF_Reg_1F => reg1F <= Din;
					when others    => reg00 <= (others => '0');
			
			end case;	
		
		end if;	
		
		
	end process;
	
End Architecture;	
