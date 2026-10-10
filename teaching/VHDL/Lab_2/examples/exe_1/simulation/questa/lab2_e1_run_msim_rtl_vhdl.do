transcript on
if {[file exists rtl_work]} {
	vdel -lib rtl_work -all
}
vlib rtl_work
vmap work rtl_work

vcom -93 -work work {C:/Teaching/VHDL/Lab_2/examples/exe_1/trans_latch.vhd}
vcom -93 -work work {C:/Teaching/VHDL/Lab_2/examples/exe_1/ms_flipflop.vhd}

