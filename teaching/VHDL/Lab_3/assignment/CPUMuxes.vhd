--------------------------------------------------------------------------------
-- EE 362 - Computer Organization Laboratory
-- Lab 3 - Assignment, Part 3 of 3
--
-- The four multiplexers your CPU actually needs, built by INSTANTIATING the
-- generic Mux2 and Mux3 at the right widths.
--
-- YOUR NAME  :
-- SECTION    :  Monday / Tuesday
-- DATE       :
--
--   entity      width  sel   role on the CPU block diagram
--   ---------------------------------------------------------------------------
--   MUX2x5       5      1    DselMUX   - register write-destination select
--   MUX3x5       5      2    (spare 5-bit selector)
--   MUX2x32     32      1    ALUinMUX  - ALU A-input: register or immediate
--   MUX3x32     32      2    DinMUX    - register write data: ALU / memory /
--                                        return address
--
-- Find all four on the CPU diagram and mark them. That annotated diagram is a
-- required figure in your report - it is the first time you see the whole
-- datapath, and from Lab 7 onward you will be reading it constantly.
--
-- MUX2x5 IS DONE FOR YOU as a worked example of instantiation syntax.
-- Write the other three the same way.
--
-- SYNTAX REMINDER
--   generic map (...) comes BEFORE port map (...)
--   there is NO semicolon between them
--   use named association: formal => actual
--------------------------------------------------------------------------------

library ieee;
use ieee.std_logic_1164.all;

--------------------------------------------------------------------------------
-- MUX2x5  -  WORKED EXAMPLE, already complete. Copy this shape.
--------------------------------------------------------------------------------
entity MUX2x5 is
    port (
        A, B : in  std_logic_vector(4 downto 0);
        Sel  : in  std_logic;
        Y    : out std_logic_vector(4 downto 0)
    );
end entity MUX2x5;

architecture wrapper of MUX2x5 is
begin
    U : entity work.Mux2
        generic map (W => 5)                -- no semicolon on this line
        port map (A => A, B => B, Sel => Sel, Y => Y);
end architecture wrapper;


--------------------------------------------------------------------------------
-- MUX2x32  -  ALUinMUX
--------------------------------------------------------------------------------
library ieee;
use ieee.std_logic_1164.all;

entity MUX2x32 is
    port (
        A, B : in  std_logic_vector(31 downto 0);
        Sel  : in  std_logic;
        Y    : out std_logic_vector(31 downto 0)
    );
end entity MUX2x32;

architecture wrapper of MUX2x32 is
begin
    -- TODO: instantiate Mux2 with W => 32
end architecture wrapper;


--------------------------------------------------------------------------------
-- MUX3x5
--------------------------------------------------------------------------------
library ieee;
use ieee.std_logic_1164.all;

entity MUX3x5 is
    port (
        A, B, C : in  std_logic_vector(4 downto 0);
        Sel     : in  std_logic_vector(1 downto 0);
        Y       : out std_logic_vector(4 downto 0)
    );
end entity MUX3x5;

architecture wrapper of MUX3x5 is
begin
    -- TODO: instantiate Mux3 with W => 5
end architecture wrapper;


--------------------------------------------------------------------------------
-- MUX3x32  -  DinMUX. This is the project's top-level entity.
--------------------------------------------------------------------------------
library ieee;
use ieee.std_logic_1164.all;

entity MUX3x32 is
    port (
        A, B, C : in  std_logic_vector(31 downto 0);
        Sel     : in  std_logic_vector(1 downto 0);
        Y       : out std_logic_vector(31 downto 0)
    );
end entity MUX3x32;

architecture wrapper of MUX3x32 is
begin
    -- TODO: instantiate Mux3 with W => 32
end architecture wrapper;
