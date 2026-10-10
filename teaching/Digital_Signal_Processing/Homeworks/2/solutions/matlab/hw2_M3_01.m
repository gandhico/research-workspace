%HW2_M3_01  MATLAB Exercise M3.1  (Mitra, 4th ed., Chapter 3)
%   Using Program 3_1, determine and plot the real and imaginary parts and
%   the magnitude and phase spectra of
%
%        G(e^jw) = ---------------------------------------------- ,  0 < r < 1
%                   1 - 2r cos(theta) e^-jw + r^2 e^-j2w
%
%   for various values of r and theta.
%
%   Rational form of Eq. (3.37):   num = 1
%                                  den = [1, -2*r*cos(theta), r^2]
%   Poles:  z = r*exp(+/-j*theta)  -- a complex-conjugate pair at radius r
%           and angle +/-theta.  Both lie inside the unit circle for r < 1,
%           which is exactly the condition for the DTFT to exist.
%
%   Program 3_1 evaluates the transform only on 0 <= w <= pi because the
%   coefficients are real, so G(e^-jw) = G*(e^jw) (Table 3.4).
%
%   Run:  matlab -batch hw2_M3_01

clc; close all;

K = 512;                                    % frequency points on [0, pi]

%% ---- Sweep 1: theta = pi/4 fixed, r varied ----------------------------
theta0 = pi/4;
rlist  = [0.5 0.8 0.95];
clear cases1
for k = 1:numel(rlist)
    cases1(k) = struct('r', rlist(k), 'th', theta0, ...
                       'lbl', sprintf('r = %.2f', rlist(k)));  %#ok<SAGROW>
end
p3_1(cases1, K, 'M3.1  \theta = \pi/4, r varied');

%% ---- Sweep 2: r = 0.8 fixed, theta varied -----------------------------
r0     = 0.8;
thlist = [pi/6 pi/3 2*pi/3];
lbl2   = {'\theta = \pi/6','\theta = \pi/3','\theta = 2\pi/3'};
clear cases2
for k = 1:numel(thlist)
    cases2(k) = struct('r', r0, 'th', thlist(k), 'lbl', lbl2{k});  %#ok<SAGROW>
end
p3_1(cases2, K, 'M3.1  r = 0.8, \theta varied');

%% ---- Numerical observations -------------------------------------------
% The peak of |G| sits essentially at w = theta and grows like 1/(1-r).
fprintf('\n     r   theta/pi   peak|G|   w_peak/pi   1/[(1-r)|1-r e^{-j2th}|]\n');
fprintf(  '  ---------------------------------------------------------------\n');
for r = [0.5 0.8 0.95 0.99]
    for th = [pi/6 pi/4 pi/3]
        [w, G]  = dtft(1, [1, -2*r*cos(th), r^2], K);
        [pk, i] = max(abs(G));
        pred    = 1/((1-r)*abs(1 - r*exp(-1j*2*th)));   % |G| exactly at w=theta
        fprintf('%6.2f %9.4f %10.3f %11.4f %14.3f\n', r, th/pi, pk, w(i)/pi, pred);
    end
end

% Sanity check: freqz must agree with the direct DTFT sum of the impulse
% response, h[n] = r^n sin((n+1)theta)/sin(theta) (the standard resonator).
r = 0.8; th = pi/3; N = 400; n = (0:N-1).';
h = (r.^n).*sin((n+1)*th)/sin(th);
[w, G] = dtft(1, [1, -2*r*cos(th), r^2], 64);
Gsum   = (exp(-1j*w(:)*n.')*h).';                % sum_n h[n] e^{-jwn}
fprintf('\nfreqz == direct DTFT sum of h[n] : %d  (max err %.2e)\n', ...
        max(abs(G(:)-Gsum(:))) < 1e-8, max(abs(G(:)-Gsum(:))));

%% ========================================================================
function [w, G] = dtft(num, den, K)
%DTFT  Program 3_1 kernel: DTFT of a rational function in e^jw at K points.
w = 0:pi/(K-1):pi;
G = freqz(num, den, w);
end

function p3_1(cases, K, figname)
%P3_1  Program 3_1 plotting layout: real, imaginary, magnitude, phase.
figure('Name', figname, 'Position', [60 60 980 620]);
ttl = {'Real part','Imaginary part','Magnitude spectrum','Phase spectrum'};
yl  = {'Amplitude','Amplitude','Magnitude','Phase, radians'};
for c = cases
    [w, G] = dtft(1, [1, -2*c.r*cos(c.th), c.r^2], K);
    val = {real(G), imag(G), abs(G), unwrap(angle(G))};
    for p = 1:4
        subplot(2,2,p); plot(w/pi, val{p}, 'LineWidth', 1.2); hold on; grid on
        title(ttl{p}); xlabel('\omega/\pi'); ylabel(yl{p});
    end
end
for p = 1:4, subplot(2,2,p); legend({cases.lbl}, 'Location', 'best'); end
sgtitle(figname);
end
