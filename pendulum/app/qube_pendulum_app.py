from __future__ import annotations

import queue
import subprocess
import sys
import threading
from pathlib import Path
from tkinter import BooleanVar, StringVar, Tk, messagebox, ttk
from tkinter.scrolledtext import ScrolledText


PROJECT_ROOT = Path(__file__).resolve().parents[1]

MODE_MAP = {
    "Offline Simulation": "offline",
    "Digital Twin": "digital_twin",
    "Hardware Experiment": "hardware",
}

CONTROLLER_MAP = {
    "Sensor check": "sensor_check",
    "Balance": "balance",
    "HyperLIF residual": "hyperlif_residual",
}


class QubePendulumApp:
    """Small desktop launcher for the QUBE-Servo pendulum runners.

    The app deliberately delegates all control work to the existing command-line
    runners. It is a safer configuration and monitoring surface, not a separate
    controller implementation.
    """

    def __init__(self, root: Tk) -> None:
        self.root = root
        self.root.title("QUBE-Servo Pendulum Control Panel")
        self.root.minsize(920, 620)

        self.mode = StringVar(value="Digital Twin")
        self.controller = StringVar(value="Sensor check")
        self.duration = StringVar(value="20")
        self.sample_rate = StringVar(value="500")
        self.voltage_limit = StringVar(value="5.0")
        self.capture_angle = StringVar(value="10.0")
        self.armed = BooleanVar(value=False)
        self.status = StringVar(value="Ready")
        self.command_preview = StringVar(value="")

        self.process: subprocess.Popen[str] | None = None
        self.output_queue: queue.Queue[str] = queue.Queue()

        self._build_ui()
        self._refresh_command_preview()
        self._poll_output()

    def _build_ui(self) -> None:
        frame = ttk.Frame(self.root, padding=16)
        frame.grid(row=0, column=0, sticky="nsew")
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)

        title = ttk.Label(frame, text="QUBE-Servo Pendulum", font=("Segoe UI", 16, "bold"))
        title.grid(row=0, column=0, columnspan=4, sticky="w", pady=(0, 12))

        ttk.Label(frame, text="Mode").grid(row=1, column=0, sticky="w")
        ttk.Combobox(frame, textvariable=self.mode, values=list(MODE_MAP), state="readonly").grid(
            row=2, column=0, sticky="ew", padx=(0, 12)
        )

        ttk.Label(frame, text="Controller").grid(row=1, column=1, sticky="w")
        ttk.Combobox(frame, textvariable=self.controller, values=list(CONTROLLER_MAP), state="readonly").grid(
            row=2, column=1, sticky="ew", padx=(0, 12)
        )

        ttk.Label(frame, text="Duration [s]").grid(row=1, column=2, sticky="w")
        ttk.Entry(frame, textvariable=self.duration).grid(row=2, column=2, sticky="ew", padx=(0, 12))

        ttk.Checkbutton(frame, text="Arm motor output", variable=self.armed).grid(row=2, column=3, sticky="w")

        ttk.Label(frame, text="Sample rate [Hz]").grid(row=3, column=0, sticky="w", pady=(12, 0))
        ttk.Entry(frame, textvariable=self.sample_rate).grid(row=4, column=0, sticky="ew", padx=(0, 12))

        ttk.Label(frame, text="Voltage limit [V]").grid(row=3, column=1, sticky="w", pady=(12, 0))
        ttk.Entry(frame, textvariable=self.voltage_limit).grid(row=4, column=1, sticky="ew", padx=(0, 12))

        ttk.Label(frame, text="Capture angle [deg]").grid(row=3, column=2, sticky="w", pady=(12, 0))
        ttk.Entry(frame, textvariable=self.capture_angle).grid(row=4, column=2, sticky="ew", padx=(0, 12))

        button_bar = ttk.Frame(frame)
        button_bar.grid(row=5, column=0, columnspan=4, sticky="ew", pady=(16, 8))
        ttk.Button(button_bar, text="Run", command=self.run).grid(row=0, column=0, padx=(0, 8))
        ttk.Button(button_bar, text="Stop", command=self.stop).grid(row=0, column=1, padx=(0, 8))
        ttk.Button(button_bar, text="Emergency Stop", command=self.emergency_stop).grid(row=0, column=2)
        ttk.Label(button_bar, textvariable=self.status).grid(row=0, column=3, sticky="e", padx=(16, 0))
        button_bar.columnconfigure(3, weight=1)

        command_box = ttk.LabelFrame(frame, text="Command")
        command_box.grid(row=6, column=0, columnspan=4, sticky="ew", pady=(0, 12))
        ttk.Label(command_box, textvariable=self.command_preview, wraplength=840).grid(
            row=0, column=0, sticky="w", padx=8, pady=8
        )

        output_box = ttk.LabelFrame(frame, text="Runner Output")
        output_box.grid(row=7, column=0, columnspan=4, sticky="nsew")
        self.output = ScrolledText(output_box, height=20, wrap="word")
        self.output.grid(row=0, column=0, sticky="nsew")
        output_box.columnconfigure(0, weight=1)
        output_box.rowconfigure(0, weight=1)

        for var in (
            self.mode,
            self.controller,
            self.duration,
            self.sample_rate,
            self.voltage_limit,
            self.capture_angle,
        ):
            var.trace_add("write", lambda *_: self._refresh_command_preview())
        self.armed.trace_add("write", lambda *_: self._refresh_command_preview())

        for col in range(4):
            frame.columnconfigure(col, weight=1)
        frame.rowconfigure(7, weight=1)

    def _build_command(self) -> list[str]:
        mode = MODE_MAP[self.mode.get()]
        duration = self.duration.get().strip()

        if mode == "offline":
            return [
                sys.executable,
                str(PROJECT_ROOT / "runners" / "run_offline_benchmark.py"),
                "--duration",
                duration,
            ]

        hardware_flag = "1" if mode == "hardware" else "0"
        controller = CONTROLLER_MAP[self.controller.get()]
        cmd = [
            sys.executable,
            str(PROJECT_ROOT / "runners" / "run_online_qube.py"),
            "--mode",
            controller,
            "--hardware",
            hardware_flag,
            "--duration",
            duration,
            "--sample-rate",
            self.sample_rate.get().strip(),
            "--voltage-limit",
            self.voltage_limit.get().strip(),
            "--capture-angle-deg",
            self.capture_angle.get().strip(),
        ]
        if self.armed.get() and controller != "sensor_check":
            cmd.append("--armed")
        return cmd

    def _refresh_command_preview(self) -> None:
        try:
            cmd = self._build_command()
        except Exception as exc:  # pragma: no cover - defensive UI path
            self.command_preview.set(f"Invalid configuration: {exc}")
            return
        self.command_preview.set(" ".join(f'"{part}"' if " " in part else part for part in cmd))

    def run(self) -> None:
        if self.process and self.process.poll() is None:
            messagebox.showinfo("Runner active", "A runner is already active. Stop it before starting another run.")
            return

        mode = MODE_MAP[self.mode.get()]
        controller = CONTROLLER_MAP[self.controller.get()]
        if mode == "hardware" and controller != "sensor_check" and self.armed.get():
            ok = messagebox.askyesno(
                "Confirm hardware run",
                "This will command the physical QUBE motor. Confirm that the rig is clear, calibrated, and the stop path is ready.",
            )
            if not ok:
                return

        cmd = self._build_command()
        self.output.insert("end", f"\n$ {' '.join(cmd)}\n")
        self.output.see("end")
        self.status.set("Running")

        self.process = subprocess.Popen(
            cmd,
            cwd=PROJECT_ROOT,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )
        threading.Thread(target=self._read_process_output, daemon=True).start()

    def stop(self) -> None:
        self._terminate_process("Stop requested")

    def emergency_stop(self) -> None:
        self._terminate_process("Emergency stop requested")

    def _terminate_process(self, status: str) -> None:
        if self.process and self.process.poll() is None:
            self.status.set(status)
            self.process.terminate()
        else:
            self.status.set("Ready")

    def _read_process_output(self) -> None:
        assert self.process is not None
        if self.process.stdout is not None:
            for line in self.process.stdout:
                self.output_queue.put(line)
        return_code = self.process.wait()
        self.output_queue.put(f"\n[runner exited with code {return_code}]\n")
        self.output_queue.put("__PROCESS_DONE__")

    def _poll_output(self) -> None:
        while True:
            try:
                item = self.output_queue.get_nowait()
            except queue.Empty:
                break
            if item == "__PROCESS_DONE__":
                self.status.set("Ready")
                continue
            self.output.insert("end", item)
            self.output.see("end")
        self.root.after(100, self._poll_output)


def main() -> None:
    root = Tk()
    QubePendulumApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
