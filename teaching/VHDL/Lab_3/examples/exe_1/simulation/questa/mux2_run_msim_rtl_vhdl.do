transcript on
if {[file exists rtl_work]} {
	vdel -lib rtl_work -all
}
vlib rtl_work
vmap work rtl_work

vcom -93 -work work {C:/Teaching/VHDL/Lab_3/examples/exe_1/mux2_styles.vhd}

