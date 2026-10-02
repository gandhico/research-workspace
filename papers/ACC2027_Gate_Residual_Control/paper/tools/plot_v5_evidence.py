"""Publication-size plots from existing traces; no smoothing or new experiments."""
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

PAPER = Path(__file__).resolve().parents[1]
RUNS = PAPER.parent/'experiments/nengo_nef_replication_2026-08-29/results/matched_45s'
OUT = PAPER/'figures/v5_audit'
OUT.mkdir(parents=True, exist_ok=True)
plt.rcParams.update({'font.size': 8, 'axes.labelsize': 8, 'legend.fontsize': 7,
                     'xtick.labelsize': 7, 'ytick.labelsize': 7,
                     'axes.spines.top': False, 'axes.spines.right': False,
                     'savefig.dpi': 350, 'font.family': 'DejaVu Sans'})

fig, ax = plt.subplots(figsize=(3.45, 2.05), layout='constrained')
for name, label, color in [('x2_hard45_classical', 'Quaternion PD', '#285A8E'),
                            ('x2_hard45_nengo_nef_pes', 'CMG-PES', '#C5472C')]:
    data = np.genfromtxt(RUNS/name/'trace.csv', delimiter=',', names=True,
                         usecols=('t', 'qerr'))
    ax.plot(data['t'], np.rad2deg(data['qerr']), label=label, color=color, lw=.8)
ax.set(xlim=(0, 45), ylim=(0, 42), xticks=[0, 15, 30, 45],
       yticks=[0, 10, 20, 30, 40], xlabel='Time (s)', ylabel='Angle error (deg)')
ax.grid(alpha=.2)
ax.legend(loc='upper right', framealpha=.95)
fig.savefig(OUT/'x2_hard45_error.png')
plt.close(fig)

data = np.genfromtxt(RUNS/'x2_yaw360_nengo_nef_pes/trace.csv', delimiter=',',
                     names=True, usecols=('t', 'voltage_2', 'voltage_5',
                                          'gate_2', 'gate_5', 'activity_2', 'activity_5'))
fig, axes = plt.subplots(3, 1, figsize=(3.45, 3.35), sharex=True, layout='constrained')
for ax, field, label in zip(axes, ['voltage', 'gate', 'activity'],
                           ['Membrane v', 'Gate r', 'Activity a']):
    for j, branch, color, style in [(2, '+z unit', '#7751A8', '-'),
                                      (5, '-z unit', '#00857D', '--')]:
        ax.plot(data['t'], data[f'{field}_{j}'], color=color, ls=style, lw=1., label=branch)
    ax.set_ylabel(label)
    ax.grid(alpha=.2)
axes[0].legend(loc='lower right', ncol=2)
axes[1].ticklabel_format(axis='y', style='sci', scilimits=(0, 0), useMathText=True)
axes[-1].set(xlim=(0, 45), xticks=[0, 15, 30, 45], xlabel='Time (s)')
fig.savefig(OUT/'x2_yaw360_cmg_states.png')
plt.close(fig)
print(f'Created two publication-size PNG figures in {OUT}')
