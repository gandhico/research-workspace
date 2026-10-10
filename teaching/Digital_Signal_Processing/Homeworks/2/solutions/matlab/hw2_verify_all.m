function hw2_verify_all()
%HW2_VERIFY_ALL  Numerical check of the hand-derived answers in Homework 2.
%
%   Mitra 4th ed.: Problems 3.16(a,b), 3.25, 3.60, 3.66, 4.9, 4.15,
%   4.23(a) and 4.39.  MATLAB twin of julia/hw2_verify_all.jl.
%
%       >> hw2_verify_all
clc;
pass = 0; fail = 0;
rng(1);

fprintf('=== Homework 2 : numerical verification =====================\n\n');

%% ------------------------------------------------------------ 3.16(a,b)
% (a) x1[n] = a^n mu[n-1]   ->  X1 = a e^-jw / (1 - a e^-jw)
% (b) x2[n] = n a^n mu[n]   ->  X2 = a e^-jw / (1 - a e^-jw)^2
a = 0.6; N = 4000; ok_a = true; ok_b = true;
for w = linspace(0, 2*pi, 37)
    e     = exp(-1j*w);
    X1num = sum(a.^(1:N) .* e.^(1:N));
    X1cf  = a*e/(1 - a*e);
    X2num = sum((0:N) .* a.^(0:N) .* e.^(0:N));
    X2cf  = a*e/(1 - a*e)^2;
    if abs(X1num - X1cf) > 1e-9, ok_a = false; end
    if abs(X2num - X2cf) > 1e-9, ok_b = false; end
end
check('3.16a X1(e^jw) = a e^-jw / (1 - a e^-jw)',   ok_a);
check('3.16b X2(e^jw) = a e^-jw / (1 - a e^-jw)^2', ok_b);
w0 = 0.7; e0 = exp(-1j*w0);
check('3.16a  1/(1 - a e^-jw) is NOT the answer  [flagged slip]', ...
      abs(sum(a.^(1:N) .* e0.^(1:N)) - 1/(1 - a*e0)) > 1e-3);

%% ------------------------------------------------------------ 3.25
% Y(e^jw) = 0.5{ X(e^{jw/2}) + X(-e^{jw/2}) }  ->  y[n] = x[2n]
n0 = -6; xs = randn(1,25); ok = true;
for w = linspace(-pi, pi, 41)
    Y   = 0.5*(dtft(xs,n0,w/2) + dtft(xs,n0,w/2+pi));   % -e^{jw/2}=e^{j(w/2+pi)}
    idx = find(mod(n0 + (1:numel(xs)) - 1, 2) == 0);    % even time indices
    yv  = xs(idx);  ny0 = (n0 + idx(1) - 1)/2;
    if abs(Y - dtft(yv,ny0,w)) > 1e-9, ok = false; end
end
check('3.25  y[n] = x[2n]', ok);

%% ------------------------------------------------------------ 3.60
checkeq('3.60  x1 (*) x2  [n = -1..5]', ...
        conv([1 2 1], [-2 1 0 -1 2]), [-2 -3 0 0 0 3 2]);
check('3.60  start index -1 + 0 = -1', (-1+0) == -1);

%% ------------------------------------------------------------ 3.66
av = 2-1j; bv = 1; cv = -1+1j; ok = true;
tgt = {3*pi/2, 3-1j; 3*pi, 0; 6*pi, 2};
for k = 1:3
    w = tgt{k,1};
    X = av + bv*exp(-1j*w) + cv*exp(-2j*w);
    if abs(X - tgt{k,2}) > 1e-9, ok = false; end
end
check('3.66  a = 2-j, b = 1, c = -1+j', ok);

%% ------------------------------------------------------------ 4.9
% y[n] = (x[n])^2 : nonlinear, time-invariant, causal (memoryless)
x1 = randn(1,40); x2 = randn(1,40); sq = @(v) v.^2;
check('4.9   NOT homogeneous: (2x)^2 != 2 x^2', ...
      max(abs(sq(2*x1) - 2*sq(x1))) > 1e-6);
check('4.9   NOT additive: (x1+x2)^2 != x1^2 + x2^2', ...
      max(abs(sq(x1+x2) - (sq(x1)+sq(x2)))) > 1e-6);
nd = 5;  xd = [zeros(1,nd) x1(1:end-nd)];
check('4.9   time-invariant: T{x[n-n0]} = y[n-n0]', ...
      max(abs(sq(xd(nd+1:end)) - sq(x1(1:end-nd)))) < 1e-12);
check('4.9   causal / memoryless: y[n] depends only on x[n]', ...
      isequal(sq(x1), x1.^2));

%% ------------------------------------------------------------ 4.15
ok = true; mono = true;
for trial = 1:200
    h = abs(randn(1,30)) .* (0.8.^(0:29));   % nonnegative, summable
    s = cumsum(h);
    if any(diff(s) < -1e-12),      mono = false; end
    if max(s) > s(end) + 1e-12,    ok   = false; end
end
check('4.15  s[n] - s[n-1] = h[n] >= 0  (monotone)', mono);
check('4.15  s[n] <= s_inf  (no overshoot)',          ok);

%% ------------------------------------------------------------ 4.23(a)
yv = [6 -7 -13 24 12 33 -5 14];  hv = [3 4 -1 2];
xv = deconv_causal(yv, hv);
checkeq('4.23a x[n] = {2, -5, 3, 1, 7}', xv, [2 -5 3 1 7]);
checkeq('4.23a h (*) x reproduces y',    conv(hv,xv), yv);
check('4.23a length(x) = 8 - 4 + 1 = 5', numel(xv) == 5);

%% ------------------------------------------------------------ 4.39
Nf = 30;
f = zeros(1,Nf); f(2) = 1;
for n = 3:Nf, f(n) = f(n-1) + f(n-2); end          % f[0]=0, f[1]=1
phi = (1+sqrt(5))/2;  psi = (1-sqrt(5))/2;
binet = (phi.^(0:Nf-1) - psi.^(0:Nf-1))/sqrt(5);
checkeq('4.39a f[n] = (phi^n - psi^n)/sqrt(5)', f, binet, 1e-6);
check('4.39a A = 1/sqrt(5), B = -1/sqrt(5)', abs(1/sqrt(5)-0.4472135955) < 1e-9);
xi = zeros(1,Nf); xi(1) = 1;  yi = zeros(1,Nf);
for n = 1:Nf
    ym1 = 0; ym2 = 0; xm1 = 0;
    if n >= 2, ym1 = yi(n-1); xm1 = xi(n-1); end
    if n >= 3, ym2 = yi(n-2); end
    yi(n) = ym1 + ym2 + xm1;
end
checkeq('4.39b impulse response of y[n]=y[n-1]+y[n-2]+x[n-1] is f[n]', yi, f);

fprintf('\n=== done ====================================================\n');
fprintf('  %d/%d checks PASSED', pass, pass+fail);
if fail > 0, fprintf('   (%d FAILED)', fail); end
fprintf('\n');

%% ---------------- nested helpers -------------------------------------
    function check(name, ok)
        if ok, fprintf('  PASS  %s\n', name); pass = pass + 1;
        else,  fprintf('  FAIL  %s\n', name); fail = fail + 1;
        end
    end
    function checkeq(name, got, want, tol)
        if nargin < 4, tol = 1e-9; end
        ok = isequal(numel(got),numel(want)) && max(abs(got(:)-want(:))) <= tol;
        check(name, ok);
        if ~ok
            fprintf('        got  : %s\n', mat2str(round(got,5)));
            fprintf('        want : %s\n', mat2str(round(want,5)));
        end
    end
end

%% ---------------- local functions ---------------------------------------
function X = dtft(s, n0, w)
X = sum(s .* exp(-1j*w*(n0 + (0:numel(s)-1))));
end

function x = deconv_causal(y, h)
L = numel(y) - numel(h) + 1;
x = zeros(1,L);
for n = 1:L
    acc = y(n);
    for k = 2:min(n, numel(h)), acc = acc - h(k)*x(n-k+1); end
    x(n) = acc/h(1);
end
end
