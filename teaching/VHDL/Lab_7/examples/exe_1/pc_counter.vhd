--------------------------------------------------------------------------------
-- EE 362 - Computer Organization Laboratory
-- Lab 7, Example 1 - The program counter, at 8 bits so you can read it
--
-- A program counter is a REGISTER with an adder in front of it. That is all it
-- is. You built the register in Lab 2; the adder is one line.
--
--   PC+ = Rst  ? RESET_VEC
--       : Ld   ? NextPC          <- from the NIAG multiplexer, in Lab 8
--       :        PC              <- hold
--
-- WHY THE PC IS A REGISTER AND NOT A COUNTER
--   A counter only counts. A program counter must also JUMP - to a branch
--   target, to a subroutine, back from one. So it is a loadable register, and
--   "count" is just the special case of loading PC+4.
--
--   That is why Lab 8 replaces this +4 with a multiplexer over five possible
--   next addresses. Sequential execution is not a separate mechanism; it is
--   one input of the mux.
--
-- WHY THE RESET VECTOR MATTERS
--   On reset the PC must go somewhere DEFINED. If it powers up at 'U' the CPU
--   fetches garbage forever and every waveform you look at is meaningless.
--   Here, and in your CPU, the reset vector is address 0.
--------------------------------------------------------------------------------

library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

entity pc_counter is
    generic (
        RESET_VEC : natural := 0
    );
    port (
        NextPC : in  std_logic_vector(7 downto 0);   -- where to go if loading
        Ld     : in  std_logic;                      -- load enable
        Rst    : in  std_logic;                      -- asynchronous reset
        clk    : in  std_logic;
        PC     : out std_logic_vector(7 downto 0);
        NSA    : out std_logic_vector(7 downto 0)    -- next sequential address
    );
end entity pc_counter;

architecture rtl of pc_counter is

    signal pc_reg : std_logic_vector(7 downto 0)
                  := std_logic_vector(to_unsigned(RESET_VEC, 8));

begin

    -- The register. This is your Lab 2 RegN, at 8 bits.
    process (clk, Rst)
    begin
        if Rst = '1' then
            pc_reg <= std_logic_vector(to_unsigned(RESET_VEC, 8));
        elsif rising_edge(clk) then
            if Ld = '1' then
                pc_reg <= NextPC;
            end if;
            -- no else: not loading means hold
        end if;
    end process;

    PC <= pc_reg;

    -- The adder. Instructions are 4 bytes, so the next one is 4 bytes along.
    -- Note this is COMBINATIONAL and sits outside the register: NSA is
    -- available during the cycle, not one cycle later. The CPU needs it now.
    NSA <= std_logic_vector(unsigned(pc_reg) + 4);

end architecture rtl;
