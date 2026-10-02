"""Render a saved MuJoCo mission trace as a compact shareable GIF."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

import mujoco
import numpy as np
from PIL import Image, ImageDraw, ImageFont


def load_trace(path: Path) -> dict[str, np.ndarray]:
    fields = ("time_s", "x_m", "y_m", "z_m", "q_w", "q_x", "q_y", "q_z",
              "actual_rotation_progress_deg")
    values = {field: [] for field in fields}
    with path.open(newline="", encoding="utf-8") as stream:
        for row in csv.DictReader(stream):
            for field in fields:
                values[field].append(float(row[field]))
    return {field: np.asarray(column) for field, column in values.items()}


def font(size: int) -> ImageFont.ImageFont:
    try:
        return ImageFont.truetype("arial.ttf", size)
    except OSError:
        return ImageFont.load_default()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("trace", type=Path)
    parser.add_argument("--xml", type=Path, default=Path(__file__).parents[1] / "mjmodel.xml")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--fps", type=float, default=15.0)
    parser.add_argument("--speed", type=float, default=8.0,
                        help="Playback speed relative to simulated time")
    parser.add_argument("--size", type=int, default=480)
    args = parser.parse_args()

    trace = load_trace(args.trace)
    model = mujoco.MjModel.from_xml_path(str(args.xml.resolve()))
    data = mujoco.MjData(model)
    body_id = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_BODY, "drone")
    if body_id < 0:
        raise ValueError("Body 'drone' was not found")

    camera = mujoco.MjvCamera()
    camera.type = mujoco.mjtCamera.mjCAMERA_FREE
    camera.lookat[:] = (0.0, 0.0, 1.0)
    camera.distance = 1.25
    camera.azimuth = 135.0
    camera.elevation = -18.0
    option = mujoco.MjvOption()

    sample_times = np.arange(trace["time_s"][0], trace["time_s"][-1], args.speed / args.fps)
    indices = np.searchsorted(trace["time_s"], sample_times, side="left")
    indices = np.clip(indices, 0, len(trace["time_s"]) - 1)
    title_font, info_font = font(22), font(18)
    frames: list[Image.Image] = []

    with mujoco.Renderer(model, height=args.size, width=args.size) as renderer:
        for index in indices:
            data.qpos[:3] = [trace["x_m"][index], trace["y_m"][index], trace["z_m"][index]]
            data.qpos[3:7] = [trace["q_w"][index], trace["q_x"][index],
                              trace["q_y"][index], trace["q_z"][index]]
            mujoco.mj_forward(model, data)
            renderer.update_scene(data, camera=camera, scene_option=option)
            image = Image.fromarray(renderer.render()).convert("RGB")
            draw = ImageDraw.Draw(image, "RGBA")
            draw.rounded_rectangle((12, 12, args.size - 12, 82), radius=10,
                                   fill=(255, 255, 255, 215))
            draw.text((26, 22), "Omnicopter virtual twin - X-axis 360 deg",
                      fill=(20, 25, 35, 255), font=title_font)
            draw.text((26, 51),
                      f"Geometric PD | progress {trace['actual_rotation_progress_deg'][index]:6.1f} deg",
                      fill=(35, 45, 60, 255), font=info_font)
            frames.append(image.quantize(colors=192, method=Image.Quantize.MEDIANCUT))

    args.output.parent.mkdir(parents=True, exist_ok=True)
    frame_ms = round(1000 / args.fps)
    frames[0].save(args.output, save_all=True, append_images=frames[1:], duration=frame_ms,
                   loop=0, optimize=True, disposal=2)
    print(args.output.resolve())
    print(f"frames={len(frames)}, displayed_duration_s={len(frames) / args.fps:.2f}")


if __name__ == "__main__":
    main()
