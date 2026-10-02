"""Plot the saved validation traces; does not rerun simulations."""
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

out = Path(__file__).resolve().parent / "output/validation"
plt.rcParams.update({"font.size": 11, "axes.spines.top": False, "axes.spines.right": False})
fig, axes = plt.subplots(3, 1, figsize=(10, 8), sharex=True, layout="constrained")
for name, label, color in [
    ("demo", "Initial offset: 20 cm / 7.8 deg", "#007f86"),
    ("impulse", "Velocity impulse at 2 s", "#d68a00"),
    ("larger_displacement", "Initial offset: 47 cm / 26.9 deg", "#6454b1"),
]:
    data = np.genfromtxt(out / f"{name}.csv", delimiter=",", names=True)
    axes[0].plot(data["time_s"], 100 * data["position_error_m"], label=label, color=color, lw=2)
    axes[1].plot(data["time_s"], data["attitude_error_deg"], color=color, lw=2)
    axes[2].plot(data["time_s"], data["peak_abs_thrust_N"], color=color, lw=2)
axes[0].set_ylabel("Position error (cm)")
axes[1].set_ylabel("Attitude error (deg)")
axes[2].set_ylabel("Largest |rotor thrust| (N)")
axes[2].axhline(10, color="#b7333e", linestyle="--", lw=1.3)
axes[2].text(9.9, 10.08, "XML actuator limit", ha="right", color="#b7333e", fontsize=10)
axes[2].set_ylim(6.5, 10.7)
axes[2].set_xlabel("Simulation time (s)")
axes[0].legend(loc="upper right", frameon=False, fontsize=10)
for ax in axes:
    ax.grid(alpha=.18)
    ax.set_xlim(0, 10)
fig.suptitle("Omnicopter | Stage-1 hover recovery\nOriginal MuJoCo model, ideal state feedback, eight bounded thrust inputs", fontsize=14)
fig.savefig(out / "hover_validation.png", dpi=150)
plt.close(fig)
print(out / "hover_validation.png")
