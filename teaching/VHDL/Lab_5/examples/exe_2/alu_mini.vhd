--------------------------------------------------------------------------------
-- EE 362 - Computer Organization Laboratory
-- Lab 5, Example 2 - What an ALU actually IS
--
-- An ALU is not a mysterious block. It is:
--
--     every function computed at once, and a MULTIPLEXER that picks one.
--
-- All the units run in parallel, all the time, on the same inputs. The function
-- code does not tell the hardware what to compute - it tells the multiplexer
-- which already-computed answer to forward. There is no "choosing" and then
-- "doing"; the doing already happened.
--
-- You built the multiplexer in Lab 3. That is genuinely all the new structure
-- there is here.
--
-- This example wires two units and a 2-to-1 mux, structurally, so you can see
-- it. Your assignment has sixteen operations, and at that size writing sixteen
-- entities and a 16-to-1 mux by hand is pointless typing - you will use a
-- 'case' instead.
--
-- BUT THE CASE IS STILL THE MULTIPLEXER. Look at your RTL Viewer after the
-- assignment: the synthesiser draws a mux. The case statement is how you SPELL
-- a multiplexer when there are too many inputs to wire by hand.
--------------------------------------------------------------------------------

library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

entity alu_and is
    port (
        Ain  : in  std_logic_vector(31 downto 0);
        Bin  : in  std_logic_vector(31 downto 0);
        Rout : out std_logic_vector(31 downto 0)
    );
end entity alu_and;

architecture rtl of alu_and is
begin
    Rout <= Ain and Bin;                -- bitwise, all 32 bits at once
end architecture rtl;


--------------------------------------------------------------------------------
-- The mini ALU: two function units and a multiplexer.
--------------------------------------------------------------------------------
library ieee;
use ieee.std_logic_1164.all;

entity alu_mini is
    port (
        Ain  : in  std_logic_vector(31 downto 0);
        Bin  : in  std_logic_vector(31 downto 0);
        Func : in  std_logic;                       -- '0' = add, '1' = and
        Rout : out std_logic_vector(31 downto 0);
        Zero : out std_logic;
        Neg  : out std_logic
    );
end entity alu_mini;

architecture structural of alu_mini is

    signal add_result : std_logic_vector(31 downto 0);
    signal and_result : std_logic_vector(31 downto 0);
    signal result     : std_logic_vector(31 downto 0);

    -- The adder computes its own flags, but we ignore them here: the flags
    -- must describe the SELECTED result, not one particular unit's result.
    signal add_z, add_n, add_c : std_logic;

begin

    -- Both units run on every input, every time. Nothing is gated off.
    U_ADD : entity work.alu_add
        port map (Ain => Ain, Bin => Bin, Rout => add_result,
                  Zero => add_z, Neg => add_n, Cout => add_c);

    U_AND : entity work.alu_and
        port map (Ain => Ain, Bin => Bin, Rout => and_result);

    -- THE MULTIPLEXER. This is the ALU's function selector, and it is exactly
    -- the Mux2 you wrote in Lab 3.
    result <= and_result when Func = '1' else add_result;

    Rout <= result;

    -- FLAGS ARE COMPUTED ON THE SELECTED RESULT, after the multiplexer.
    -- This is a real design decision and students get it wrong: if you took the
    -- adder's Zero flag directly, then an AND that produced zero would report
    -- Zero = '0'. The flags describe what the ALU OUTPUT is, not what any one
    -- unit happened to compute.
    Zero <= '1' when result = (result'range => '0') else '0';
    Neg  <= result(31);

end architecture structural;
