--------------------------------------------------------------------------------
-- EE 362 - Computer Organization Laboratory
-- Lab 5 - Assignment: the Arithmetic Logic Unit
--
-- YOUR NAME  :
-- SECTION    :  Monday / Tuesday
-- DATE       :
--
-- WHAT THIS IS
--   Sixteen operations and a multiplexer. Example 2 wired two units and a mux
--   structurally so you could see it; at sixteen operations that becomes
--   pointless typing, so you write a 'case' instead. THE CASE IS STILL THE
--   MULTIPLEXER - check your RTL Viewer afterwards and you will see one drawn.
--
-- WHERE TO SPEND YOUR TIME
--   Ten of these are one line each. Do those first, in five minutes, and get
--   the wrapper compiling. Then spend the rest of the session on the four that
--   are actually interesting:
--
--       SRA    - the sign-filling shift.  Example 3 exists for this.
--       SOLS   - signed set-on-less.      Needs a signed comparison.
--       SOLU   - unsigned set-on-less.    Same operands, different answer.
--       flags  - computed on the SELECTED result, after the mux (Example 2).
--
-- THE OPERATIONS
--
--   code            Rout                         note
--   ------------    -------------------------    ---------------------------
--   ALU_FUNC_ADD    Ain + Bin                    GIVEN below
--   ALU_FUNC_SUB    Ain - Bin
--   ALU_FUNC_NEG    0 - Bin                      negate the B operand
--   ALU_FUNC_AND    Ain and Bin                  GIVEN below
--   ALU_FUNC_NAND   not (Ain and Bin)
--   ALU_FUNC_OR     Ain or Bin
--   ALU_FUNC_NOR    not (Ain or Bin)
--   ALU_FUNC_XOR    Ain xor Bin
--   ALU_FUNC_XNOR   not (Ain xor Bin)
--   ALU_FUNC_NOT    not Bin                      one operand, and it is B
--   ALU_FUNC_SLL    Ain shifted left  by Shft    fill with '0'
--   ALU_FUNC_SLA    same as SLL                  left shifts have one answer
--   ALU_FUNC_SRL    Ain shifted right by Shft    fill with '0'
--   ALU_FUNC_SRA    Ain shifted right by Shft    fill with the SIGN BIT
--   ALU_FUNC_SOLS   1 if Ain <  Bin signed,   else 0
--   ALU_FUNC_SOLU   1 if Ain <  Bin unsigned, else 0
--
-- SET ON LESS THAN - read this before you write it
--   The naive hardware answer is "subtract and look at the sign bit". That is
--   wrong, and it is wrong in an interesting way: if the subtraction OVERFLOWS,
--   the sign bit lies. The correct hardware equation is
--
--       SOLS = R(31) XOR V          where R = Ain - Bin and V is signed overflow
--
--   In VHDL you do not have to build that by hand. numeric_std's comparison
--   operators are already correct:
--
--       if signed(Ain) < signed(Bin) then ...
--
--   The synthesiser turns that into the overflow-corrected comparison. Use the
--   operator - and EXPLAIN THE EQUATION IN YOUR REPORT. Knowing why the naive
--   version fails is the point; retyping it is not.
--
--   SOLS and SOLU give DIFFERENT answers on the same bits:
--       Ain = 0xFFFFFFFF, Bin = 0x00000001
--       signed:    -1 < 1          -> 1
--       unsigned:  4294967295 < 1  -> 0
--   Your testbench must include that pair.
--
-- THE FLAGS
--   Zero = 1 when every bit of the SELECTED result is '0'
--   Neg  = bit 31 of the SELECTED result
--   Compute both AFTER the case, on the final result. Example 2 shows why.
--
-- THE DEFAULT
--   'when others' must assign something. An unimplemented code should produce
--   a defined, harmless value - not a latch.
--------------------------------------------------------------------------------

library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

use work.ALU_Pkg.all;                       -- the function codes

entity ALU is
    port (
        Ain  : in  std_logic_vector(31 downto 0);
        Bin  : in  std_logic_vector(31 downto 0);
        Func : in  std_logic_vector(4 downto 0);    -- ALU_FUNC_* from the package
        Shft : in  std_logic_vector(4 downto 0);    -- shift amount, from ALUsftMUX
        Rout : out std_logic_vector(31 downto 0);
        Zero : out std_logic;
        Neg  : out std_logic
    );
end entity ALU;

architecture rtl of ALU is

    -- The selected result, before it leaves the entity. The flags are computed
    -- from THIS, which is what makes them describe the ALU's actual output.
    signal result : std_logic_vector(31 downto 0);

    -- Convert the shift amount once. You cannot shift by a vector.
    signal amount : natural range 0 to 31;

begin

    amount <= to_integer(unsigned(Shft));

    ----------------------------------------------------------------------------
    -- The function multiplexer.
    --
    -- Note the sensitivity list: every signal read inside. Get this wrong and
    -- you are back in Lab 1.
    ----------------------------------------------------------------------------
    process (Ain, Bin, Func, amount)
    begin

        case Func is

            -- ---- GIVEN, as the template ------------------------------------
            when ALU_FUNC_ADD =>
                result <= std_logic_vector(unsigned(Ain) + unsigned(Bin));

            when ALU_FUNC_AND =>
                result <= Ain and Bin;

            -- ---- TODO 1: the easy ones. Ten lines, five minutes. ------------
            -- SUB, NEG, NAND, OR, NOR, XOR, XNOR, NOT, SLL, SLA, SRL


            -- ---- TODO 2: SRA. Read Example 3 first. -------------------------
            -- Remember: the TYPE decides the fill, not the function name.


            -- ---- TODO 3: SOLS and SOLU. -------------------------------------
            -- Result is the 32-bit value 1 or the 32-bit value 0.
            -- x"00000001" and x"00000000" are the easiest way to write those.


            -- ---- TODO 4: the default ---------------------------------------
            when others =>
                result <= (others => '0');

        end case;

    end process;

    Rout <= result;

    -- TODO 5: the flags, computed on 'result' - not on any one operation.
    --         Zero is '1' only when every bit of result is '0'.
    --         Neg is the top bit. No computation needed.


end architecture rtl;
