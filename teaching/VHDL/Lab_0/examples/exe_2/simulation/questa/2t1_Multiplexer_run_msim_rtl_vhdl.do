transcript on
if {[file exists rtl_work]} {
	vdel -lib rtl_work -all
}
vlib rtl_work
vmap work rtl_work

vcom -93 -work work {C:/Teaching/VHDL/Lab_0/examples/exe_2/2e_2t1_multiplexer_beh.vhd}

