--------------------------------------------------------------------------------
-- EE 362 - Computer Organization Laboratory
-- Lab 10, Example 3 - Sixteen latches, and a CPU with a memory of its own
--
-- This file contains TWO decoders. They differ in one line.
--
--   good_decode  assigns the complete default FIRST, then overrides.
--   bad_decode   assigns only the fields each instruction "needs".
--
-- bad_decode compiles. It passes any test that feeds it one instruction at a
-- time. And it is catastrophically wrong.
--
-- ============================================================================
-- WHY
-- ============================================================================
-- If a field is not assigned on some path through the process, the synthesiser
-- must keep its previous value - so it builds a LATCH. Sixteen fields, sixteen
-- latches, and now the control signals depend on WHICH INSTRUCTION RAN BEFORE.
--
-- The symptom in Lab 12 is the worst kind:
--   * each instruction works when tested alone
--   * the program still fails
--   * and it fails DIFFERENTLY depending on instruction order
--
-- You have met this exact bug twice already, at smaller scale:
--   Lab 1  the missing 'else'      - there we WANTED the latch
--   Lab 3  the missing 'when others' - there we did not
--   Lab 10 sixteen at once
--
-- Same sentence every time: NO ASSIGNMENT MEANS HOLD THE PREVIOUS VALUE.
--
-- The testbench demonstrates it by running ADDI and then LUI, and showing that
-- bad_decode leaves ADDI's sign-extension setting switched on during LUI - so
-- LUI loads the wrong value, but only when it follows an ADDI.
--------------------------------------------------------------------------------

library ieee;
use ieee.std_logic_1164.all;

use work.CPU_Pkg.all;

--------------------------------------------------------------------------------
-- THE CORRECT ONE: default first, then override.
--------------------------------------------------------------------------------
entity good_decode is
    port (
        Instr : in  std_logic_vector(31 downto 0);
        Ctrl  : out CTRL_REC
    );
end entity good_decode;

architecture rtl of good_decode is
    signal opcode : std_logic_vector(5 downto 0);
begin
    opcode <= Instr(31 downto 26);

    process (opcode)
        variable c : CTRL_REC;
    begin
        c := CTRL_DEFAULT;              -- <<< every field defined, every path

        case opcode is
            when OP_ADDI =>
                c.ALU_Asel := ALU_ASEL_IMMED;
                c.IR_Xsel  := IR_XSEL_SIGN;
                c.RF_Wsel  := RF_WSEL_RT;
                c.RF_strb  := RF_STRB_STROBE;

            when OP_LUI =>
                c.ALU_Asel := ALU_ASEL_IMMED;
                c.IR_Xsel  := IR_XSEL_ZERO;     -- explicitly ZERO-extend
                c.RF_Wsel  := RF_WSEL_RT;
                c.RF_strb  := RF_STRB_STROBE;

            when others =>
                null;                   -- keep the default
        end case;

        Ctrl <= c;
    end process;
end architecture rtl;


--------------------------------------------------------------------------------
-- THE BROKEN ONE: no default. Assigns only what each instruction "needs".
--
-- Note that LUI does not set IR_Xsel at all - the author reasoned that LUI
-- zero-extends and zero is "the normal case". With no default, "not assigned"
-- means "keep whatever it was", so LUI inherits ADDI's sign-extension.
--------------------------------------------------------------------------------
library ieee;
use ieee.std_logic_1164.all;

use work.CPU_Pkg.all;

entity bad_decode is
    port (
        Instr : in  std_logic_vector(31 downto 0);
        Ctrl  : out CTRL_REC
    );
end entity bad_decode;

architecture broken of bad_decode is
    signal opcode : std_logic_vector(5 downto 0);
begin
    opcode <= Instr(31 downto 26);

    process (opcode)
        variable c : CTRL_REC;
    begin
        -- NO DEFAULT ASSIGNMENT. This is the bug.

        case opcode is
            when OP_ADDI =>
                c.ALU_Asel := ALU_ASEL_IMMED;
                c.IR_Xsel  := IR_XSEL_SIGN;
                c.RF_Wsel  := RF_WSEL_RT;
                c.RF_strb  := RF_STRB_STROBE;

            when OP_LUI =>
                c.ALU_Asel := ALU_ASEL_IMMED;
                -- IR_Xsel not assigned: "LUI zero-extends, and zero is normal"
                c.RF_Wsel  := RF_WSEL_RT;
                c.RF_strb  := RF_STRB_STROBE;

            when others =>
                c.RF_strb  := RF_STRB_HOLD;
        end case;

        Ctrl <= c;
    end process;
end architecture broken;
