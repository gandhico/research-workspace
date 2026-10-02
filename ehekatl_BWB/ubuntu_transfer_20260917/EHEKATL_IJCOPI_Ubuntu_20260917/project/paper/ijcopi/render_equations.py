"""Render manuscript equations as high-resolution transparent PNG files."""

from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt


HERE = Path(__file__).resolve().parent
OUTPUT = HERE / "equations"
OUTPUT.mkdir(parents=True, exist_ok=True)

EQUATIONS = [
    r"$u_{y,k} \rightarrow u_{t,k} \rightarrow \delta_{a,k} \rightarrow P_k$",
    r"$x_k = [\Delta P_k,\;\Delta u_{t,k},\;\Delta u_{y,k-1}]^T$",
    r"$x_{k+1}=Ax_k+Bu_k$",
    "MATRIX_SPECIAL",
    r"$J=\sum_{k=0}^{\infty}(x_k^TQx_k+u_k^TRu_k)$",
    r"$K=[0.0002944,\;0.0027424,\;0.0292528]$",
    r"$\min_g\;\Vert y_f\Vert_{Q_y}^2+\Vert u_f\Vert_{R_u}^2+\Vert\Delta u_f\Vert_{R_{\Delta u}}^2+\lambda_g\Vert g\Vert_2^2$",
]

mpl.rcParams.update({
    "text.usetex": False,
    "font.family": "serif",
    "font.serif": ["Times New Roman"],
})

for index, equation in enumerate(EQUATIONS, start=1):
    figure = plt.figure(figsize=(8.0, 0.75 if index != 4 else 1.55), dpi=320)
    figure.patch.set_alpha(0.0)
    axis = figure.add_axes([0, 0, 1, 1])
    axis.set_axis_off()
    if equation == "MATRIX_SPECIAL":
        matrix_text = (
            "A = [ 0.40856   3.55738  37.94551 ]      B = [ 23.90120 ]\n"
            "      [ 0         0.05609   0.59835 ]          [  0.37689 ]\n"
            "      [ 0         0         0       ]          [  1       ]"
        )
        axis.text(0.5, 0.5, matrix_text, ha="center", va="center", fontsize=15,
                  family="DejaVu Serif", color="black", linespacing=1.35)
    else:
        axis.text(0.5, 0.5, equation, ha="center", va="center", fontsize=16, color="black")
    figure.savefig(OUTPUT / f"equation_{index}.png", dpi=320, transparent=True,
                   bbox_inches="tight", pad_inches=0.04)
    plt.close(figure)
