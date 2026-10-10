library IEEE;
use IEEE.STD_LOGIC_1164.ALL;

use work.ALU_Pkg.all;
use work.DecodeLogic_Pkg.all;
use work.NIAG_Pkg.all;

-- =========================================================
-- NIAG_MUX
-- Next Instruction Address Generation:
-- Address Selection MUX
--
-- Purpose:
-- This component chooses which next instruction address
-- will be sent to the Program Counter.
--
-- Main idea:
-- Several possible next addresses are computed in parallel:
--
--   1. NxtAdrs   -> next sequential address
--   2. RelAdrs   -> relative branch address
--   3. RegAdrs   -> register-based address
--   4. AbsltAdrs -> absolute jump address
--
-- The signal Sel selects which addressing mode is used.
--
-- For the relative case, the final choice also depends on
-- the branch condition. If the condition is true, the CPU
-- takes RelAdrs. If the condition is false, it continues
-- with NxtAdrs.
--
-- ---------------------------------------------------------
-- Branch condition examples:
--
-- Cond = NIAG_COND_EQ
--     take branch if ALU_zero = '1'
--
-- Cond = NIAG_COND_NEQ
--     take branch if ALU_zero = '0'
--
-- Cond = NIAG_COND_GTZ
--     take branch if result > 0
--
-- ---------------------------------------------------------
-- Example:
--
-- Suppose:
--   Sel       = NIAG_SEL_REL
--   Cond      = NIAG_COND_EQ
--   Stat.ALU_zero = '1'
--   NxtAdrs   = x"00000024"
--   RelAdrs   = x"00000040"
--
-- Then:
--   take_rel  = '1'
--   InstrAdrs = x"00000040"
--
-- But if Stat.ALU_zero = '0', then:
--   take_rel  = '0'
--   InstrAdrs = x"00000024"
--
-- So this block decides the final next instruction address.
-- =========================================================

entity NIAG_MUX is
    port (
        -- Next sequential address
        NxtAdrs   : in  STD_LOGIC_VECTOR(31 downto 0);

        -- Absolute jump address
        AbsltAdrs : in  STD_LOGIC_VECTOR(31 downto 0);

        -- Relative branch address
        RelAdrs   : in  STD_LOGIC_VECTOR(31 downto 0);

        -- Register-based address
        RegAdrs   : in  STD_LOGIC_VECTOR(31 downto 0);

        -- Branch condition control
        Cond      : in  STD_LOGIC_VECTOR(2 downto 0);

        -- Address source select
        Sel       : in  STD_LOGIC_VECTOR(1 downto 0);

        -- ALU status flags
        Stat      : in  STAT_SIGNL_REC;

        -- Final next instruction address
        InstrAdrs : out STD_LOGIC_VECTOR(31 downto 0)
    );
end NIAG_MUX;

architecture rtl of NIAG_MUX is

    -- Internal signal indicating whether the relative branch
    -- should be taken.
    signal take_rel : STD_LOGIC;

begin

    -- =====================================================
    -- TODO:
    -- Evaluate the branch condition.
    --
    -- Use the official NIAG condition encodings:
    --
    -- NIAG_COND_NONE : unconditional relative selection
    -- NIAG_COND_EQ   : take branch if ALU_zero = '1'
    -- NIAG_COND_NEQ  : take branch if ALU_zero = '0'
    -- NIAG_COND_GTZ  : take branch if result > 0
    -- NIAG_COND_GEZ  : take branch if result >= 0
    -- NIAG_COND_LTZ  : take branch if result < 0
    -- NIAG_COND_LEZ  : take branch if result <= 0
    --
    -- Complete the conditional assignment below.
    -- =====================================================

    take_rel <= '1' when Cond = NIAG_COND_NONE else
                Stat.ALU_zero when Cond = NIAG_COND_EQ else
                not Stat.ALU_zero when Cond = NIAG_COND_NEQ else
                ((not Stat.ALU_sign) and (not Stat.ALU_zero)) when Cond = NIAG_COND_GTZ else
                (not Stat.ALU_sign) when Cond = NIAG_COND_GEZ else
                Stat.ALU_sign when Cond = NIAG_COND_LTZ else
                (Stat.ALU_sign or Stat.ALU_zero) when Cond = NIAG_COND_LEZ else
                '0';

    -- =====================================================
    -- TODO:
    -- Select the final next instruction address.
    --
    -- Cases:
    --   NIAG_SEL_NSA -> use NxtAdrs
    --   NIAG_SEL_REL -> use RelAdrs if take_rel = '1',
    --                   otherwise use NxtAdrs
    --   NIAG_SEL_REG -> use RegAdrs
    --   NIAG_SEL_ABS -> use AbsltAdrs
    --
    -- If no valid selection is detected, use NxtAdrs as the
    -- default.
    -- =====================================================

    process(NxtAdrs, AbsltAdrs, RelAdrs, RegAdrs, Sel, take_rel)
    begin
        case Sel is
            when NIAG_SEL_NSA =>
                InstrAdrs <= NxtAdrs;

            when NIAG_SEL_REL =>
                if take_rel = '1' then
                    InstrAdrs <= RelAdrs;
                else
                    InstrAdrs <= NxtAdrs;
                end if;

            when NIAG_SEL_REG =>
                InstrAdrs <= RegAdrs;

            when NIAG_SEL_ABS =>
                InstrAdrs <= AbsltAdrs;

            when others =>
                InstrAdrs <= NxtAdrs;
        end case;
    end process;

end rtl;