transcript on
if {[file exists rtl_work]} {
	vdel -lib rtl_work -all
}
vlib rtl_work
vmap work rtl_work

vcom -93 -work work {C:/Teaching/VHDL/Lab 0 (Transparent Latch)/TransLatch.vhd}

