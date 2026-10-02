from __future__ import annotations

import queue
import subprocess
import sys
import threading
from pathlib import Path
from tkinter import BooleanVar, StringVar, Tk, messagebox, ttk
from tkinter.scrolledtext import ScrolledText


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from aero2.config import capabilities

MODE_MAP = {
    meta["label"]: key for key, meta in capabilities.EXECUTION_MODES.items()
}

MODE_STATUS = {
    key: meta["status"] for key, meta in capabilities.EXECUTION_MODES.items()
}


class Aero2App:
    """Robot-specific desktop launcher for Aero 2 control experiments."""

    def __init__(self, root: Tk) -> None:
        self.root = root
        self.root.title("Quanser Aero 2 Control Panel")
        self.root.minsize(980, 660)

        self.mode = StringVar(value="Offline Simulation")
        self.model = StringVar(value="helicopter_2dof")
        self.controller = StringVar(value="pd")
        self.application = StringVar(value="reference_tracking")
        self.duration = StringVar(value="40")
        self.hz = StringVar(value="200")
        self.dt = StringVar(value="0.005")
        self.save = BooleanVar(value=True)
        self.allow_scaffolded = BooleanVar(value=False)
        self.status = StringVar(value="Ready")
        self.command_preview = StringVar(value="")
        self.capability_text = StringVar(value="")

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

        title = ttk.Label(frame, text="Quanser Aero 2", font=("Segoe UI", 16, "bold"))
        title.grid(row=0, column=0, columnspan=4, sticky="w", pady=(0, 12))

        ttk.Label(frame, text="Mode").grid(row=1, column=0, sticky="w")
        ttk.Combobox(frame, textvariable=self.mode, values=list(MODE_MAP), state="readonly").grid(
            row=2, column=0, sticky="ew", padx=(0, 12)
        )

        ttk.Label(frame, text="Model").grid(row=1, column=1, sticky="w")
        ttk.Combobox(
            frame,
            textvariable=self.model,
            values=list(capabilities.MODELS),
            state="readonly",
        ).grid(row=2, column=1, sticky="ew", padx=(0, 12))

        ttk.Label(frame, text="Controller").grid(row=1, column=2, sticky="w")
        ttk.Combobox(
            frame,
            textvariable=self.controller,
            values=list(capabilities.CONTROLLERS),
            state="readonly",
        ).grid(row=2, column=2, sticky="ew", padx=(0, 12))

        ttk.Label(frame, text="Application").grid(row=1, column=3, sticky="w")
        ttk.Combobox(
            frame,
            textvariable=self.application,
            values=list(capabilities.APPLICATIONS),
            state="readonly",
        ).grid(row=2, column=3, sticky="ew")

        ttk.Label(frame, text="Duration [s]").grid(row=3, column=0, sticky="w", pady=(12, 0))
        ttk.Entry(frame, textvariable=self.duration).grid(row=4, column=0, sticky="ew", padx=(0, 12))

        ttk.Label(frame, text="Nominal rate [Hz]").grid(row=3, column=1, sticky="w", pady=(12, 0))
        ttk.Entry(frame, textvariable=self.hz).grid(row=4, column=1, sticky="ew", padx=(0, 12))

        ttk.Label(frame, text="Offline dt [s]").grid(row=3, column=2, sticky="w", pady=(12, 0))
        ttk.Entry(frame, textvariable=self.dt).grid(row=4, column=2, sticky="ew", padx=(0, 12))

        checks = ttk.Frame(frame)
        checks.grid(row=4, column=3, sticky="w")
        ttk.Checkbutton(checks, text="Save results", variable=self.save).grid(row=0, column=0, sticky="w")
        ttk.Checkbutton(checks, text="Allow scaffolded modes", variable=self.allow_scaffolded).grid(
            row=1, column=0, sticky="w"
        )

        button_bar = ttk.Frame(frame)
        button_bar.grid(row=5, column=0, columnspan=4, sticky="ew", pady=(16, 8))
        ttk.Button(button_bar, text="Run", command=self.run).grid(row=0, column=0, padx=(0, 8))
        ttk.Button(button_bar, text="Stop", command=self.stop).grid(row=0, column=1, padx=(0, 8))
        ttk.Button(button_bar, text="Emergency Stop", command=self.emergency_stop).grid(row=0, column=2)
        ttk.Label(button_bar, textvariable=self.status).grid(row=0, column=3, sticky="e", padx=(16, 0))
        button_bar.columnconfigure(3, weight=1)

        command_box = ttk.LabelFrame(frame, text="Command")
        command_box.grid(row=6, column=0, columnspan=4, sticky="ew", pady=(0, 12))
        ttk.Label(command_box, textvariable=self.command_preview, wraplength=900).grid(
            row=0, column=0, sticky="w", padx=8, pady=8
        )

        capability_box = ttk.LabelFrame(frame, text="Capability")
        capability_box.grid(row=7, column=0, columnspan=4, sticky="ew", pady=(0, 12))
        ttk.Label(capability_box, textvariable=self.capability_text, wraplength=900, justify="left").grid(
            row=0, column=0, sticky="w", padx=8, pady=8
        )

        output_box = ttk.LabelFrame(frame, text="Runner Output")
        output_box.grid(row=8, column=0, columnspan=4, sticky="nsew")
        self.output = ScrolledText(output_box, height=22, wrap="word")
        self.output.grid(row=0, column=0, sticky="nsew")
        output_box.columnconfigure(0, weight=1)
        output_box.rowconfigure(0, weight=1)

        for var in (self.mode, self.model, self.controller, self.application, self.duration, self.hz, self.dt):
            var.trace_add("write", lambda *_: self._refresh_command_preview())
        self.save.trace_add("write", lambda *_: self._refresh_command_preview())

        for col in range(4):
            frame.columnconfigure(col, weight=1)
        frame.rowconfigure(8, weight=1)

    def _build_command(self) -> list[str]:
        cmd = [
            sys.executable,
            str(PROJECT_ROOT / "runners" / "run_control.py"),
            "--model",
            self.model.get(),
            "--mode",
            MODE_MAP[self.mode.get()],
            "--controller",
            self.controller.get(),
            "--application",
            self.application.get(),
            "--duration",
            self.duration.get().strip(),
            "--hz",
            self.hz.get().strip(),
            "--dt",
            self.dt.get().strip(),
        ]
        if self.save.get():
            cmd.append("--save")
        return cmd

    def _refresh_command_preview(self) -> None:
        try:
            cmd = self._build_command()
        except Exception as exc:  # pragma: no cover - defensive UI path
            self.command_preview.set(f"Invalid configuration: {exc}")
            return
        mode_key = MODE_MAP[self.mode.get()]
        self.command_preview.set(
            f"[{MODE_STATUS[mode_key]}] "
            + " ".join(f'"{part}"' if " " in part else part for part in cmd)
        )
        self.capability_text.set(
            "\n".join(
                capabilities.capability_notes(
                    self.model.get(),
                    mode_key,
                    self.controller.get(),
                    self.application.get(),
                )
            )
        )

    def run(self) -> None:
        if self.process and self.process.poll() is None:
            messagebox.showinfo("Runner active", "A runner is already active. Stop it before starting another run.")
            return

        mode_key = MODE_MAP[self.mode.get()]
        if MODE_STATUS[mode_key] == "scaffolded" and not self.allow_scaffolded.get():
            messagebox.showwarning(
                "Mode not implemented",
                "This Aero 2 backend is scaffolded but not implemented yet. "
                "Use Offline Simulation or Digital Twin, or enable scaffolded modes to verify the failure path.",
            )
            return
        if mode_key == "virtual_twin" or MODE_STATUS[mode_key] == "external_required":
            ok = messagebox.askyesno(
                "Confirm digital twin",
                "Digital Twin uses Quanser PAL/QLabs and expects the virtual Aero 2 to be running at localhost:18950. "
                "The current QLabs scene has only been validated as pitch-only; yaw is locked until a true 2-DOF scene is loaded.",
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
    Aero2App(root)
    root.mainloop()


if __name__ == "__main__":
    main()
