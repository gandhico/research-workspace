"""
render_events.py  --  run the DVS emulator on one vehicle's onboard camera over a logged race.

For vehicle <pre>:
  * replays results/race_<tag>.npz (qpos logged at 500 Hz) and renders "<pre>/dvs"
    (346x260, 75 deg FOV, cast shadows OFF for speed) at EVERY logged step -> 500 Hz frames;
  * feeds the frames to event_camera.DVS  -> events with interpolated sub-ms timestamps;
  * renders "<pre>/fpv" RGB (shadows on) at 30 fps for the side-by-side video.
Outputs (events are STREAMED to disk; RAM holds only the last ~80 ms):
  results/events_<pre>.bin   raw events, numpy dtype [t <i8 us, x <u2, y <u2, p i1] (13 B/event)
                             -> np.fromfile(path, dtype=event_camera.EVENT_DTYPE)
  results/events_<pre>.npz   per-10 ms event-rate series (ON/OFF) + sensor geometry
  media/events_<pre>.mp4     [ FPV RGB | DVS events accumulated over 33 ms (ON red / OFF blue) ]

    python render_events.py --veh y6 [--tag fleet] [--t0 0] [--t1 inf]
"""
import argparse, pathlib, time, json
import numpy as np
import mujoco
import imageio.v2 as imageio
from PIL import Image, ImageDraw, ImageFont

import build_scene
from event_camera import MujocoEventCamera, event_frame, EVENT_DTYPE

HERE = pathlib.Path(__file__).resolve().parent
W, H = 346, 260
FONT = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", 14)
NAMES = {"x2": "Skydio X2", "cf2": "Crazyflie 2 (rotor model)", "omni": "Omnicopter", "y6": "Coaxial Y6"}


def tag_img(img, text, sub=None):
    im = Image.fromarray(img); dr = ImageDraw.Draw(im)
    dr.rectangle([0, 0, 7*len(text) + 10, 20], fill=(0, 0, 0))
    dr.text((5, 2), text, font=FONT, fill=(255, 255, 255))
    if sub:
        dr.text((5, H - 20), sub, font=FONT, fill=(0, 0, 0), stroke_width=2, stroke_fill=(255, 255, 255))
    return np.asarray(im)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--veh", required=True)
    ap.add_argument("--tag", default="fleet")
    ap.add_argument("--t0", type=float, default=0.0)
    ap.add_argument("--t1", type=float, default=np.inf)
    ap.add_argument("--fps", type=float, default=30.0)
    a = ap.parse_args()
    pre = a.veh

    D = np.load(HERE / "results" / f"race_{a.tag}.npz")
    T, Q = D["t"], D["qpos"]
    spec, m = build_scene.build(out=HERE / "models" / f"_render_{pre}.xml")
    d = mujoco.MjData(m)
    cam = MujocoEventCamera(m, f"{pre}/dvs", W, H)
    rgb = mujoco.Renderer(m, H, W)

    sel = np.nonzero((T >= a.t0) & (T <= a.t1))[0]
    out_v = HERE / "media"; out_v.mkdir(exist_ok=True)
    writer = imageio.get_writer(out_v / f"events_{pre}.mp4", fps=a.fps, codec="libx264", quality=7,
                                macro_block_size=2)
    evs, next_frame, t_wall = [], T[sel[0]], time.time()
    win_us = int(1e6/a.fps)
    raw = open(HERE / "results" / f"events_{pre}.bin", "wb")
    t_first_us = int(T[sel[0]]*1e6)
    nb = int((T[sel[-1]] - T[sel[0]])*100) + 2                 # 10 ms bins
    rate_on, rate_off = np.zeros(nb, np.int64), np.zeros(nb, np.int64)
    n_total = n_on = 0
    for n, k in enumerate(sel):
        d.qpos[:] = Q[k]; mujoco.mj_forward(m, d); d.time = T[k]
        cam.r.update_scene(d, camera=cam.cam)
        cam.r.scene.flags[mujoco.mjtRndFlag.mjRND_SHADOW] = False
        cam.r.scene.flags[mujoco.mjtRndFlag.mjRND_REFLECTION] = False
        img = cam.r.render().astype(np.float32)/255.0
        gray = 0.299*img[..., 0] + 0.587*img[..., 1] + 0.114*img[..., 2]
        ev = cam.dvs.step(gray, T[k])
        if len(ev):
            ev.tofile(raw)
            b = np.clip((ev["t"] - t_first_us)//10_000, 0, nb - 1)
            on = ev["p"] > 0
            np.add.at(rate_on, b[on], 1); np.add.at(rate_off, b[~on], 1)
            n_total += len(ev); n_on += int(on.sum())
            evs.append(ev)
            if len(evs) > 40:                                  # keep only ~80 ms in RAM
                evs.pop(0)
        if T[k] >= next_frame:                                   # video frame (30 fps)
            rgb.update_scene(d, camera=f"{pre}/fpv")
            fr = rgb.render()
            t_us = int(T[k]*1e6)
            recent = np.concatenate(evs) if evs else np.zeros(0, EVENT_DTYPE)
            ef = event_frame(recent, W, H, t_us - win_us, t_us)
            nwin = int(((recent["t"] >= t_us - win_us) & (recent["t"] < t_us)).sum()) if len(recent) else 0
            left = tag_img(fr, f"{NAMES[pre]} - FPV RGB", f"t = {T[k]:5.2f} s")
            right = tag_img(ef, "DVS 346x260 - events / 33 ms", f"{nwin/(win_us*1e-6)/1e6:5.2f} Mev/s")
            writer.append_data(np.hstack([left, right]))
            next_frame += 1.0/a.fps
        if n % 2500 == 0:
            print(f"  {pre}: {n}/{len(sel)} frames, {n_total} events, {time.time()-t_wall:.0f} s", flush=True)
    writer.close(); raw.close()
    rate = rate_on + rate_off
    np.savez_compressed(HERE / "results" / f"events_{pre}.npz",
                        rate_t=T[sel[0]] + 0.01*np.arange(nb), rate_ev_per_10ms=rate,
                        rate_on=rate_on, rate_off=rate_off, width=W, height=H)
    stats = dict(vehicle=pre, frames=len(sel), frame_rate_hz=round(float(1/np.median(np.diff(T[sel]))), 1),
                 events=int(n_total), on_frac=round(n_on/max(n_total, 1), 3),
                 mean_rate_Mev_s=round(n_total/(T[sel[-1]] - T[sel[0]])/1e6, 3),
                 peak_rate_Mev_s_10ms=round(float(rate.max())/0.01/1e6, 3),
                 raw_file=f"results/events_{pre}.bin", raw_MB=round(n_total*EVENT_DTYPE.itemsize/1e6, 1),
                 dvs=dict(C=0.25, sigma_C=0.03, t_ref_s=1e-4, noise_hz_per_px=0.1, W=W, H=H,
                          fovy_deg=75, frame_rate_hz=500, shadows=False),
                 wall_s=round(time.time() - t_wall, 1))
    (HERE / "results" / f"events_{pre}.json").write_text(json.dumps(stats, indent=1))
    print(stats)


if __name__ == "__main__":
    main()
