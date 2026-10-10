--------------------------------------------------------------------------------
-- EE 362 - Lab 8 REFERENCE SOLUTION  (TA only - do not publish)
--
-- NIAG : the complete Next Instruction Address Generator, six components.
--
-- Marking points:
--   * named association throughout
--   * one internal signal per inter-component wire
--   * PC and NSA driven from internal signals (an 'out' port cannot be read)
--   * Rtn is NSA - a wire with a better name, no hardware
--------------------------------------------------------------------------------

library ieee;
use ieee.std_logic_1164.all;

use work.NIAG_Pkg.all;

entity NIAG is
    generic (
        RESET_VEC : natural := 0
    );
    port (
        Index   : in  std_logic_vector(25 downto 0);
        Xtnd32  : in  std_logic_vector(31 downto 0);
        RegAddr : in  std_logic_vector(31 downto 0);
        Sel     : in  std_logic_vector(1 downto 0);
        Cond    : in  std_logic_vector(2 downto 0);
        Strb    : in  std_logic;
        Zero    : in  std_logic;
        Neg     : in  std_logic;
        Rst     : in  std_logic;
        clk     : in  std_logic;
        PC      : out std_logic_vector(31 downto 0);
        NSA     : out std_logic_vector(31 downto 0);
        Rtn     : out std_logic_vector(31 downto 0)
    );
end entity NIAG;

architecture structural of NIAG is

    -- One signal per wire between components.
    signal pc_i     : std_logic_vector(31 downto 0);
    signal nsa_i    : std_logic_vector(31 downto 0);
    signal rel_i    : std_logic_vector(31 downto 0);
    signal abslt_i  : std_logic_vector(31 downto 0);
    signal taken_i  : std_logic;
    signal nextpc_i : std_logic_vector(31 downto 0);

begin

    U_PC : entity work.NIAG_Reg
        generic map (RESET_VEC => RESET_VEC)
        port map (
            NextPC => nextpc_i,
            Strb   => Strb,
            Rst    => Rst,
            clk    => clk,
            PC     => pc_i
        );

    U_NSA : entity work.NIAG_NSA
        port map (
            PC  => pc_i,
            NSA => nsa_i
        );

    U_REL : entity work.NIAG_Rel
        port map (
            NSA    => nsa_i,
            Xtnd32 => Xtnd32,
            Rel    => rel_i
        );

    U_ABS : entity work.NIAG_Abslt
        port map (
            NSA   => nsa_i,
            Index => Index,
            Abslt => abslt_i
        );

    U_COND : entity work.NIAG_Cond
        port map (
            Cond  => Cond,
            Zero  => Zero,
            Neg   => Neg,
            Taken => taken_i
        );

    U_MUX : entity work.NIAG_MUX
        port map (
            Sel     => Sel,
            Taken   => taken_i,
            NSA     => nsa_i,
            Rel     => rel_i,
            RegAddr => RegAddr,
            Abslt   => abslt_i,
            NextPC  => nextpc_i
        );

    PC  <= pc_i;
    NSA <= nsa_i;
    Rtn <= nsa_i;                       -- the return address IS PC+4

end architecture structural;
