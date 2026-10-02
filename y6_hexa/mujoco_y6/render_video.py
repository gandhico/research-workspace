"""
render_video.py  --  replay a logged MuJoCo run and render it with the scene's built-in cameras.

2x2 panel video (1280x720, 30 fps):
    chase (trackcom, world-fixed offset) | onboard FPV RGB  (body-fixed, 70 deg FOV)
    side tracker (ground, targets y6)     | onboard FPV depth (metres, 0-20 m colour map)
plus PNG snapshots (FPV RGB/depth at the hub hold, down-looking gimbal, overview).

    python render_video.py results/nef_lif.npz  ["label"]
"""
import sys, pathlib
import numpy as np
import mujoco
import imageio.v2 as imageio
from PIL import Image, ImageDraw, ImageFont

HERE = pathlib.Path(__file__).resolve().parent
XML = HERE / "y6_turbine_scene.xml"
W, H, FPS = 640, 360, 30
FONT = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", 17)
FONT_B = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", 19)


def depth_to_rgb(depth, dmax=20.0):
    from matplotlib import colormaps
    x = np.clip(depth / dmax, 0, 1)
    img = (colormaps["turbo_r"](x)[..., :3]*255).astype(np.uint8)   # near = red, far = blue
    img[depth >= dmax] = (15, 15, 30)
    return img


def label(img, text, sub=None):
    im = Image.fromarray(img); dr = ImageDraw.Draw(im)
    dr.rectangle([0, 0, 8 + 10*len(text), 28], fill=(0, 0, 0))
    dr.text((6, 4), text, font=FONT_B, fill=(255, 255, 255))
    if sub:
        for i, line in enumerate(sub):
            dr.text((8, H - 24*(len(sub) - i) - 4), line, font=FONT, fill=(255, 255, 255),
                    stroke_width=2, stroke_fill=(0, 0, 0))
    return np.asarray(im)


def main(npz, tag_label=None):
    npz = pathlib.Path(npz)
    D = np.load(npz)
    t, qpos, S, wind = D["t"], D["qpos"], D["state"], D["wind"]
    ref = D["ref_pos"]
    tag_label = tag_label or npz.stem
    m = mujoco.MjModel.from_xml_path(str(XML)); d = mujoco.MjData(m)
    rgb = mujoco.Renderer(m, H, W)
    dep = mujoco.Renderer(m, H, W); dep.enable_depth_rendering()

    out = HERE / "media"; out.mkdir(exist_ok=True)
    writer = imageio.get_writer(out / f"{npz.stem}.mp4", fps=FPS, codec="libx264",
                                quality=7, macro_block_size=16)
    frame_idx = np.searchsorted(t, np.arange(t[0], t[-1], 1.0 / FPS))
    snaps = {17.0: "hub_hold", 27.0: "blade_sweep", 44.0: "side_view"}
    for n, k in enumerate(frame_idx):
        d.qpos[:] = qpos[k]; mujoco.mj_forward(m, d)
        panels = []
        for cam in ("chase", "fpv", "side"):
            rgb.update_scene(d, camera=cam); panels.append(rgb.render().copy())
        dep.update_scene(d, camera="fpv"); depth = dep.render().copy()
        e = np.linalg.norm(S[k, :3] - ref[k])
        hud = [f"t = {t[k]:5.1f} s   {tag_label}",
               f"pos = ({S[k,0]:5.2f}, {S[k,1]:5.2f}, {S[k,2]:5.2f}) m   |e| = {e*100:4.1f} cm",
               f"yaw = {np.degrees(S[k,8]):6.1f} deg   wind = {wind[k,0]:4.1f} m/s"]
        a = label(panels[0], "Chase camera", hud)
        b = label(panels[1], "Onboard FPV camera (RGB)")
        c = label(panels[2], "Ground tracking camera  -  hub 8 m, rotor R 3.7 m")
        dd = label(depth_to_rgb(depth), "Onboard FPV depth (0-20 m)",
                   [f"centre-ROI range = {np.nanmin(np.where(depth[150:210, 290:350] > 0, depth[150:210, 290:350], np.nan)):.2f} m"])
        frame = np.vstack([np.hstack([a, b]), np.hstack([c, dd])])
        writer.append_data(frame)
        for ts, name in list(snaps.items()):
            if abs(t[k] - ts) < 0.5 / FPS:
                Image.fromarray(frame).save(out / f"{npz.stem}_{name}.png")
                Image.fromarray(panels[1]).save(out / f"{npz.stem}_{name}_fpv.png")
                Image.fromarray(depth_to_rgb(depth)).save(out / f"{npz.stem}_{name}_depth.png")
        if n % 300 == 0:
            print(f"  frame {n}/{len(frame_idx)}", flush=True)
    writer.close()
    # hero still of the whole scene (free camera)
    d.qpos[:] = qpos[np.searchsorted(t, 25.0)]; mujoco.mj_forward(m, d)
    big = mujoco.Renderer(m, 720, 1280); cam = mujoco.MjvCamera()
    cam.lookat[:] = [8.5, -0.8, 6.8]; cam.distance = 10.5; cam.azimuth = 28; cam.elevation = -9
    big.update_scene(d, camera=cam); Image.fromarray(big.render()).save(out / f"{npz.stem}_hero.png")
    big.update_scene(d, camera="gimbal_down"); Image.fromarray(big.render()).save(out / f"{npz.stem}_gimbal_down.png")
    print("wrote", out / f"{npz.stem}.mp4")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None)
