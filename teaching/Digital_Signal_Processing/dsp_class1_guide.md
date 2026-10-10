# EE 545 – Digital Signal Processing II
## Foundations Refresher & MATLAB Companion — Prep for Class 1

**Instructor:** Chuck Creusere · **Textbook:** S.K. Mitra, *Digital Signal Processing: A Computer-Based Approach*, 4th Ed. (2011) · **Fall 2026, NMSU**

---

### 0. Where this course starts (from the actual syllabus)

EE 545 is pitched as a **first-year graduate DSP course**, and its official prerequisite is undergraduate DSP (an EE 395-equivalent). That means Chuck will move quickly through Mitra Ch. 1–4 (signals, sequences, LTI systems, DTFT, basic sampling) as *review*, and the real content of the semester is:

- Bandpass and **non-ideal sampling**
- Frequency-domain representations and their uses
- Digital **filter structures** for implementation
- Digital **filter design**
- Implementation issues and **finite word-length effects**
- Intro to **multirate** systems
- Intro to **2-D / higher-dimensional** processing
- Intro to **adaptive filtering** (time permitting)
- Intro to **statistical signal processing** (time permitting)

This guide rebuilds the undergrad foundations you need walking in the door (Mitra Ch. 1–4 notation, exactly as the book defines it) and ends by previewing the first "new" topic on the syllabus — bandpass sampling — so the jump from review to new material doesn't catch you flat-footed. Every concept below has a MATLAB block: run it as you read.

---

### 1. Complex exponentials (the language everything else is written in)

DSP represents signals as sums of complex exponentials because LTI systems don't distort them — only scale/phase-shift them. That single fact is why the DTFT, z-transform, and frequency response all exist.

Euler's formula:
$$e^{j\theta} = \cos\theta + j\sin\theta$$

A discrete complex exponential sequence:
$$x[n] = e^{j\omega n} = \cos(\omega n) + j\sin(\omega n)$$

where $\omega$ is *normalized* (radians/sample) frequency — this normalization is exactly why discrete-time frequency is always discussed mod $2\pi$.

```matlab
%% 1. Complex exponentials
n = 0:20;
omega = pi/6;                 % normalized frequency (rad/sample)
x = exp(1j*omega*n);

figure;
subplot(2,1,1); stem(n, real(x)); title('Re\{e^{j\omega n}\}'); xlabel('n');
subplot(2,1,2); stem(n, imag(x)); title('Im\{e^{j\omega n}\}'); xlabel('n');

figure;
plot(real(x), imag(x), 'o-'); axis equal; grid on;
title('Trajectory on the unit circle'); xlabel('Re'); ylabel('Im');
```

---

### 2. Discrete-time signals (Mitra §2.4)

Mitra denotes a sequence $x[n]$ (brackets — reserved for discrete time, vs. $x(t)$ for continuous time). Two building blocks:

**Unit sample (impulse) sequence**, Mitra Eq. (2.45):
$$\delta[n] = \begin{cases} 1, & n = 0 \\ 0, & n \neq 0 \end{cases}$$

**Unit step sequence**, Mitra Eq. (2.46):
$$u[n] = \begin{cases} 1, & n \geq 0 \\ 0, & n < 0 \end{cases}$$

Any sequence can be written as a weighted, time-shifted sum of impulses — the fact that makes convolution work:
$$x[n] = \sum_{k=-\infty}^{\infty} x[k]\,\delta[n-k]$$

```matlab
%% 2. Basic sequences
n = -5:10;
delta = double(n == 0);
u     = double(n >= 0);

figure;
subplot(2,1,1); stem(n, delta); title('\delta[n]'); xlabel('n'); ylim([-0.2 1.2]);
subplot(2,1,2); stem(n, u);     title('u[n]');      xlabel('n'); ylim([-0.2 1.2]);

% A causal exponential sequence x[n] = alpha^n u[n], |alpha| < 1
alpha = 0.8;
x = (alpha.^n) .* u;
figure; stem(n, x); title(['x[n] = ' num2str(alpha) '^n u[n]']); xlabel('n');
```

---

### 3. LTI systems & the convolution sum (Mitra §2.2.3, §4.4)

Every LTI system is completely characterized by its impulse response $h[n]$ (the output when the input is $\delta[n]$). The output for *any* input is the **convolution sum**, Mitra Eq. (2.20a):
$$y[n] = \sum_{k=-\infty}^{\infty} x[k]\,h[n-k] \;=\; x[n] \circledast h[n]$$

(Mitra uses a circled asterisk $\circledast$ for the convolution sum specifically to keep $*$ free for complex conjugation.)

Two properties worth having cold before this course: **stability** ($h[n]$ absolutely summable, $\sum |h[n]| < \infty$) and **causality** ($h[n] = 0$ for $n<0$).

```matlab
%% 3. Convolution sum
x = [1 2 3 4];          % length-4 input sequence
h = [1 1 1];             % length-3 impulse response (3-point moving average, unnormalized)
y = conv(x, h);           % MATLAB's built-in convolution sum

disp('y[n] ='); disp(y);
% length check: length(y) should equal length(x)+length(h)-1
fprintf('length(y) = %d, expected %d\n', length(y), length(x)+length(h)-1);

figure; stem(0:length(y)-1, y); title('y[n] = x[n] \circledast h[n]'); xlabel('n');
```

---

### 4. The Discrete-Time Fourier Transform — DTFT (Mitra §3.2, Eq. 3.10)

$$X(e^{j\omega}) = \sum_{n=-\infty}^{\infty} x[n]\,e^{-j\omega n}$$

$X(e^{j\omega})$ is the frequency-domain "fingerprint" of $x[n]$: it tells you how much of each normalized frequency $\omega \in (-\pi,\pi]$ is present. It's periodic in $\omega$ with period $2\pi$ — a direct consequence of $n$ being an integer.

```matlab
%% 4. DTFT (evaluated numerically over a fine frequency grid)
alpha = 0.5;
n = 0:50;
x = alpha.^n;                       % causal exponential, matches Mitra Eq. (3.12)

omega = linspace(-pi, pi, 1024);
X = zeros(size(omega));
for k = 1:length(omega)
    X(k) = sum(x .* exp(-1j*omega(k)*n));   % direct evaluation of Eq. (3.10)
end
% Closed form for this case (Mitra Eq. 3.13): X = 1./(1 - alpha*exp(-j*omega))

figure;
subplot(2,1,1); plot(omega, abs(X)); title('|X(e^{j\omega})|'); xlabel('\omega (rad)');
subplot(2,1,2); plot(omega, angle(X)); title('\angle X(e^{j\omega})'); xlabel('\omega (rad)');

% If you have the Signal Processing Toolbox, freqz does this for you directly:
% [H, w] = freqz(1, [1 -alpha], 1024, 'whole'); plot(w, abs(H));
```

---

### 5. The z-transform (generalizes the DTFT)

The DTFT only converges for signals with bounded energy/amplitude. The **z-transform** generalizes $e^{j\omega}$ to a complex variable $z = re^{j\omega}$, extending the analysis to a region of convergence (ROC):
$$X(z) = \sum_{n=-\infty}^{\infty} x[n]\,z^{-n}$$

The DTFT is just $X(z)$ evaluated on the unit circle, $z = e^{j\omega}$ — provided the unit circle lies inside the ROC. This is the tool you'll use constantly this semester for filter structures, stability analysis, and filter design (poles inside the unit circle $\Rightarrow$ stable & causal).

```matlab
%% 5. z-transform via pole-zero analysis
% For a rational system H(z) = B(z)/A(z), MATLAB works directly with
% numerator/denominator coefficient vectors.
b = [1];             % numerator coefficients (feedforward)
a = [1 -0.8];         % denominator coefficients (feedback) -> pole at z = 0.8

figure; zplane(b, a); title('Pole-Zero plot of H(z) = 1 / (1 - 0.8 z^{-1})');
% requires Signal Processing Toolbox; pole at 0.8 is inside the unit circle -> stable
```

---

### 6. The Sampling Theorem — and where the course actually starts (Mitra §3.8–3.9)

**Baseband sampling theorem**, Mitra Eq. (3.71)–(3.72): a signal $g_a(t)$ band-limited to $|\Omega| \le \Omega_m$ is exactly recoverable from samples $g_a(nT)$ if
$$\Omega_T \geq 2\Omega_m, \qquad \Omega_T = \frac{2\pi}{T}$$
$2\Omega_m$ is the **Nyquist rate**. Sample below it and you get **aliasing** — high frequencies fold back and masquerade as lower ones.

```matlab
%% 6a. Aliasing demo
fs_good = 1000;   fs_bad = 60;     % Hz
f0 = 50;                            % Hz, the true tone
t_good = 0:1/fs_good:0.1;
t_bad  = 0:1/fs_bad:0.1;

figure;
plot(t_good, cos(2*pi*f0*t_good), 'b-'); hold on;
stem(t_bad, cos(2*pi*f0*t_bad), 'r', 'filled');
legend('true signal (well-sampled)', ['samples @ ' num2str(fs_bad) ' Hz (< Nyquist)']);
title('Aliasing: undersampling a 50 Hz tone'); xlabel('t (s)');
```

**This is exactly where EE 545's syllabus picks up.** The first learning objective is *bandpass and non-ideal sampling* — Mitra §3.9 extends the theorem to signals whose energy sits in a band $\Omega_L \le |\Omega| \le \Omega_H$ rather than at baseband. The punchline: for a bandpass signal of bandwidth $B=\Omega_H-\Omega_L$, you often don't need $\Omega_T \geq 2\Omega_H$ — you can get away with sampling rates as low as $2B$ if $\Omega_H$ is an integer multiple of $B$ (Mitra Eq. 3.85):
$$\Omega_T = 2B = \frac{2\Omega_H}{M}, \qquad \Omega_H = M \cdot B$$

That's the kind of "non-ideal/advanced sampling" result you should expect Chuck to build toward quickly once the review is done — it's on the syllabus by name.

```matlab
%% 6b. Bandpass signal spectrum intuition (conceptual, not literal simulation)
% A bandpass signal occupies [-OmegaH,-OmegaL] U [OmegaL,OmegaH], not [-Om,Om].
% Naive Nyquist (2*OmegaH) is wasteful; §3.9's bandpass sampling exploits the gap.
OmegaL = 2*pi*40; OmegaH = 2*pi*60;   % rad/s, a 20 Hz-wide band centered at 50 Hz
B = OmegaH - OmegaL;
fprintf('Naive Nyquist rate: %.1f Hz\n', 2*OmegaH/(2*pi));
fprintf('Bandpass-sampling floor (~2B): %.1f Hz\n', 2*B/(2*pi));
```

---

### 7. The rest of the semester, in one line each

| Topic (syllabus objective) | Mitra chapter (approx.) | One-line preview |
|---|---|---|
| Frequency-domain representations | Ch. 3 | DTFT/DFT properties, spectral analysis |
| Filter structures for implementation | Ch. 6 | Direct-form, cascade, lattice realizations |
| Digital filter design | Ch. 7 | FIR/IIR design methods (windowing, Parks-McClellan, bilinear transform) |
| Finite word-length effects | Ch. 9 | Quantization noise, coefficient sensitivity, overflow |
| Multirate systems | Ch. 10 | Decimation, interpolation, filter banks |
| 2-D / higher-dimensional processing | — | Extending 1-D theory to images |
| Adaptive filtering (time permitting) | — | LMS-family algorithms |
| Statistical signal processing (time permitting) | — | Spectral estimation, random signals |

---

### Before class: quick self-check

- Can you write $y[n]$ as a convolution sum and evaluate it by hand for two short sequences?
- Can you state the sampling theorem and explain *why* undersampling causes aliasing, not just recite the inequality?
- Do you know why the ROC matters for the z-transform (i.e., why $X(z)$ alone doesn't uniquely determine $x[n]$)?
- Open MATLAB now and run Sections 1–6 above top to bottom — if `zplane` or `freqz` errors out, you're missing the Signal Processing Toolbox; check licensing before the semester gets busy.

A companion script, `dsp_class1_companion.m`, has all the code blocks above in one runnable file with `%%` cell breaks matching these sections.
