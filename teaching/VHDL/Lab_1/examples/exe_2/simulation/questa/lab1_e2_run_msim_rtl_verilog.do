transcript on
if {[file exists rtl_work]} {
	vdel -lib rtl_work -all
}
vlib rtl_work
vmap work rtl_work

vlog  -work work +incdir+C:/Teaching/VHDL/Lab_1/examples/exe_2 {C:/Teaching/VHDL/Lab_1/examples/exe_2/de0_nano_soc_baseline.v}

