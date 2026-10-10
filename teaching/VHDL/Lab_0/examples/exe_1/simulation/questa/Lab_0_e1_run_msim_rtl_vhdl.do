transcript on
if {[file exists rtl_work]} {
	vdel -lib rtl_work -all
}
vlib rtl_work
vmap work rtl_work

vcom -93 -work work {C:/Teaching/VHDL/Lab_0/examples/exe_1/e1_majority3_beh.vhd}

