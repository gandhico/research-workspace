transcript on
if {[file exists rtl_work]} {
	vdel -lib rtl_work -all
}
vlib rtl_work
vmap work rtl_work

vcom -93 -work work {C:/Teaching/VHDL/Lab_3/examples/exe_3/mux3_latch_trap.vhd}

