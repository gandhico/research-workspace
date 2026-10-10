library IEEE;
use IEEE.STD_LOGIC_1164.ALL;

package CPU_Pkg is
    component CPU is
        port(
            SysClk : in STD_LOGIC
        );
    end component;
end package;
