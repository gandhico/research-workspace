from __future__ import annotations

from pathlib import Path
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    Image,
    KeepTogether,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

BUILD = Path(r"C:\Research\presentations\ACC2027_CMG_Research_Update_build")
OUTPUT = Path(r"C:\Research\presentations\ACC2027_CMG_PES_Slide_by_Slide_Speech_Study_Guide.pdf")
SLIDE_DIR = BUILD / "powerpoint_render5"
ACC = Path(r"C:\Research\papers\ACC2027_Gate_Residual_Control")
HOVER = Path(r"C:\Research\hover3dof")

MAROON = colors.HexColor("#8C0B41")
DARK_MAROON = colors.HexColor("#5F0027")
BLUE = colors.HexColor("#50B9F2")
GRAY = colors.HexColor("#6D6E71")
LIGHT_GRAY = colors.HexColor("#E7E6E6")
PALE = colors.HexColor("#F7F3F5")
GREEN = colors.HexColor("#238B57")
AMBER = colors.HexColor("#C47C15")
RED = colors.HexColor("#B3261E")

pdfmetrics.registerFont(TTFont("Arial", r"C:\Windows\Fonts\arial.ttf"))
pdfmetrics.registerFont(TTFont("Arial-Bold", r"C:\Windows\Fonts\arialbd.ttf"))
pdfmetrics.registerFont(TTFont("Arial-Italic", r"C:\Windows\Fonts\ariali.ttf"))

styles = getSampleStyleSheet()
styles.add(ParagraphStyle(name="CoverTitle", fontName="Arial-Bold", fontSize=24, leading=29, textColor=MAROON, alignment=TA_CENTER, spaceAfter=12))
styles.add(ParagraphStyle(name="CoverSub", fontName="Arial-Bold", fontSize=14, leading=18, textColor=GRAY, alignment=TA_CENTER, spaceAfter=12))
styles.add(ParagraphStyle(name="SlideTitle", fontName="Arial-Bold", fontSize=20, leading=24, textColor=DARK_MAROON, spaceAfter=8))
styles.add(ParagraphStyle(name="Section", fontName="Arial-Bold", fontSize=12.5, leading=15, textColor=MAROON, spaceBefore=10, spaceAfter=5))
styles.add(ParagraphStyle(name="BodyStudy", fontName="Arial", fontSize=10.2, leading=14.2, textColor=colors.HexColor("#1B1B1B"), alignment=TA_JUSTIFY, spaceAfter=6))
styles.add(ParagraphStyle(name="BodySmall", fontName="Arial", fontSize=8.8, leading=11.5, textColor=colors.HexColor("#222222"), spaceAfter=4))
styles.add(ParagraphStyle(name="Speech", fontName="Arial", fontSize=10.4, leading=14.6, textColor=colors.HexColor("#111111"), alignment=TA_LEFT, leftIndent=10, rightIndent=10, borderColor=MAROON, borderWidth=0.6, borderPadding=8, backColor=PALE, spaceAfter=8))
styles.add(ParagraphStyle(name="Equation", fontName="Arial", fontSize=9.8, leading=13, textColor=DARK_MAROON, alignment=TA_CENTER, borderColor=BLUE, borderWidth=0.5, borderPadding=6, backColor=colors.white, spaceAfter=4))
styles.add(ParagraphStyle(name="Callout", fontName="Arial-Bold", fontSize=9.5, leading=13, textColor=DARK_MAROON, borderColor=AMBER, borderWidth=0.8, borderPadding=7, backColor=colors.HexColor("#FFF8EA"), spaceBefore=5, spaceAfter=6))
styles.add(ParagraphStyle(name="Caption", fontName="Arial-Italic", fontSize=8.2, leading=10.5, textColor=GRAY, alignment=TA_CENTER, spaceAfter=7))
styles.add(ParagraphStyle(name="TOC", fontName="Arial", fontSize=10.5, leading=15, textColor=colors.HexColor("#222222"), leftIndent=8, spaceAfter=3))
styles.add(ParagraphStyle(name="Footer", fontName="Arial", fontSize=7.5, leading=9, textColor=GRAY, alignment=TA_CENTER))


def P(text: str, style: str = "BodyStudy") -> Paragraph:
    return Paragraph(escape(text).replace("\n", "<br/>") , styles[style])


def H(text: str) -> Paragraph:
    return P(text, "Section")


def equation(text: str) -> Paragraph:
    return P(text, "Equation")


def slide_image(number: int) -> Image:
    path = SLIDE_DIR / f"Slide{number}.PNG"
    image = Image(str(path))
    image._restrictSize(7.25 * inch, 4.08 * inch)
    image.hAlign = "CENTER"
    return image


def study_image(path: Path, max_width=6.9 * inch, max_height=7.3 * inch) -> Image:
    image = Image(str(path))
    image._restrictSize(max_width, max_height)
    image.hAlign = "CENTER"
    return image


def make_table(rows, widths=None, header=True, font_size=8.4):
    data = [[P(str(cell), "BodySmall") for cell in row] for row in rows]
    table = Table(data, colWidths=widths, repeatRows=1 if header else 0, hAlign="CENTER")
    commands = [
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("GRID", (0, 0), (-1, -1), 0.35, LIGHT_GRAY),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("FONTNAME", (0, 0), (-1, -1), "Arial"),
        ("FONTSIZE", (0, 0), (-1, -1), font_size),
    ]
    if header:
        commands += [
            ("BACKGROUND", (0, 0), (-1, 0), MAROON),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Arial-Bold"),
        ]
    for row_index in range(1 if header else 0, len(rows)):
        if row_index % 2 == 1:
            commands.append(("BACKGROUND", (0, row_index), (-1, row_index), PALE))
    table.setStyle(TableStyle(commands))
    return table


def bullet_list(items):
    return [P(f"• {item}", "BodyStudy") for item in items]


def on_page(canvas, doc):
    canvas.saveState()
    canvas.setFillColor(MAROON)
    canvas.rect(0, letter[1] - 22, letter[0], 22, stroke=0, fill=1)
    canvas.setFont("Arial", 7.5)
    canvas.setFillColor(GRAY)
    canvas.drawString(0.65 * inch, 0.38 * inch, "ACC 2027 CMG-PES presentation - technical speech and study guide")
    canvas.drawRightString(letter[0] - 0.65 * inch, 0.38 * inch, f"Page {doc.page}")
    canvas.restoreState()


slides = [
    {
        "n": 1,
        "title": "Opening title and research identity",
        "purpose": "Establish the contribution as constrained online residual control, not as a neuron demonstration in isolation.",
        "speech": [
            "Good morning. This presentation reports our current ACC 2027 result on online PES-adapted neuromorphic membrane-gate residual control for actuator-constrained UAV quaternion attitude tracking. The central idea is simple: we keep a conventional nominal controller in charge, then learn only a bounded corrective residual online. The correction is generated from coupled membrane and gate states and decoded through a PES-adapted weight matrix.",
            "The current evidence has two layers. First, we have a matched MuJoCo campaign on the Skydio X2 model and a Crazyflie-class four-rotor authority design study. Second, we have the first physical transfer to the Quanser 3DOF Hover using the vendor LQR and a residual limited to 3 volts. I will separate what is already demonstrated from what still requires repeated trials.",
            "The result I want you to remember is not merely that a neural state exists. It is that online decoder adaptation produces large improvements in the simulated moving-reference tasks while the residual remains bounded and the nominal controller remains primary. On hardware, the gains are smaller but positive in all three tested dynamic conditions under a deliberately conservative authority limit.",
        ],
        "technical": [
            "Title phrase 'Online PES-Adapted' means the decoder weights are updated during the same trajectory being evaluated. This is adaptation, not offline training and not zero-shot generalization.",
            "'Neuromorphic Membrane-Gate' refers to a dynamical state encoder with coupled membrane state v and gate state r. The current controller decodes a continuous amplified gate activity, not discrete output spikes.",
            "'Residual control' means the learned term is added to the nominal command. It does not replace PD or LQR.",
            "'Actuator-constrained' means the residual and final command are bounded, and the CF2 claim is explicitly conditioned on available rotor authority.",
            "'Quaternion attitude tracking' is the primary UAV problem. Euler angles are used only for human-readable plots; the MuJoCo control law operates on quaternion error.",
        ],
        "boundary": "Do not begin by claiming that the CMG unit is inherently better than LIF, ALIF, or Izhikevich neurons. The present evidence isolates online PES decoder adaptation as the main source of improvement. Comparative neuron-model validation remains future work.",
        "qa": [
            ["Likely question", "Recommended response"],
            ["What is the main contribution?", "A bounded additive residual architecture whose decoder adapts online with PES while a nominal controller remains primary, demonstrated across matched MuJoCo cases and transferred conservatively to physical hardware."],
            ["Is this end-to-end neural control?", "No. It is residual augmentation of PD or LQR, with explicit saturation and limited residual authority."],
            ["Is this already statistically conclusive?", "The MuJoCo runs are deterministic trajectory-level evidence. The current 3DOF hardware table is n=1 per condition and is not yet a statistical robustness claim."],
        ],
        "transition": "I will first state the evidence contract, then show the architecture, equations, simulated results, actuator boundary, and hardware transfer.",
    },
    {
        "n": 2,
        "title": "The research claim in one slide",
        "purpose": "Give the audience the quantitative result and the evidence boundary before introducing details.",
        "speech": [
            "This slide is the evidence contract for the entire talk. A bounded online PES residual improves quaternion tracking while leaving the nominal controller in command. In the X2 simulation, the largest improvement is 60.6 percent on yaw360. Across the five X2 missions and the five CF2 authority-design missions, all ten tested comparisons improve.",
            "On the physical 3DOF Hover, the best current improvement is 7.05 percent on yaw360. The residual is limited to 3 volts out of a 24-volt command range, which is 12.5 percent and is rounded to approximately 13 percent on the slide.",
            "The lower callout is intentionally conservative. The result supported now is online decoder adaptation. We have not yet proven that the CMG state encoder is superior to all other neuron models, and the hardware data are not yet multi-trial statistics.",
        ],
        "technical": [
            "The 60.6 percent value is computed from X2 yaw360 mean quaternion-error magnitude: (0.075863 - 0.029902) / 0.075863 x 100 = 60.6 percent.",
            "The 10 of 10 count covers X2 and the CF2 1.5x rotor-authority design point over yaw360, full3, hard45, hardstep, and roll. The stock CF2 XML is not part of that headline count because it is severely authority-limited.",
            "The 7.05 percent hardware value is computed from mean combined yaw-pitch-roll error: (9.696 - 9.013) / 9.696 x 100 = 7.05 percent.",
            "The 13 percent card is a rounded authority ratio: 3 V / 24 V = 0.125 = 12.5 percent. It does not mean the residual actually uses 3 V continuously; it is the configured absolute cap.",
        ],
        "values": [
            ["Card", "Exact meaning", "Important qualification"],
            ["+60.6%", "Best X2 improvement, yaw360", "Adaptation occurs on the evaluation trajectory"],
            ["10 / 10", "All matched MuJoCo mission-platform comparisons improve", "CF2 values use the explicit 1.5x authority design point"],
            ["+7.05%", "Best 3DOF Hover improvement, yaw360", "One run per controller and condition"],
            ["13%", "3 V residual cap divided by 24 V", "Final hardware command remains nonnegative"],
        ],
        "boundary": "Use the phrases 'demonstrated improvement' and 'transfer evidence.' Avoid 'proof of superiority,' 'robust hardware validation,' and 'stock Crazyflie result.'",
        "qa": [
            ["Likely question", "Recommended response"],
            ["Why only 7 percent on hardware?", "The hardware residual has about 13 percent voltage authority, the plant is positive-voltage-only, the vendor LQR is stronger than the simulated PD baseline, and real noise reduces learning-signal quality."],
            ["Why are all ten simulation cases positive?", "The residual addresses repeatable structural tracking error, especially phase lag in moving references, while being bounded so it does not replace the baseline."],
        ],
        "transition": "The next slide shows exactly where the nominal command, neural state, decoder, residual bound, and plant connect.",
    },
    {
        "n": 3,
        "title": "Architecture: nominal control remains primary",
        "purpose": "Explain every signal and show that the learned path cannot bypass saturation.",
        "speech": [
            "The signal flow begins with desired quaternion q-d, measured quaternion q, and measured body rate omega. We construct a quaternion attitude error and combine it with angular-rate information. That same tracking information supports two paths.",
            "The upper path is the nominal controller. In MuJoCo it is a quaternion PD-like law. On the 3DOF Hover it is the vendor state-feedback LQR. This produces u-zero, the command that would be applied if the residual were disabled.",
            "The lower path is the adaptive residual. The error-derived input drives the coupled membrane-gate state encoder. The encoder produces gate activity a. A decoder matrix W maps this population activity into a normalized residual direction. That direction is scaled by channel-specific residual limits and multiplied by beta.",
            "The two paths meet at the summing and saturation block. The applied command is u equals sat of u-zero plus beta delta-u. Therefore the nominal controller remains present at every sample, and the learned path never bypasses the final actuator constraint.",
        ],
        "equations": [
            ["Expression", "Meaning"],
            ["q-tilde = q-d inverse tensor-product q", "Relative attitude between desired and measured orientation; the implementation uses the project quaternion convention."],
            ["e-q = signed vector part of q-tilde", "Three-axis shortest-rotation attitude error used by the nominal and residual logic."],
            ["u-zero = -K-q e-q - K-omega omega", "Representative MuJoCo quaternion PD-like baseline."],
            ["delta-u = W a elementwise-multiplied by u-res-bar", "Decoder output scaled to physical residual limits by channel."],
            ["u = sat(u-zero + beta delta-u)", "Additive residual command after final actuator saturation."],
        ],
        "technical": [
            "For a three-axis torque interface, u, u-zero, and delta-u are three-vectors. For rotor or voltage interfaces, the control dimension equals the number of actuators after the platform allocation/mapping step.",
            "The error vector and decoder target must not be a tautological copy of the nominal command. The hardware bring-up showed that using essentially the same signal for gate drive and supervision can produce activity without useful corrective learning.",
            "The architecture is platform-independent at the controller level, but every plant adapter is responsible for state conventions, actuator allocation, units, channel order, saturation, and safety behavior.",
            "MuJoCo supplies rigid-body dynamics, contacts, joint/actuator integration, sensor/state access, and deterministic stepping. Our Python loop computes the reference, reads q and omega, calls the nominal controller and CMG-PES augmentor, then writes actuator commands before the next mj_step."],
        "boundary": "Do not describe W a as a direct motor command until platform-specific scaling and allocation are explained. The mathematical residual is normalized first; physical units enter through the residual-limit vector and plant adapter.",
        "qa": [
            ["Likely question", "Recommended response"],
            ["Can the neural path destabilize the system?", "It can degrade performance if learning is too aggressive, as the hardware tuning sweep showed. The safeguards are a strong nominal loop, projected decoder weights, beta scaling, channel-specific residual limits, and final saturation."],
            ["Is the controller the same across platforms?", "The CMG-PES core and additive structure are shared. State extraction, nominal controller, actuator allocation, units, and safety constraints are platform-specific adapters."],
        ],
        "transition": "Now I will define the membrane state, gate state, decoded activity, and PES update mathematically.",
    },
    {
        "n": 4,
        "title": "Coupled membrane-gate dynamics and PES learning",
        "purpose": "Define every equation and isolate state encoding from online decoder adaptation.",
        "speech": [
            "Each CMG unit has two continuous states. The membrane state v integrates the input current I with leakage and a gate-dependent conductance. The gate state r moves toward a sigmoid target whose effective threshold depends on r itself. This makes v and r dynamically coupled.",
            "The first equation says that r relaxes toward sigma of alpha times v minus the effective threshold v-th minus gamma r. Tau-r controls how quickly the gate follows that target, and alpha controls sigmoid steepness.",
            "The second equation is the membrane ODE. The first term pulls v toward the resting potential. The input term injects current. The final conductance term pulls v toward the reset potential with strength c. The conductance is proportional to r squared and can optionally scale with input magnitude when adaptive conductance is enabled.",
            "The controller does not decode spikes. It amplifies the continuous gate and clips it: a equals clip of ten-to-the-fifth r between zero and one. The decoder produces delta-u from W a, scaled elementwise by residual limits. PES then updates W toward an independently computed target y-star, with learning rate eta, weight leak lambda, and projection to the interval minus six to six.",
        ],
        "equations": [
            ["Equation", "Definition and interpretation"],
            ["r-dot = [sigma(alpha(v - (v-th - gamma r))) - r] / tau-r", "r is the gate state in [0,1]. sigma is the logistic function. alpha sets steepness. v-th - gamma r is the effective threshold. Larger r lowers this threshold in the written sign convention, reinforcing opening, while the r-squared conductance damps v."],
            ["v-dot = -(v - v-rest)/tau + I/tau - c(v - v-reset)", "v leaks toward v-rest, receives current I, and is pulled toward v-reset by the gate-dependent conductance c."],
            ["c = (g-zero + indicator-adapt g-one |I|) r-squared", "g-zero is base conductance. g-one adds input-dependent conductance only in the adaptive-conductance variant. r-squared makes the effect weak near a closed gate and strong after opening."],
            ["a = clip(10^5 r, 0, 1)", "Continuous decoder activity. Any r above approximately 10^-5 is clipped close to one, which is central to the fixed/adaptive equivalence observed here."],
            ["delta-u = W a elementwise-multiplied by u-res-bar", "W maps N activities to m normalized control channels. u-res-bar gives physical residual authority per channel."],
            ["W(k+1) = projection[-6,6]{W(k) + eta(y-star - W(k)a)a-transpose - lambda W(k)}", "Online delta-rule/PES update. The outer product assigns credit in proportion to activity. Projection prevents unbounded weights; lambda provides regularization/leak."],
        ],
        "technical": [
            "Dimensional view: v, r, and a are N-vectors; W is m by N; y-star and W a are m-vectors; u-res-bar and delta-u are m-vectors.",
            "Positive/negative branches can encode signed variables with nonnegative current: one unit receives the positive rectified part, a paired unit receives the negative rectified part, and the decoder can subtract them through W.",
            "The implementation uses an exponential membrane update for numerical stability rather than a naive Euler step when conductance becomes large. The displayed differential equation is the continuous model; the code integrates its linear-in-v step analytically for fixed step inputs.",
            "PES is not changing v or r directly. PES changes W, the decoder from state activity to residual command. Adaptive conductance changes c and therefore the internal state trajectory. These are separate adaptation mechanisms."],
        "boundary": "Do not say 'the gate alone learns.' The v-r dynamics generate activity; the PES rule learns decoder weights W. Also do not say 'adaptive CMG is better' in the present amplified-gate setting, because fixed and adaptive conductance give numerically identical headline outputs.",
        "qa": [
            ["Likely question", "Recommended response"],
            ["Is r the decoder?", "r is a dynamical gate state. The decoder input is the amplified and clipped activity a derived from r. The learned decoder itself is W."],
            ["Are both v and r involved?", "Yes. r depends on v and on its r-dependent threshold, while v depends on r through conductance c. Only the postprocessed gate activity is exposed to W in the present decoder."],
            ["Why project W to plus or minus six?", "Projection supplies an explicit bound on decoder parameters and limits runaway online adaptation. It complements, but does not replace, command saturation."],
        ],
        "transition": "With the mechanism defined, I will show whether the effect is broad across missions or isolated to one trajectory.",
    },
    {
        "n": 5,
        "title": "MuJoCo improvement across the full mission suite",
        "purpose": "Show the ten audited comparisons and explain why mission type controls the improvement magnitude.",
        "speech": [
            "This bar chart summarizes the matched MuJoCo mission suite. The maroon bars are X2 and the blue bars are the CF2 1.5-times authority design point. All ten bars are positive.",
            "The ranking is almost identical on both platforms. Yaw360 improves by 60.6 percent. Full3 improves by 56.6 percent on X2 and 56.1 percent on CF2. Hard45 improves by 53.1 and 53.7 percent. Hardstep remains positive at 20.9 and 18.4 percent. Roll improves by 17.4 and 17.3 percent.",
            "The mechanism is consistent with the mission structure. Persistent moving references expose repeatable phase lag and coupled tracking error that the online residual can learn. An instantaneous step is dominated at its peak by actuator-rate limits, so the residual mainly improves the settling tail. Roll is gentle and single-axis, leaving less baseline error to remove.",
        ],
        "values": [
            ["Platform", "Mission", "Classical qerr mean (rad)", "CMG-PES qerr mean (rad)", "Improvement"],
            ["X2", "yaw360", "0.075863", "0.029902", "60.6%"],
            ["X2", "full3", "0.303275", "0.131748", "56.6%"],
            ["X2", "hard45", "0.294082", "0.138007", "53.1%"],
            ["X2", "hardstep", "0.454528", "0.359355", "20.9%"],
            ["X2", "roll", "0.050565", "0.041785", "17.4%"],
            ["CF2 1.5x", "yaw360", "0.075812", "0.029870", "60.6%"],
            ["CF2 1.5x", "full3", "0.288383", "0.126476", "56.1%"],
            ["CF2 1.5x", "hard45", "0.285449", "0.132319", "53.7%"],
            ["CF2 1.5x", "hardstep", "0.426182", "0.347886", "18.4%"],
            ["CF2 1.5x", "roll", "0.051337", "0.042439", "17.3%"],
        ],
        "technical": [
            "Matched configuration: simulation step dt = 0.0005 s, beta = 0.5, PES learning rate eta = 8e-4, k-error = 8, k-rate = 0, and duration = 45 s.",
            "Improvement is 100 times (classical metric - CMG metric) divided by the classical metric. Positive values mean lower error under CMG-PES.",
            "The source audit calls the metric qerr mean or mean quaternion-error magnitude. The slide chart says RMS attitude-error improvement. For the meeting, call the metric mean quaternion attitude-error magnitude unless code inspection confirms an RMS aggregation. The numerical values above are the authoritative audited values.",
            "The static hover mission is omitted because both deterministic controllers reach exactly zero in the noiseless setup, giving no comparative information.",
            "The Claude artifact reference on the slide was supplied by the author but remained behind private sign-in during deck construction. None of the numerical claims depends on that artifact; all values are from local audited result files."],
        "boundary": "The runs show repeatable deterministic trajectory-level improvement. They do not by themselves establish disturbance rejection, hold-out generalization, sensitivity to initialization, or cross-seed statistics.",
        "qa": [
            ["Likely question", "Recommended response"],
            ["Why is hardstep improvement smaller?", "The step-edge peak is limited by actuator rate/authority for both controllers. CMG-PES improves the post-step settling more than the instantaneous peak."],
            ["Why is roll smallest?", "The nominal baseline already has low error on the gentle single-axis motion, so there is less residual structure to learn."],
            ["Are X2 and CF2 really identical?", "They are not numerically identical, but the mission ranking and percentages are very close under the matched authority design, indicating the mechanism is not unique to one airframe."],
        ],
        "transition": "The next three slides move from the summary bars to the time histories behind the strongest results.",
    },
    {
        "n": 6,
        "title": "X2 Hard45 time-history result",
        "purpose": "Explain the six-panel comparison and the 53.07 percent headline result.",
        "speech": [
            "Hard45 is the headline coupled maneuver. It is multi-axis and multi-frequency, with moderate-large angles, so it reveals structural tracking error without relying on an unrealizable discontinuity.",
            "The first three panels compare desired and measured Euler angles for the three attitude axes. The Euler conversion is only for visualization; the control and headline metric remain quaternion-based. The CMG-PES traces follow the reference more closely through the repeated oscillations.",
            "The error panel overlays the quaternion-error magnitude for the classical and CMG-PES runs. The mean decreases from 0.294082 radians to 0.138007 radians. The relative reduction is 53.07 percent, rounded to 53.1 percent on the slide.",
            "The lower command panels show that the improvement is achieved with bounded commands and no modeled rotor saturation in this audited X2 case. Beta is 0.5 and the PES learning rate is 8 times 10 to the minus four.",
        ],
        "values": [
            ["Quantity", "Value", "Interpretation"],
            ["Classical qerr mean", "0.294082 rad", "Nominal quaternion PD-like controller"],
            ["CMG-PES qerr mean", "0.138007 rad", "Nominal plus online adaptive residual"],
            ["Improvement", "53.07%", "Relative reduction in the audited mean metric"],
            ["beta", "0.5", "Residual scaling relative to configured residual limits"],
            ["eta", "8e-4", "PES decoder learning rate"],
            ["Modeled rotor saturation", "0%", "No rotor saturation in the headline X2 run"],
        ],
        "technical": [
            "Plot rows 1-3: output tracking for roll, pitch, and yaw in Euler degrees, with reference and controller traces. These angles are generated from logged quaternions by a ZYX conversion for plotting only.",
            "Plot row 4: combined quaternion attitude-error magnitude over time. The horizontal or annotated mean values produce the headline metric.",
            "Plot rows 5-6: actuator or torque-command histories for the compared controllers, used to check authority use and saturation behavior.",
            "The card says 'RMS improvement,' but the audited result table names the statistic qerr mean. Say 'mean quaternion-error reduction' in the meeting. This is a label correction, not a change to the numerical result.",
            "The fixed residual result for the same X2 Hard45 case is 0.263890 rad, a 10.27 percent improvement. The large additional reduction to 0.138007 is associated with online PES adaptation of W."],
        "boundary": "This is adaptation on the same 45-second trajectory that is scored. It is a strong online-control result, but it is not a hold-out or zero-shot learning experiment.",
        "qa": [
            ["Likely question", "Recommended response"],
            ["Could the improvement be an Euler-angle artifact?", "No. Euler angles are plotted for readability, but the audited metric and controller use quaternion error."],
            ["Is the residual simply using more actuator authority?", "The comparison uses the same actuator model and final limits. The commands remain unsaturated in this case, and the fixed residual with the same beta improves only 10.27 percent versus 53.07 percent with PES."],
        ],
        "transition": "Hard45 is not isolated. The next slide shows that persistent continuous references produce even larger improvements.",
        "plots": [ACC / "results" / "plots" / "x2_hard45_classical_vs_cmg.png"],
    },
    {
        "n": 7,
        "title": "Continuous references: yaw360 and full3",
        "purpose": "Explain why persistent reference motion supplies a coherent online learning signal.",
        "speech": [
            "The left plot is yaw360. The desired yaw progresses continuously through a full rotation. A fixed regulator without explicit reference-rate feedforward carries persistent lag. The CMG-PES residual observes a coherent error pattern and learns a repeatable correction, reducing mean quaternion error from 0.075863 to 0.029902 radians, or 60.6 percent.",
            "The right plot is full3, where all three attitude axes vary continuously. The mean error decreases from 0.303275 to 0.131748 radians, or 56.6 percent. This shows that the effect is not limited to single-axis yaw.",
            "In both cases, the residual has time to adapt to recurring structure. I describe this as empirical online learning of repeatable tracking correction. I do not describe it as formal convergence, because the present evidence is trajectory-level and does not include a proof or held-out mission.",
        ],
        "values": [
            ["Mission", "Classical", "CMG-PES", "Improvement", "Reference character"],
            ["X2 yaw360", "0.075863 rad", "0.029902 rad", "60.6%", "Continuous full-yaw ramp"],
            ["X2 full3", "0.303275 rad", "0.131748 rad", "56.6%", "Continuous three-axis oscillation"],
        ],
        "technical": [
            "Yaw360 is duration-dependent: the ramp spans the configured mission duration. A longer duration produces a slower, easier ramp, so only matched-duration controller comparisons are valid.",
            "Full3 is periodic and simultaneously excites all three axes, making it a useful coupled-dynamics test. Its high improvement suggests PES is compensating a systematic tracking gap rather than only correcting a single transient.",
            "The repeated pattern provides persistent excitation, but persistent excitation alone does not guarantee a stable optimal decoder under clipping, projection, and nonlinear plant dynamics. The claim remains empirical."],
        "boundary": "Do not compare yaw360 values across different mission durations. Do not call the result feedforward identification unless the learning target and resulting mapping are analyzed explicitly as such.",
        "qa": [
            ["Likely question", "Recommended response"],
            ["Why does yaw360 outperform Hard45?", "Yaw360 creates a highly coherent, continuously moving tracking error. Hard45 mixes frequencies and axes, making the correction less uniform."],
            ["Does PES memorize the trajectory?", "It adapts on the trajectory and can learn repeatable structure. The current experiment does not distinguish trajectory-specific adaptation from more general learned compensation; hold-out tests are planned."],
        ],
        "transition": "The next slide applies the same honesty to Crazyflie: the result is strong, but only at an explicitly stated actuator-authority design point.",
        "plots": [
            ACC / "results" / "plots" / "x2_yaw360_classical_vs_cmg.png",
            ACC / "results" / "plots" / "x2_full3_classical_vs_cmg.png",
        ],
    },
    {
        "n": 8,
        "title": "CF2 authority boundary",
        "purpose": "Present the strong CF2-class result without implying stock Crazyflie hardware capability.",
        "speech": [
            "The CF2 Hard45 result is a 53.7 percent reduction, from 0.285449 to 0.132319 radians, under a four-rotor model with 1.5-times authority. This is a useful future hardware design point, not a stock Crazyflie 2.x claim.",
            "The stock CF2 XML is not defensible for the headline experiment. In the audited stock setup, the classical case reaches approximately 99.88 percent rotor saturation and a much larger error. Under near-continuous saturation, the controller comparison is dominated by inadequate actuator authority rather than by the residual architecture.",
            "Therefore the fair statement is: if a CF2-class platform provides the modeled 1.5-times authority, the online residual reproduces the same mission ranking and approximately the same large improvements as X2. The next engineering task is to map that authority to a physically plausible motor, propeller, battery, and mixer configuration.",
        ],
        "values": [
            ["Quantity", "Value", "Meaning"],
            ["CF2 1.5x Hard45 classical", "0.285449 rad", "Matched authority-design baseline"],
            ["CF2 1.5x Hard45 CMG-PES", "0.132319 rad", "Online adaptive residual"],
            ["Improvement", "53.65% -> 53.7%", "Relative reduction in qerr mean"],
            ["Stock XML saturation", "99.88%", "Classical headline setup is almost continuously saturated"],
            ["Stock XML classical error", "about 2.458662 rad", "Authority-limited case, not used as headline comparison"],
        ],
        "technical": [
            "The Menagerie CF2 inertia is [2.3951e-5, 2.3951e-5, 3.2347e-5] kg m^2. With project angular-acceleration bounds [12, 12, 10] rad/s^2, inertia-derived torque bounds are approximately [2.87412e-4, 2.87412e-4, 3.23470e-4] N m.",
            "A historical learned runner used torque floors [0.03, 0.03, 0.02] N m. Those floors are about [104.38, 104.38, 61.83] times the inertia-derived bounds and thousands of times the XML moment-actuator authority. This historical comparison must not be presented as stock hardware feasibility.",
            "The XML documentation itself describes virtual moment limits as arbitrary. Thus the XML is useful for a model audit, not as a measured Crazyflie motor specification.",
            "A future hardware-applicable model should use rotor thrust and reaction-torque coefficients, mixer geometry, voltage/battery limits, motor speed dynamics, and experimentally defensible maximum rotor speeds."],
        "boundary": "Always say 'CF2 explicit four-rotor authority design study' or 'CF2-class 1.5x authority model.' Never say 'stock Crazyflie achieved 53.7 percent.'",
        "qa": [
            ["Likely question", "Recommended response"],
            ["Why not simply report the stock XML result?", "Because 99.88 percent saturation makes it an actuator-sizing failure. It would not isolate controller quality."],
            ["Is 1.5x physically achievable?", "It is a design hypothesis, not yet a hardware fact. It must be tied to a motor-propeller-battery configuration and then validated experimentally."],
            ["Does this weaken the paper?", "It strengthens the scientific framing by separating controller performance from actuator infeasibility and by making the hardware design requirement explicit."],
        ],
        "transition": "The next slide explains which part of the neural architecture actually causes the large improvement in the current regime.",
        "plots": [ACC / "results" / "plots" / "cf2_hard45_classical_vs_cmg.png"],
    },
    {
        "n": 9,
        "title": "Fixed and adaptive CMG are indistinguishable here",
        "purpose": "Explain the amplified-gate regime and attribute the large gain correctly to PES decoder adaptation.",
        "speech": [
            "This plot shows the membrane and gate states over the full mission and over the initial activation transient. The mean gate is approximately 0.963. Because the decoder activity is a equals clip of ten-to-the-fifth times r, almost any positive gate value above ten to the minus five becomes activity one.",
            "That amplification suppresses differences between the fixed-conductance and adaptive-conductance variants at the decoder input. Their internal v and r trajectories may not be mathematically identical at every instant, but after the large gain and clipping, the activities presented to W are numerically indistinguishable for this experiment. Consequently their control results are identical to reported precision.",
            "The large improvement instead comes from online PES adaptation of W. The fixed residual improves X2 Hard45 by 10.27 percent, from 0.294082 to 0.263890 radians. Adding online PES reduces the error further to 0.138007 radians, a 53.07 percent improvement.",
            "This is why the defensible claim is coupled membrane-gate state encoding with online PES decoder adaptation. We do not yet claim that this neuron model inherently outperforms LIF, ALIF, or Izhikevich neurons under a controlled comparison.",
        ],
        "values": [
            ["Controller variant", "X2 Hard45 qerr mean", "Improvement", "Interpretation"],
            ["Classical", "0.294082 rad", "baseline", "Nominal controller only"],
            ["Fixed residual", "0.263890 rad", "10.27%", "Fixed decoder, fixed conductance"],
            ["Adaptive-conductance residual", "0.263890 rad", "10.27%", "Conductance change hidden by amplified activity"],
            ["Online PES, fixed conductance", "0.138007 rad", "53.07%", "W adapts online"],
            ["Online PES, adaptive conductance", "0.138007 rad", "53.07%", "Same decoded result in this regime"],
            ["Mean gate state", "about 0.963", "not an error metric", "Gate is open for most of the run"],
        ],
        "technical": [
            "The full-mission membrane plot shows the long-term v behavior after activation. The full-mission gate plot shows r remaining mostly open. The zoomed panels show the fast startup transient where v rises, r opens, and conductance changes the membrane response.",
            "With gain 10^5, activity saturation begins at r approximately 10^-5. Therefore a gate mean of 0.963 is deep inside the clipped regime, not near the sensitive transition.",
            "If we want to test whether adaptive conductance adds value, we must reduce the gate gain, change the operating region, decode a less-saturated state combination, or design a task where v-r transient differences remain visible at the decoder.",
            "A fair neuron comparison must match input encoding, neuron count, decoder size, residual authority, learning rule, learning rate search budget, initialization, mission, and random seed. Otherwise a worse LIF/ALIF/Izhikevich result cannot be attributed solely to neuron dynamics."],
        "boundary": "Do not say 'HyperLIF learns 53 percent.' Say 'PES adaptation of the decoder produces the 53 percent result using CMG gate-state activity.' Both v and r participate in state dynamics, but W is the learned object.",
        "qa": [
            ["Likely question", "Recommended response"],
            ["Then why keep adaptive conductance?", "It is a meaningful architectural degree of freedom, but the current amplified decoder masks it. We retain it as a hypothesis and will test it in a non-saturated activity regime."],
            ["Is CMG just a filter?", "It is a coupled nonlinear dynamical encoder with membrane leakage, gate feedback, and gate-dependent conductance. However the control benefit must be demonstrated empirically against matched alternative state encoders."],
            ["Can r alone explain the result?", "The decoded activity comes from r, but r is generated by coupled v-r dynamics. The large performance difference between fixed and PES cases is due to adaptation of W, not merely the presence of r."],
        ],
        "transition": "Having isolated the mechanism in simulation, I will show how the same residual structure was transferred to physical hardware without bypassing the vendor safety loop.",
        "plots": [ACC / "results" / "plots" / "x2_hard45_neuron_activity.png"],
    },
    {
        "n": 10,
        "title": "3DOF Hover transfer architecture",
        "purpose": "Explain the hardware signal chain, safety constraints, parameter set, and four implementation corrections.",
        "speech": [
            "The physical transfer begins with the three encoders. We tare the initial angles, compute filtered rates, and form the six-state vector of yaw, pitch, roll, and their rates. The vendor LQR produces the nominal four-motor voltage command.",
            "The CMG-PES path computes a bounded residual and adds it to the nominal command. Set E uses beta 0.4, a maximum residual of 3 volts, a 24-volt command ceiling, learning rate 3 times 10 to the minus four, k-error 4, k-rate 0, and a 25-second matched run.",
            "The final hardware law is positive-voltage-only. Every motor command is constrained to the valid nonnegative range. The slide box that visually says plus-or-minus voltage should be interpreted as a signed residual correction before final saturation, not as permission to apply negative motor voltage. The physically applied command is in the interval zero to 24 volts.",
            "Four corrections were essential. We verified the real motor channel map. We added encoder tare and physically meaningful rate estimation. We corrected the safety bridge so it clips the residual rather than shrinking the entire LQR command. Finally, we separated the gate-drive signal from the PES target so the learner was not supervised by a tautological copy of its own baseline direction.",
        ],
        "values": [
            ["Parameter or signal", "Value / definition", "Reason"],
            ["State x", "[yaw, pitch, roll, yaw-rate, pitch-rate, roll-rate]", "Vendor-style six-state feedback"],
            ["Motor channels", "AO0 front, AO1 back, AO2 left, AO3 right", "Physically verified on this rig"],
            ["beta", "0.4", "Residual blend/scale"],
            ["Maximum residual", "3.0 V per channel", "Bounded outside the augmentor"],
            ["Final command range", "0 to 24 V", "Positive-voltage-only hardware requirement"],
            ["PES learning rate", "3e-4", "Slower than the unstable 8e-4 setting"],
            ["k-error", "4", "Learning-target error gain"],
            ["k-rate", "0", "Rate term disabled in recommended Set E"],
            ["Duration", "25 s", "Matched baseline and CMG comparisons"],
            ["Authority ratio", "3 / 24 = 12.5% -> about 13%", "Configured residual cap"],
        ],
        "technical": [
            "The vendor documentation warns that rapid positive-negative switching can damage the amplifier because of low motor resistance. The final stage must clamp each motor voltage to a nonnegative value.",
            "The rig's amplifier gain was confirmed as 3, consistent with the vendor setup. DAQ voltage and actual motor-equivalent voltage must always be interpreted through that gain.",
            "The vendor figure and table disagreed on motor mapping. Physical single-channel tests established AO0 front, AO1 back, AO2 left, AO3 right for this unit.",
            "A higher-authority/faster-learning configuration caused severe Hard45 regression. Set E shows that authority alone was not the problem: reducing eta from 8e-4 to 3e-4 and k-error from 8 to 4 made the same beta 0.4 and 3 V authority behave safely.",
            "The residual target must be independent enough to represent missing correction. If gate drive and target are the same rescaled baseline signal, activity can be high while the learned residual adds little new control information."],
        "boundary": "The 3DOF Hover is a fixed-base rotational testbed, not a free-flying UAV. Present it as a physically constrained hardware transfer of the residual architecture, not as direct Crazyflie or Skydio flight validation.",
        "qa": [
            ["Likely question", "Recommended response"],
            ["Why no negative voltage?", "The vendor hardware law and amplifier safety guidance require nonnegative motor voltage. Negative residual intent is realized by reducing one positive channel relative to another, never by commanding negative motor voltage."],
            ["Why was k-rate zero?", "The Set F rate-feedback test underperformed Set E on all three missions, likely because filtered derivative noise/lag did not provide a useful target at the tested gain."],
            ["What does the 13 percent mean?", "It is the maximum configured residual voltage divided by the 24 V ceiling, not the average residual usage and not total plant authority."],
        ],
        "transition": "The next slide reports the final Set E numbers and immediately states the n equals one evidence boundary.",
    },
    {
        "n": 11,
        "title": "3DOF Hover Set E result table and Hard45 plot",
        "purpose": "Present the three positive hardware comparisons without overstating robustness.",
        "speech": [
            "Under Set E, all three tested dynamic missions improve relative to the matched vendor LQR baseline. Yaw360 decreases from 9.696 to 9.013 degrees, a 7.05 percent improvement. Full3 decreases from 12.367 to 12.061 degrees, a 2.47 percent improvement. Hard45 decreases from 12.954 to 12.795 degrees, a 1.23 percent improvement.",
            "The plot shows Hard45 because it is the most coupled maneuver and the hardest hardware case to improve. The first three panels show true measured yaw, pitch, and roll against reference. The fourth panel shows the combined tracking-error magnitude. The final panels show all four real motor-voltage channels.",
            "The improvement is small, but the important physical result is that the residual remains mechanically correct and bounded while preserving a maximum error essentially equal to the baseline. The current evidence is one run per controller and condition, so I describe this as safe transfer evidence, not statistical robustness.",
        ],
        "values": [
            ["Mission", "LQR mean combined error", "CMG-PES mean combined error", "Improvement"],
            ["yaw360", "9.696 deg", "9.013 deg", "7.05%"],
            ["full3", "12.367 deg", "12.061 deg", "2.47%"],
            ["hard45", "12.954 deg", "12.795 deg", "1.23%"],
        ],
        "technical": [
            "These hardware values are mean combined yaw-pitch-roll tracking-error magnitudes in degrees. They are not the same metric or units as the MuJoCo quaternion-error values in radians.",
            "Hard45 baseline maximum error was approximately 31.835 degrees. Under Set E the maximum was approximately 31.87 degrees, essentially unchanged, unlike the earlier aggressive configuration that increased the maximum dramatically.",
            "The plot's dotted mean lines summarize each run. Motor-voltage panels are important because an error reduction is not meaningful if obtained through unsafe clipping, asymmetric saturation, or excessive voltage.",
            "One run per cell means the percent differences could be sensitive to initialization, encoder noise, timing jitter, or run-to-run mechanical conditions. The next defensible experiment is at least five repeats per condition with mean, standard deviation, peak error, saturation fraction, and residual-energy metrics."],
        "boundary": "Say 'all three single-run comparisons improved under Set E.' Do not say 'hardware performance is robust' or 'the architecture consistently improves hardware' until repeated trials are complete.",
        "qa": [
            ["Likely question", "Recommended response"],
            ["Is 1.23 percent meaningful?", "It is evidence of correct bounded transfer in the hardest condition, but n=1 is insufficient to establish significance. The repeated-trial campaign is the next step."],
            ["Why show Hard45 if yaw360 is better?", "Hard45 is the most coupled and difficult maneuver. Showing it prevents cherry-picking the easiest percentage and demonstrates that the residual does not destabilize the hard case under Set E."],
            ["Why are the units degrees here?", "The Hover has physical yaw, pitch, and roll joints. The drone metric is quaternion-error magnitude in radians; the metrics should not be numerically compared as identical quantities."],
        ],
        "transition": "The next slide shows the other two hardware time histories, including the best hardware improvement.",
        "plots": [HOVER / "results" / "plots" / "set_e_final" / "hard45_classical_vs_cmg.png"],
    },
    {
        "n": 12,
        "title": "3DOF Hover yaw360 and full3 time histories",
        "purpose": "Explain the best hardware result and the consistency of small bounded corrections across continuous references.",
        "speech": [
            "The left plot is yaw360, the best current hardware condition. The mean combined error decreases by 7.05 percent. The desired yaw is a ramp over the full 25 seconds, so duration must remain matched between controllers.",
            "The right plot is full3. All three axes vary and the mean error decreases by 2.47 percent. The four motor-voltage traces remain noisy because they are real measured hardware commands, but the residual is deliberately small relative to the 24-volt ceiling.",
            "These plots support the claim that the residual transfers across more than one trajectory. They do not show the 17 to 61 percent simulation gains because the hardware has a stronger nominal LQR, a positive-voltage-only actuator law, real friction and sensor noise, and a residual capped at approximately 13 percent of the voltage range.",
        ],
        "values": [
            ["Mission", "LQR", "CMG-PES", "Improvement", "Key interpretation"],
            ["yaw360", "9.696 deg", "9.013 deg", "7.05%", "Best hardware result; coherent continuous ramp"],
            ["full3", "12.367 deg", "12.061 deg", "2.47%", "Three-axis continuous motion"],
        ],
        "technical": [
            "Yaw360 duration is part of the reference definition. A 25-second ramp is slower than a 10-second ramp; compare only matched-duration LQR and CMG runs.",
            "The residual can request signed corrections internally, but final physical commands are positive motor voltages. Differential motor action produces signed torques.",
            "Real encoder quantization, filtered-rate lag, friction, motor mismatch, and timing jitter dilute the clean error-to-correction relation available in MuJoCo.",
            "The vendor LQR is tuned for the identified linearized plant and is a stronger baseline than the simple quaternion PD-like drone controller. A smaller residual gap is therefore expected."],
        "boundary": "Do not directly compare 7.05 percent hardware and 60.6 percent MuJoCo as though only the plant changed. The nominal controller, metric, authority, constraints, noise, and reference realization also differ.",
        "qa": [
            ["Likely question", "Recommended response"],
            ["Could the residual simply be exploiting noise?", "That is why repeated trials, randomized initial conditions, and residual-energy/error correlation analysis are needed. The current single-run result is transfer evidence, not a final statistical conclusion."],
            ["Why not increase the residual cap?", "Earlier aggressive settings produced severe overshoot. Set E shows that safe adaptation rate and target scaling matter as much as raw authority."],
        ],
        "transition": "The final technical slide separates what is supported now from the validation required before submission and the broader extensions for later work.",
        "plots": [
            HOVER / "results" / "plots" / "set_e_final" / "yaw360_classical_vs_cmg.png",
            HOVER / "results" / "plots" / "set_e_final" / "full3_classical_vs_cmg.png",
        ],
    },
    {
        "n": 13,
        "title": "Evidence boundary and ACC-ready plan",
        "purpose": "Tell the advisor exactly what is supported, what must be validated, and what should remain future work.",
        "speech": [
            "The left column lists what is supported now. All ten matched MuJoCo comparisons improve. Actuator authority is explicitly accounted for. The fixed-versus-PES comparison attributes the large improvement to online decoder adaptation. All three Set E hardware comparisons improve in their current single runs.",
            "The middle column lists what must be completed for a stronger submission. We need at least five hardware repeats per condition, locked or recorded initial-state procedures, explicit saturation and voltage metrics, and a controlled LIF, ALIF, and Izhikevich comparison before claiming neuron-model superiority.",
            "The right column lists extensions. QDrone can provide a more UAV-like virtual and later physical platform. The 3DOF Hover repeated-trial campaign is the nearest-term priority. QCar vision and spiking perception, and the pendulum as a generality test, are valuable but should not dilute the core ACC paper unless their results are complete and directly support the central claim.",
            "The proposed paper center of gravity is therefore UAV quaternion tracking with broad MuJoCo evidence and one carefully bounded hardware demonstration.",
        ],
        "technical": [
            "A strong repeated-trial protocol should predefine primary metric, run duration, initial conditions, random seeds, actuator caps, stop conditions, and exclusion rules before collecting results.",
            "Recommended reported statistics: mean and standard deviation of the primary error, median, maximum error, saturation fraction, residual RMS/energy, weight norm, gate mean, and safety-stop count.",
            "Recommended ablations: classical; fixed decoder; PES with fixed conductance; PES with adaptive conductance; matched LIF/ALIF/Izhikevich encoders; and optionally a linear filtered-feature residual with the same PES decoder to isolate whether coupled dynamics add value.",
            "Recommended generalization tests: new initial attitudes, held-out mission frequencies, mass/inertia perturbation, actuator effectiveness loss, sensor noise, delay, and disturbances. Freeze-W transfer can be evaluated separately from online adaptation."],
        "boundary": "Do not expand the ACC paper into pendulum, QCar vision, QDrone, CF2 hardware, and 3DOF hardware simultaneously unless the results are mature. A narrow, defensible paper is stronger than a broad collection of incomplete demonstrations.",
        "qa": [
            ["Likely question", "Recommended response"],
            ["What is the minimum next experiment?", "Five matched repeats of LQR and Set E on yaw360, full3, and Hard45, with locked initialization and full safety/actuator metrics."],
            ["Should pendulum or QCar be in ACC 2027?", "Only if they provide completed, directly comparable evidence without delaying the core UAV and hardware validation. Otherwise they belong in future work or a journal extension."],
            ["What would prove a CMG-specific benefit?", "A controlled encoder ablation with identical PES rule, neuron count, decoder capacity, residual authority, tuning budget, missions, and seeds, preferably including a simple non-neural dynamical feature baseline."],
        ],
        "transition": "I will close with the decision I am asking from the group for Friday and the immediate experimental priority.",
    },
    {
        "n": 14,
        "title": "Closing decision and advisor ask",
        "purpose": "End with a concrete decision rather than another technical detail.",
        "speech": [
            "My proposed decision for Friday is to present the mechanism honestly, lead with the audited MuJoCo result, and request approval to complete the repeated hardware trials as the immediate strengthening step.",
            "The paper already has a coherent technical spine: coupled membrane-gate state encoding, online PES decoder adaptation, bounded additive residual control, broad matched MuJoCo improvement, an explicit CF2 authority boundary, and a conservative physical transfer to the 3DOF Hover.",
            "The remaining work is not to add more claims. It is to make the evidence harder: repeat the hardware runs, lock the experimental protocol, report uncertainty and actuator metrics, correct the mean-versus-RMS wording, and complete a fair neuron-model ablation if we want a CMG-specific claim.",
            "The question I would like the advisor to answer is: do we agree that the ACC paper should remain centered on actuator-constrained UAV quaternion residual control, with the 3DOF result as bounded hardware evidence and QDrone, pendulum, and QCar reserved for follow-on strengthening or journal extension?",
        ],
        "technical": [
            "The closing phrase 'full draft plus reproducible runners next' means the manuscript, scripts, configurations, result tables, and commands should be frozen together so another session can reproduce the exact numbers.",
            "The supplied interactive Claude artifact is referenced in the slide notes, but the deck and this guide rely on local audited files. It should not be presented as an inspected source until access is confirmed.",
            "The best final one-sentence claim is: 'Online PES adaptation of a bounded CMG state-decoded residual reduced mean quaternion tracking error in all ten matched MuJoCo cases and produced small positive single-run improvements on a positive-voltage-only 3DOF hardware testbed.'"],
        "boundary": "End with the next decision and experiment. Do not end by implying submission readiness before the repeated hardware and wording corrections are complete.",
        "qa": [
            ["Likely question", "Recommended response"],
            ["What do you need from the advisor?", "Approval of the claim boundary and paper center of gravity, plus prioritization of repeated 3DOF/QDrone experiments over unrelated extensions."],
            ["What can be ready immediately?", "A complete draft using the audited MuJoCo table and current hardware transfer as preliminary evidence, with limitations stated explicitly."],
            ["What is the strongest sentence you can defend today?", "Online PES decoder adaptation produced large deterministic MuJoCo tracking improvements under explicit actuator accounting and small positive single-run improvements after conservative physical transfer."],
        ],
        "transition": "Thank you. I am ready to discuss the actuator model, PES target, metric definition, and repeated-trial plan in detail.",
    },
]


story = []

# Cover
story += [Spacer(1, 0.35 * inch), P("Online PES-Adapted Neuromorphic Membrane-Gate Residual Control", "CoverTitle")]
story += [P("Complete slide-by-slide speech, equation guide, plot interpretation, and technical defense notes", "CoverSub")]
story += [Spacer(1, 0.15 * inch), slide_image(1), Spacer(1, 0.18 * inch)]
story += [P("Prepared as a full study base for the ACC 2027 research meeting. This guide is deliberately more detailed than the spoken presentation. Use the suggested speech as a foundation, then shorten it to match the meeting time.", "Callout")]
story += [P("Accuracy note: the local audit records the simulated metric as mean quaternion-error magnitude, while two visible slide labels use the word RMS. This guide treats the audited mean metric as authoritative. The hardware final command is nonnegative 0-24 V, even though one slide box uses a plus-or-minus symbol for the pre-saturation correction.", "BodyStudy")]
story += [PageBreak()]

# How to use
story += [P("How to use this study guide", "SlideTitle")]
story += bullet_list([
    "Read each Suggested speech section aloud once without interruption.",
    "Study the Exact technical meaning and values until every symbol and percentage can be reconstructed.",
    "Use the Claim boundary language whenever a question could tempt an overstatement.",
    "Practice the likely questions in one-sentence and thirty-second versions.",
    "For a short meeting, speak only the first two or three speech paragraphs per slide; keep the rest for discussion.",
])
story += [H("Recommended 18-20 minute timing")]
timing = [["Slides", "Time", "Job"], ["1-2", "2 min", "Frame contribution and evidence contract"], ["3-4", "4 min", "Architecture and equations"], ["5-9", "8 min", "Simulation results, CF2 boundary, adaptation attribution"], ["10-12", "4 min", "Hardware implementation and results"], ["13-14", "2 min", "Evidence plan and advisor ask"]]
story += [make_table(timing, widths=[0.9*inch, 0.8*inch, 5.2*inch])]
story += [H("Table of contents")]
for slide in slides:
    story += [P(f"Slide {slide['n']}: {slide['title']}", "TOC")]
story += [P("Appendix A: Master numerical tables", "TOC"), P("Appendix B: Equation and symbol glossary", "TOC"), P("Appendix C: High-risk wording and safe replacements", "TOC"), PageBreak()]

for slide in slides:
    n = slide["n"]
    story += [P(f"Slide {n} - {slide['title']}", "SlideTitle"), slide_image(n), P(f"Figure: Final PowerPoint slide {n}.", "Caption")]
    story += [H("Purpose of the slide"), P(slide["purpose"])]
    story += [H("Suggested speech")]
    for paragraph in slide["speech"]:
        story += [P(paragraph, "Speech")]
    if slide.get("equations"):
        story += [H("Equation guide")]
        story += [make_table(slide["equations"], widths=[2.55*inch, 4.35*inch], font_size=8.1)]
    if slide.get("values"):
        story += [H("Exact values and how to describe them")]
        cols = len(slide["values"][0])
        if cols == 3:
            widths = [1.35*inch, 1.45*inch, 4.1*inch]
        elif cols == 4:
            widths = [1.15*inch, 1.45*inch, 1.45*inch, 2.85*inch]
        elif cols == 5:
            widths = [0.8*inch, 0.85*inch, 1.65*inch, 1.65*inch, 1.95*inch]
        else:
            widths = None
        story += [make_table(slide["values"], widths=widths, font_size=7.9)]
    story += [H("Exact technical meaning")]
    for paragraph in slide["technical"]:
        story += [P(paragraph)]
    story += [H("Claim boundary - what not to overstate"), P(slide["boundary"], "Callout")]
    story += [H("Likely questions and professional answers"), make_table(slide["qa"], widths=[2.0*inch, 4.9*inch], font_size=8.2)]
    story += [P(f"Transition: {slide['transition']}", "BodySmall")]

    for plot_index, plot in enumerate(slide.get("plots", []), start=1):
        if plot.exists():
            story += [PageBreak(), P(f"Slide {n} plot study view {plot_index}", "SlideTitle"), study_image(plot), P(str(plot), "Caption")]
            if n in (6, 7, 8, 11, 12):
                story += [P("Reading order: first inspect the three output/reference panels, then the combined error panel and its mean values, then the actuator-command panels. Confirm that the performance statement agrees with both the error trace and actuator behavior.", "Callout")]
            elif n == 9:
                story += [P("Reading order: compare full-mission membrane and gate states, then use the zoomed transient panels to see how v and r couple during activation. The key control observation is that the amplified gate activity is clipped for most of the run.", "Callout")]
    story += [PageBreak()]

# Appendix A
story += [P("Appendix A - Master numerical tables", "SlideTitle")]
story += [H("Matched MuJoCo mission suite")]
master_sim = [
    ["Platform", "Mission", "Classical", "CMG-PES", "Improvement"],
    ["X2", "yaw360", "0.075863 rad", "0.029902 rad", "60.6%"],
    ["X2", "full3", "0.303275 rad", "0.131748 rad", "56.6%"],
    ["X2", "hard45", "0.294082 rad", "0.138007 rad", "53.1%"],
    ["X2", "hardstep", "0.454528 rad", "0.359355 rad", "20.9%"],
    ["X2", "roll", "0.050565 rad", "0.041785 rad", "17.4%"],
    ["CF2 1.5x", "yaw360", "0.075812 rad", "0.029870 rad", "60.6%"],
    ["CF2 1.5x", "full3", "0.288383 rad", "0.126476 rad", "56.1%"],
    ["CF2 1.5x", "hard45", "0.285449 rad", "0.132319 rad", "53.7%"],
    ["CF2 1.5x", "hardstep", "0.426182 rad", "0.347886 rad", "18.4%"],
    ["CF2 1.5x", "roll", "0.051337 rad", "0.042439 rad", "17.3%"],
]
story += [make_table(master_sim, widths=[1.0*inch, 1.0*inch, 1.55*inch, 1.55*inch, 1.25*inch])]
story += [P("Simulation configuration: dt 0.0005 s; beta 0.5; eta 8e-4; k-error 8; k-rate 0; duration 45 s. Metric name in the audit: qerr mean / mean quaternion-error magnitude.", "Callout")]
story += [H("Final 3DOF Hover Set E")]
master_hw = [["Mission", "LQR", "CMG-PES", "Improvement"], ["yaw360", "9.696 deg", "9.013 deg", "7.05%"], ["full3", "12.367 deg", "12.061 deg", "2.47%"], ["hard45", "12.954 deg", "12.795 deg", "1.23%"]]
story += [make_table(master_hw, widths=[1.4*inch, 1.6*inch, 1.6*inch, 1.5*inch])]
story += [P("Hardware configuration: beta 0.4; maximum residual 3 V; final command 0-24 V; eta 3e-4; k-error 4; k-rate 0; duration 25 s; n=1 per controller-condition cell.", "Callout"), PageBreak()]

# Appendix B
story += [P("Appendix B - Equation and symbol glossary", "SlideTitle")]
glossary = [
    ["Symbol", "Meaning"],
    ["q-d, q", "Desired and measured unit quaternions"],
    ["q-tilde", "Relative quaternion error under the project convention"],
    ["e-q", "Three-vector attitude-error representation from q-tilde"],
    ["omega", "Measured body angular velocity"],
    ["u-zero", "Nominal PD or LQR control command"],
    ["v", "Continuous membrane-potential state"],
    ["r", "Continuous gate state, nominally in [0,1]"],
    ["I", "Input current or encoded controller/error drive"],
    ["tau, tau-r", "Membrane and gate time constants"],
    ["v-rest, v-reset, v-th", "Resting, reset, and threshold membrane parameters"],
    ["alpha", "Sigmoid steepness"],
    ["gamma", "Gate-dependent threshold-coupling coefficient"],
    ["c", "Gate-dependent membrane conductance"],
    ["g-zero, g-one", "Base and input-scaled conductance coefficients"],
    ["a", "Amplified and clipped gate activity decoded by W"],
    ["W", "Online-adapted decoder matrix"],
    ["y-star", "Independent normalized supervision target for decoder output"],
    ["eta", "PES learning rate"],
    ["lambda", "Decoder weight leak/regularization coefficient"],
    ["u-res-bar", "Per-channel physical residual limit vector"],
    ["beta", "Global residual scale in the additive controller"],
    ["sat", "Final actuator saturation or safety projection"],
]
story += [make_table(glossary, widths=[1.35*inch, 5.55*inch], font_size=8.5)]
story += [H("Core equations to reproduce from memory")]
for eq in [
    "r-dot = [sigma(alpha(v - (v-th - gamma r))) - r] / tau-r",
    "v-dot = -(v - v-rest)/tau + I/tau - c(v - v-reset)",
    "c = (g-zero + indicator-adapt g-one |I|) r-squared",
    "a = clip(10^5 r, 0, 1)",
    "delta-u = W a elementwise-multiplied by u-res-bar",
    "W(k+1) = projection[-6,6]{W(k) + eta(y-star - W(k)a)a-transpose - lambda W(k)}",
    "u = sat(u-zero + beta delta-u)",
]:
    story += [equation(eq)]
story += [PageBreak()]

# Appendix C
story += [P("Appendix C - High-risk wording and safe replacements", "SlideTitle")]
wording = [
    ["Avoid saying", "Use instead"],
    ["HyperLIF inherently beats LIF, ALIF, and Izhikevich", "The present CMG-PES architecture outperformed the nominal baseline; a matched neuron-model ablation is still required."],
    ["The adaptive neuron produced the 53 percent gain", "Online PES adaptation of decoder W produced the large gain in the current amplified-gate regime."],
    ["The gate learns", "The v-r dynamics generate activity; PES learns decoder weights W."],
    ["Stock Crazyflie improves 53.7 percent", "The CF2-class 1.5x rotor-authority design study improves 53.7 percent; the stock XML is authority-limited."],
    ["The hardware result is robust", "All three Set E single-run comparisons improved; repeated trials are required for robustness."],
    ["Hardware and MuJoCo use the same metric", "MuJoCo uses mean quaternion-error magnitude in radians; hardware uses mean combined yaw-pitch-roll error in degrees."],
    ["The hardware uses plus-or-minus 24 V", "The physical command is constrained to 0-24 V; signed torque arises through differential positive motor voltages."],
    ["The plot reports RMS error", "The audit reports qerr mean. Confirm the aggregation in code before using RMS wording."],
    ["The method generalizes", "The method adapts successfully on the evaluated trajectories; hold-out and perturbation tests remain future work."],
]
story += [make_table(wording, widths=[2.35*inch, 4.55*inch], font_size=8.5)]
story += [H("Final thirty-second summary")]
story += [P("We retain a nominal quaternion PD or hardware LQR controller and add a bounded residual decoded from coupled membrane-gate state activity. PES adapts the decoder online. Under matched MuJoCo conditions, all ten X2 and CF2-authority-design comparisons improve, with the strongest reductions near 60 percent on continuous references. The CF2 claim is explicitly conditioned on rotor authority. On the positive-voltage-only 3DOF Hover, Set E limits the residual to 3 V and produces small positive single-run improvements in all three tested dynamic missions. The next required step is repeated hardware trials and a matched neuron-model ablation.", "Speech")]
story += [H("Primary local evidence files")]
for source in [
    ACC / "docs" / "RESULTS_EXPLAINED.md",
    ACC / "docs" / "RESULT_AUDIT.md",
    ACC / "paper" / "acc2027_neuromorphic_gate_residual_draft.tex",
    HOVER / "docs" / "PROGRESS_2026-08-27.md",
    HOVER / "docs" / "SAFETY_CHECKLIST.md",
    Path(r"C:\Research\presentations\ACC2027_CMG_PES_Research_Update_2026-08-28.pptx"),
]:
    story += [P(str(source), "BodySmall")]

doc = SimpleDocTemplate(
    str(OUTPUT),
    pagesize=letter,
    rightMargin=0.6 * inch,
    leftMargin=0.6 * inch,
    topMargin=0.55 * inch,
    bottomMargin=0.62 * inch,
    title="ACC 2027 CMG-PES Slide-by-Slide Speech and Study Guide",
    author="Gandhico F. Roperos",
    subject="Technical presentation speech, equations, plots, values, tables, claim boundaries, and Q&A",
)
doc.build(story, onFirstPage=on_page, onLaterPages=on_page)
print(OUTPUT)
