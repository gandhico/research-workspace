--------------------------------------------------------------------------------
-- EE 362 - Lab 8, Example 2 - Exhaustive over the flags
--
-- Two flags means four flag combinations, and seven conditions. 28 cases, and
-- we test ALL of them - this is a Type E table small enough to enumerate
-- completely, so there is no coverage argument to make. Just do it.
--
-- Note that {N=1, Z=1} is impossible in real hardware: a result cannot be both
-- zero and negative. It is tested anyway, because "impossible" inputs are
-- exactly what produce latches and surprises when someone later makes them
-- possible.
--------------------------------------------------------------------------------

library ieee;
use ieee.std_logic_1164.all;

use work.NIAG_Pkg.all;

entity branch_conditions_tb is
end entity branch_conditions_tb;

architecture test of branch_conditions_tb is

    signal Cond  : std_logic_vector(2 downto 0) := NIAG_COND_NONE;
    signal Zero, Neg, Taken : std_logic := '0';

begin

    DUT : entity work.branch_conditions
        port map (Cond => Cond, Zero => Zero, Neg => Neg, Taken => Taken);

    stimulus : process

        variable errors : natural := 0;

        -- VHDL has no anonymous declare-block inside a process, so the
        -- loop variables below live here, in the process declarative part.
        variable zv, nv : std_logic;
        variable a,  b  : std_logic;

        procedure t (c : in std_logic_vector(2 downto 0);
                     z, n, want : in std_logic;
                     msg : in string) is
        begin
            Cond <= c; Zero <= z; Neg <= n;
            wait for 5 ns;
            if Taken /= want then
                report "FAIL: " & msg &
                       " (Z=" & std_logic'image(z) &
                       " N=" & std_logic'image(n) & ")" severity error;
                errors := errors + 1;
            end if;
        end procedure t;

    begin

        -- NONE: always taken, whatever the flags say
        t(NIAG_COND_NONE, '0','0','1', "NONE always taken");
        t(NIAG_COND_NONE, '1','0','1', "NONE always taken");
        t(NIAG_COND_NONE, '0','1','1', "NONE always taken");

        -- EQ = Z
        t(NIAG_COND_EQ, '0','0','0', "EQ not taken when non-zero");
        t(NIAG_COND_EQ, '1','0','1', "EQ taken when zero");
        t(NIAG_COND_EQ, '0','1','0', "EQ not taken when negative");

        -- NEQ = Z'
        t(NIAG_COND_NEQ, '0','0','1', "NEQ taken when non-zero");
        t(NIAG_COND_NEQ, '1','0','0', "NEQ not taken when zero");
        t(NIAG_COND_NEQ, '0','1','1', "NEQ taken when negative (non-zero)");

        -- GTZ = N' . Z'   (strictly positive)
        t(NIAG_COND_GTZ, '0','0','1', "GTZ taken when positive");
        t(NIAG_COND_GTZ, '1','0','0', "GTZ NOT taken when zero");
        t(NIAG_COND_GTZ, '0','1','0', "GTZ not taken when negative");

        -- GEZ = N'
        t(NIAG_COND_GEZ, '0','0','1', "GEZ taken when positive");
        t(NIAG_COND_GEZ, '1','0','1', "GEZ taken when zero");
        t(NIAG_COND_GEZ, '0','1','0', "GEZ not taken when negative");

        -- LTZ = N
        t(NIAG_COND_LTZ, '0','0','0', "LTZ not taken when positive");
        t(NIAG_COND_LTZ, '1','0','0', "LTZ not taken when zero");
        t(NIAG_COND_LTZ, '0','1','1', "LTZ taken when negative");

        -- LEZ = N + Z    <- the one the Lab 12 program uses
        t(NIAG_COND_LEZ, '0','0','0', "LEZ not taken when positive");
        t(NIAG_COND_LEZ, '1','0','1', "LEZ TAKEN when zero - the loop exit");
        t(NIAG_COND_LEZ, '0','1','1', "LEZ taken when negative");

        -- An undefined code must give a DEFINED, safe answer: not taken.
        t("111", '0','0','0', "undefined condition defaults to not-taken");
        t("111", '1','1','0', "undefined condition defaults to not-taken");

        ----------------------------------------------------------------------
        -- The complement pairs. If these do not hold, one of the six equations
        -- is wrong.
        ----------------------------------------------------------------------
        report "Checking complement pairs: GTZ/LEZ, GEZ/LTZ" severity note;

        for zi in 0 to 1 loop
            for ni in 0 to 1 loop

                if zi = 1 then zv := '1'; else zv := '0'; end if;
                if ni = 1 then nv := '1'; else nv := '0'; end if;

                Cond <= NIAG_COND_GTZ; Zero <= zv; Neg <= nv;
                wait for 5 ns; a := Taken;
                Cond <= NIAG_COND_LEZ;
                wait for 5 ns; b := Taken;
                if a = b then
                    report "FAIL: GTZ and LEZ are not complements" severity error;
                    errors := errors + 1;
                end if;

                Cond <= NIAG_COND_GEZ;
                wait for 5 ns; a := Taken;
                Cond <= NIAG_COND_LTZ;
                wait for 5 ns; b := Taken;
                if a = b then
                    report "FAIL: GEZ and LTZ are not complements" severity error;
                    errors := errors + 1;
                end if;

            end loop;
        end loop;

        if errors = 0 then
            report "PASS - branch_conditions: all 28 cases and both complement pairs."
                severity note;
        else
            report "FAILED - branch_conditions: " & integer'image(errors) &
                   " check(s) failed." severity error;
        end if;

        wait;
    end process stimulus;

end architecture test;
