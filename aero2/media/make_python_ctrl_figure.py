"""Render the Python PD + Backstepping control laws as a clean code figure
(white background, dark syntax colors) to sit beside the MATLAB/Simulink block
diagram. Faithful to aero2/control/linear/pd.py and .../nonlinear/backstepping.py.
"""
import io, os
from PIL import Image, ImageDraw, ImageFont
from pygments import highlight
from pygments.lexers import PythonLexer
from pygments.formatters import ImageFormatter
from pygments.style import Style
from pygments.token import (Keyword, Name, Comment, String, Number, Operator,
                            Punctuation, Text)

OUT = r"C:\Research\aero2\results_paper\figures\fig_python_controllers.png"

# --- GitHub-light palette: dark tokens on pure white ------------------------
class GHLight(Style):
    background_color = "#ffffff"
    styles = {
        Text:            "#24292e",
        Comment:         "italic #6a737d",
        Keyword:         "bold #d73a49",
        Keyword.Constant:"#005cc5",
        Name:            "#24292e",
        Name.Function:   "#6f42c1",
        Name.Class:      "bold #6f42c1",
        Name.Builtin:    "#005cc5",
        Name.Builtin.Pseudo: "#e36209",   # self
        String:          "#032f62",
        Number:          "#005cc5",
        Operator:        "#d73a49",
        Punctuation:     "#24292e",
    }

PD = '''class PD2DOF:                    # linear baseline (Ref 3, Eqs. 39-41)
    def compute(self, x, ref, dt):
        theta, psi = x[0], x[2]

        # filtered rate: 2nd-order derivative filter on the MEASURED
        # angle, advanced with the ACTUAL loop dt (headline lesson)
        theta_rate = self.pitch_filter.filtered_rate
        psi_rate   = self.yaw_filter.filtered_rate

        e_theta = ref.theta - theta         # tracking error
        e_psi   = ref.psi   - psi

        u_p = self.kp_pitch*e_theta - self.kd_pitch*theta_rate
        u_y = self.kp_yaw  *e_psi   - self.kd_yaw  *psi_rate
        u = np.clip([u_p, u_y], -V_MAX, V_MAX)   # +/-24 V limit

        self.pitch_filter.update(theta, dt)  # read rate, THEN update
        self.yaw_filter.update(psi, dt)
        return u
'''

BS = '''class Backstepping2DOF:          # nonlinear computed torque (Eqs. 48-50)
    def compute(self, x, ref, dt):
        theta, theta_dot, psi, psi_dot = x

        e_theta = theta - ref.theta
        e_psi   = psi   - ref.psi

        # desired virtual accelerations (stable error dynamics)
        v = [-self.k1_pitch*e_theta - self.k2_pitch*theta_dot,
             -self.k1_yaw  *e_psi   - self.k2_yaw  *psi_dot]

        # least-squares inverse dynamics:  M(theta) u = v - b(x)
        M = input_matrix(theta)   # yaw scaled by cos(theta),|c|>=.25
        b = drift(theta, theta_dot, psi_dot)
        u = np.linalg.lstsq(M, v - b)[0]
        return np.clip(u, -V_MAX, V_MAX)         # +/-24 V limit
'''

FONT_SIZE = 26
def render(code):
    fmt = ImageFormatter(style=GHLight, font_name="Consolas", font_size=FONT_SIZE,
                         line_numbers=False, image_pad=22, line_pad=6)
    png = highlight(code, PythonLexer(), fmt)
    return Image.open(io.BytesIO(png)).convert("RGB")

img_pd = render(PD)
img_bs = render(BS)

# --- compose: two titled cards side by side ---------------------------------
def load_font(path, size):
    try: return ImageFont.truetype(path, size)
    except OSError: return ImageFont.truetype(r"C:\Windows\Fonts\consolab.ttf", size)

title_font = load_font(r"C:\Windows\Fonts\segoeuib.ttf", 30)
sub_font   = load_font(r"C:\Windows\Fonts\segoeui.ttf", 21)

BLUE = (31, 119, 180); RED = (214, 39, 40)
GAP, PAD, HEAD = 46, 40, 78
BORDER = (223, 226, 229)

panel_w = max(img_pd.width, img_bs.width)
code_h  = max(img_pd.height, img_bs.height)
panel_h = HEAD + code_h
W = PAD*2 + panel_w*2 + GAP
H = PAD*2 + panel_h + 20   # +caption strip

canvas = Image.new("RGB", (W, H), "white")
d = ImageDraw.Draw(canvas)

def panel(x0, code_img, accent, title, subtitle):
    y0 = PAD
    x1, y1 = x0 + panel_w, y0 + panel_h
    # card border + header underline accent
    d.rectangle([x0, y0, x1, y1], outline=BORDER, width=2)
    d.rectangle([x0, y0, x1, y0 + HEAD], fill=(250, 251, 252))
    d.line([x0, y0 + HEAD, x1, y0 + HEAD], fill=BORDER, width=2)
    d.rectangle([x0, y0, x0 + 8, y1], fill=accent)          # left accent bar
    d.text((x0 + 30, y0 + 14), title, font=title_font, fill=(36, 41, 46))
    d.text((x0 + 30, y0 + 48), subtitle, font=sub_font, fill=(106, 115, 125))
    canvas.paste(code_img, (x0 + 8, y0 + HEAD + 6))

panel(PAD, img_pd, BLUE, "PD  (linear)",
      "filtered-rate damping - no model inversion")
panel(PAD + panel_w + GAP, img_bs, RED, "Backstepping  (nonlinear)",
      "computed torque - inverts the plant model")

cap = "Python control laws (helicopter_2dof, u = [u_p, u_y], state x = [theta, theta_dot, psi, psi_dot])"
d.text((PAD + 4, H - 30), cap, font=sub_font, fill=(120, 128, 136))

canvas.save(OUT, dpi=(220, 220))
print("SAVED", OUT, canvas.size)
