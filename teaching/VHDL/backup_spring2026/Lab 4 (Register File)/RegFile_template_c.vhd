library IEEE;
use IEEE.STD_LOGIC_1164.ALL;
use IEEE.NUMERIC_STD.ALL;

-- Import EE362Decoder package
-- This package contains the RF_REG_00 constant used for register 0.
use work.DecodeLogic_Pkg.all;

-- ============================================================================
--  RegFile
-- ----------------------------------------------------------------------------
--  32 x 32 tri-ported register file
--
--  Ports:
--      Asel : selects which register drives Aout
--      Bsel : selects which register drives Bout
--      Dsel : selects which register receives Din on a write
--      Din  : 32-bit data to be written
--      Strb : write strobe; write occurs on rising edge
--      Aout : 32-bit read port A
--      Bout : 32-bit read port B
--
--  Required behavior from the lab:
--      1. 32 registers, each 32 bits wide
--      2. Register 0 is hardwired to zero
--      3. Two independent read ports
--      4. One write port, active on rising edge of Strb
-- ============================================================================

entity RegFile is
    port(
        Asel : in  STD_LOGIC_VECTOR(4 downto 0);   -- Read-select for output A
        Bsel : in  STD_LOGIC_VECTOR(4 downto 0);   -- Read-select for output B
        Dsel : in  STD_LOGIC_VECTOR(4 downto 0);   -- Write-select register number
        Din  : in  STD_LOGIC_VECTOR(31 downto 0);  -- Data input for writes
        Strb : in  STD_LOGIC;                      -- Write strobe / clock edge
        Aout : out STD_LOGIC_VECTOR(31 downto 0);  -- Data output A
        Bout : out STD_LOGIC_VECTOR(31 downto 0)   -- Data output B
    );
end entity RegFile;

architecture Behavioral of RegFile is

    -- Create an array type representing 32 registers, each 32 bits wide.
    type reg_array_t is array (0 to 31) of STD_LOGIC_VECTOR(31 downto 0);

    -- Storage for the actual register file.
    -- Initialize every register to zero for simulation startup.
    signal Regs : reg_array_t := (others => (others => '0'));

    -- ------------------------------------------------------------------------
    -- Function: is_binary
    -- Purpose :
    --      Returns TRUE only if every bit in the vector is either '0' or '1'.
    --      This prevents conversion problems if a selector contains U, X, Z, etc.
    -- ------------------------------------------------------------------------
    function is_binary(s : STD_LOGIC_VECTOR) return boolean is
    begin
        for i in s'range loop
            if (s(i) /= '0') and (s(i) /= '1') then
                return false;
            end if;
        end loop;
        return true;
    end function;

begin

    -- ------------------------------------------------------------------------
    -- Write process
    -- ------------------------------------------------------------------------
    -- A register write happens only on the rising edge of Strb.
    -- Dsel picks the destination register.
    -- Din is copied into that register.
    --
    -- Special rule:
    --   Register 0 must always remain zero.
    --   Any write to register 0 is ignored.
    -- ------------------------------------------------------------------------
    process(Strb)
        variable idx : integer;
    begin
        if rising_edge(Strb) then

            -- Force register 0 to remain zero at every write edge.
            -- This guarantees R0 can never hold any nonzero value.
            Regs(0) <= (others => '0');

            -- Only convert Dsel to an integer if it is a valid binary value.
            if is_binary(Dsel) then
                idx := to_integer(unsigned(Dsel));

                -- Ignore writes to register 0.
                if Dsel /= RF_REG_00 then
                    Regs(idx) <= Din;
                end if;
            end if;
        end if;
    end process;

    -- ------------------------------------------------------------------------
    -- Read port A
    -- ------------------------------------------------------------------------
    -- Aout continuously reflects the contents of the register selected by Asel.
    -- This is an asynchronous read.
    --
    -- If Asel is invalid (contains U/X/Z/etc.), return all zeros so the design
    -- stays safe in simulation.
    --
    -- Register 0 is always read as zero.
    -- ------------------------------------------------------------------------
    process(Asel, Regs)
    begin
        if not is_binary(Asel) then
            Aout <= (others => '0');
        elsif Asel = RF_REG_00 then
            Aout <= (others => '0');
        else
            Aout <= Regs(to_integer(unsigned(Asel)));
        end if;
    end process;

    -- ------------------------------------------------------------------------
    -- Read port B
    -- ------------------------------------------------------------------------
    -- Bout continuously reflects the contents of the register selected by Bsel.
    -- This is also an asynchronous read.
    --
    -- If Bsel is invalid, return all zeros.
    -- Register 0 is always read as zero.
    -- ------------------------------------------------------------------------
    process(Bsel, Regs)
    begin
        if not is_binary(Bsel) then
            Bout <= (others => '0');
        elsif Bsel = RF_REG_00 then
            Bout <= (others => '0');
        else
            Bout <= Regs(to_integer(unsigned(Bsel)));
        end if;
    end process;

end architecture Behavioral;