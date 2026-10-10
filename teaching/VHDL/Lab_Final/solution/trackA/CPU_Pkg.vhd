--------------------------------------------------------------------------------
-- EE 362 - Computer Organization Laboratory
-- Labs 10-12 - Instruction encodings and control signals
--                                       *** PROVIDED COMPLETE - DO NOT EDIT ***
--
-- ============================================================================
-- WHAT A RECORD IS, AND WHY WE NEED ONE
-- ============================================================================
-- Your decoder produces SIXTEEN control signals. Passing sixteen separate ports
-- through every entity would be unreadable and would guarantee a wiring error.
--
-- A VHDL RECORD bundles related signals into one named type, exactly like a
-- struct. One port carries all sixteen:
--
--     signal Ctrl : CTRL_REC;
--     Ctrl.RF_strb <= RF_STRB_STROBE;      -- set one field
--     RegFileStrobe <= Ctrl.RF_strb;       -- read one field
--
-- In hardware nothing changes - a record is sixteen wires either way. It only
-- changes how the source reads, and at sixteen signals that is the difference
-- between a design you can debug and one you cannot.
--
-- ============================================================================
-- THE EIGHT INSTRUCTIONS
-- ============================================================================
-- This CPU implements exactly eight instructions: the ones its program uses.
-- Not forty. If the ISA manual intimidates you, remember that the CONTROL TABLE
-- is the specification, and it has eight rows.
--------------------------------------------------------------------------------

library ieee;
use ieee.std_logic_1164.all;

package CPU_Pkg is

    ----------------------------------------------------------------------------
    -- Opcode field values (instruction bits 31 downto 26)
    ----------------------------------------------------------------------------
    constant OP_SPECIAL : std_logic_vector(5 downto 0) := "000000";  -- R-type
    constant OP_J       : std_logic_vector(5 downto 0) := "000010";
    constant OP_BLEZ    : std_logic_vector(5 downto 0) := "000110";
    constant OP_ADDI    : std_logic_vector(5 downto 0) := "001000";
    constant OP_LUI     : std_logic_vector(5 downto 0) := "001111";
    constant OP_ORI     : std_logic_vector(5 downto 0) := "001101";  -- Track A
    constant OP_LW      : std_logic_vector(5 downto 0) := "100011";
    constant OP_SW      : std_logic_vector(5 downto 0) := "101011";

    ----------------------------------------------------------------------------
    -- Func field values (instruction bits 5 downto 0), only for OP_SPECIAL
    ----------------------------------------------------------------------------
    constant FN_SLL : std_logic_vector(5 downto 0) := "000000";
    constant FN_ADD : std_logic_vector(5 downto 0) := "100000";
    constant FN_SUB : std_logic_vector(5 downto 0) := "100010";      -- Track A, harder variant

    ----------------------------------------------------------------------------
    -- ALU function codes (subset used by these eight instructions)
    ----------------------------------------------------------------------------
    constant ALU_FUNC_ADD : std_logic_vector(4 downto 0) := "00000";
    constant ALU_FUNC_SLL : std_logic_vector(4 downto 0) := "10010";
    constant ALU_FUNC_SUB : std_logic_vector(4 downto 0) := "00001";  -- Track A
    constant ALU_FUNC_OR  : std_logic_vector(4 downto 0) := "01101";  -- Track A

    ----------------------------------------------------------------------------
    -- Control signal values.  Named, so a typo is a compile error.
    ----------------------------------------------------------------------------
    constant ALU_ASEL_AOUT  : std_logic := '0';   -- ALU A input from register file
    constant ALU_ASEL_IMMED : std_logic := '1';   -- ALU A input from the immediate

    constant ALU_SSEL_SA    : std_logic := '0';   -- shift amount from the sa field
    constant ALU_SSEL_BOUT  : std_logic := '1';   -- shift amount from register B

    constant IR_XSEL_ZERO   : std_logic := '0';   -- zero-extend the immediate
    constant IR_XSEL_SIGN   : std_logic := '1';   -- sign-extend it

    constant IR_XLSFT_NONE  : std_logic := '0';   -- do not scale
    constant IR_XLSFT_TWO   : std_logic := '1';   -- scale by 4 (branch offsets)

    constant IR_STRB_HOLD   : std_logic := '0';
    constant IR_STRB_STROBE : std_logic := '1';   -- latch the instruction

    constant DM_EN_DISABLE  : std_logic := '0';
    constant DM_EN_ENABLE   : std_logic := '1';

    constant DM_RW_WR       : std_logic := '0';   -- NOTE: '1' is READ
    constant DM_RW_RD       : std_logic := '1';

    constant DM_STRB_HOLD   : std_logic := '0';
    constant DM_STRB_STORE  : std_logic := '1';

    constant NIAG_SEL_NSA   : std_logic_vector(1 downto 0) := "00";
    constant NIAG_SEL_REL   : std_logic_vector(1 downto 0) := "01";
    constant NIAG_SEL_REG   : std_logic_vector(1 downto 0) := "10";
    constant NIAG_SEL_ABS   : std_logic_vector(1 downto 0) := "11";

    constant NIAG_COND_NONE : std_logic_vector(2 downto 0) := "000";
    constant NIAG_COND_EQ   : std_logic_vector(2 downto 0) := "001";
    constant NIAG_COND_NEQ  : std_logic_vector(2 downto 0) := "010";
    constant NIAG_COND_GTZ  : std_logic_vector(2 downto 0) := "011";
    constant NIAG_COND_GEZ  : std_logic_vector(2 downto 0) := "100";
    constant NIAG_COND_LTZ  : std_logic_vector(2 downto 0) := "101";
    constant NIAG_COND_LEZ  : std_logic_vector(2 downto 0) := "110";

    constant NIAG_STRB_HOLD   : std_logic := '0';
    constant NIAG_STRB_STROBE : std_logic := '1';  -- advance the PC

    constant RF_DSEL_ALU    : std_logic_vector(1 downto 0) := "00";  -- write ALU result
    constant RF_DSEL_MEM    : std_logic_vector(1 downto 0) := "01";  -- write memory data
    constant RF_DSEL_RET    : std_logic_vector(1 downto 0) := "10";  -- write return address

    constant RF_WSEL_RD     : std_logic_vector(1 downto 0) := "00";  -- destination is rd
    constant RF_WSEL_RT     : std_logic_vector(1 downto 0) := "01";  -- destination is rt
    constant RF_WSEL_R31    : std_logic_vector(1 downto 0) := "10";  -- destination is $31

    constant RF_STRB_HOLD   : std_logic := '0';
    constant RF_STRB_STROBE : std_logic := '1';   -- write the register file

    constant RF_OE_HIZ      : std_logic := '0';
    constant RF_OE_DRIVE    : std_logic := '1';   -- drive the memory data bus

    ----------------------------------------------------------------------------
    -- The control bundle: everything the decoder produces, in one type.
    ----------------------------------------------------------------------------
    type CTRL_REC is record
        ALU_func  : std_logic_vector(4 downto 0);   -- which ALU operation
        ALU_Asel  : std_logic;                      -- ALU A input source
        ALU_Ssel  : std_logic;                      -- shift amount source
        IR_Xsel   : std_logic;                      -- sign or zero extend
        IR_Xlsft  : std_logic;                      -- scale the immediate by 4
        IR_strb   : std_logic;                      -- latch the instruction
        DM_en     : std_logic;                      -- data memory enable
        DM_rw     : std_logic;                      -- data memory read/write
        DM_strb   : std_logic;                      -- data memory store strobe
        NIAG_sel  : std_logic_vector(1 downto 0);   -- next PC source
        NIAG_cond : std_logic_vector(2 downto 0);   -- branch condition
        NIAG_strb : std_logic;                      -- advance the PC
        RF_Dsel   : std_logic_vector(1 downto 0);   -- register write data source
        RF_Wsel   : std_logic_vector(1 downto 0);   -- register write destination
        RF_strb   : std_logic;                      -- write the register file
        RF_oe     : std_logic;                      -- drive the memory data bus
    end record CTRL_REC;

    ----------------------------------------------------------------------------
    -- THE DEFAULT CONTROL BUNDLE.
    --
    -- Every instruction starts from this and overrides only what it needs.
    -- That is not a convenience - it is what stops the synthesiser inferring
    -- sixteen latches, and it is what makes an unrecognised opcode SAFE:
    -- no register write, no memory write, PC advances normally.
    ----------------------------------------------------------------------------
    constant CTRL_DEFAULT : CTRL_REC := (
        ALU_func  => ALU_FUNC_ADD,
        ALU_Asel  => ALU_ASEL_AOUT,
        ALU_Ssel  => ALU_SSEL_SA,
        IR_Xsel   => IR_XSEL_ZERO,
        IR_Xlsft  => IR_XLSFT_NONE,
        IR_strb   => IR_STRB_STROBE,
        DM_en     => DM_EN_DISABLE,
        DM_rw     => DM_RW_RD,
        DM_strb   => DM_STRB_HOLD,
        NIAG_sel  => NIAG_SEL_NSA,
        NIAG_cond => NIAG_COND_NONE,
        NIAG_strb => NIAG_STRB_STROBE,
        RF_Dsel   => RF_DSEL_ALU,
        RF_Wsel   => RF_WSEL_RD,
        RF_strb   => RF_STRB_HOLD,      -- do NOT write a register by default
        RF_oe     => RF_OE_HIZ          -- do NOT drive the memory bus by default
    );

end package CPU_Pkg;
