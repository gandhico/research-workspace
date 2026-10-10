function hw1_verify_all
%HW1_VERIFY_ALL  Numerical check of every closed-form answer in Homework 1.
%
%   Mitra, "Digital Signal Processing: A Computer-Based Approach", 4th ed.,
%   Chapter 2, Problems 2.4-2.54.
%
%   Each subsection recomputes a result from first principles and compares it
%   against the value quoted in hw1_solutions.pdf.  Run with no arguments:
%
%       >> hw1_verify_all
%
%   Every line should print PASS.

clc;
fprintf('=== Homework 1 : numerical verification =====================\n\n');

% ---- Problem 2.3 sequences (used throughout) ------------------------------
x = [ 3 -4 -2  5  0  1 -3];  nx = -1;
y = [-5 -1  0  3  6 -2  8];  ny = -3;
w = [-1  3 -4  0  1 -5  6];  nw =  3;

%% -------------------------------------------------------------- 2.7
x1 = [1 0 1 0 1 0 1 0 1 0 1 0 1 0 1];
x2 = [1 1];
x3 = [1 1 0 0 0 0 0 0 1 1];
x4_printed  = [1 1 0 0 0 1 1];      % as printed  -> identity FAILS
x4_intended = [1 0 1 0 1 0 1];      % intended    -> identity HOLDS
lhs = conv(x1,x2);
check('2.7   x1*x2 = sixteen ones',           lhs, ones(1,16));
check('2.7   x3*x4 (intended) equals x1*x2',  conv(x3,x4_intended), lhs);
report('2.7   x3*x4 (as printed) DIFFERS  [book misprint]', ...
       ~isequal(conv(x3,x4_printed), lhs));

%% -------------------------------------------------------------- 2.8
check('2.8a  x1 (*) x1', conv([1 -1 1],[1 -1 1]), [1 -2 3 -2 1]);
check('2.8b  x2 (*) x2', conv([1 -1 0 1 -1],[1 -1 0 1 -1]), ...
                         [1 -2 1 2 -4 2 1 -2 1]);
check('2.8c  x3 (*) x3', conv([-1 2 0 -2 1],[-1 2 0 -2 1]), ...
                         [1 -4 4 4 -10 4 4 -4 1]);

%% -------------------------------------------------------------- 2.9
check('2.9a  u = x (*) y   [n = -4..8]', conv(x,y), ...
      [-15 17 14 -14 1 -41 49 5 -23 37 -20 14 -24]);
check('2.9b  v = x (*) w   [n =  2..14]', conv(x,w), ...
      [-3 13 -22 5 26 -40 42 -22 -25 31 -8 21 -18]);
check('2.9c  g = w (*) y   [n =  0..12]', conv(w,y), ...
      [5 -14 17 1 -2 32 -63 29 -41 -14 54 -52 48]);
report('2.9   start indices (-4, 2, 0)', ...
       isequal([nx+ny nx+nw nw+ny],[-4 2 0]));

%% -------------------------------------------------------------- 2.13
xa = [2 -3 4 1];   nxa = -1;         % -1 <= n <= 2
ha = [-3 5 -6 4];  nha = -2;         % -2 <= n <= 1
ya = conv(xa,ha);  nya = nxa + nha;  % starts at n = -3
check('2.13  y[-1] = -39', ya(-1-nya+1), -39);

%% -------------------------------------------------------------- 2.14
% Location of the largest sample of {n} (*) {n}, predicted in closed form by
%      mstar = (5-2N+sqrt(8N^2-24N+25))/2 ,  nmax = ceil(mstar)+N-3.
ok = true;
for N = 5:60
    yy = conv(0:N-1, 0:N-3);
    [~,k] = max(yy);   nmax_num = k-1;              % 0-based index
    mstar = (5-2*N+sqrt(8*N^2-24*N+25))/2;
    nmax_pred = ceil(mstar)+N-3;
    if nmax_num ~= nmax_pred && yy(nmax_pred+1) ~= max(yy)   % allow ties
        ok = false;  fprintf('   mismatch at N = %d\n', N);
    end
end
report('2.14  closed-form location of the peak (N = 5..60)', ok);

%% -------------------------------------------------------------- 2.15
check('2.15a x[n]', deconv_causal([2 5 -5 0 12 10 3],[2 -3 1 3]), [1 4 3 1]);
check('2.15b x[n]', deconv_causal([0 -15 -7 9 -4 2],[5 -1 1]),    [0 -3 -2 2]);
check('2.15c x[n]', deconv_causal([6 8 -12 -11 14 -22 -12 3 -18], ...
                                  [-3 2 2 0 3]),                  [-2 -4 0 1 -6]);

%% -------------------------------------------------------------- 2.16 / 2.17
xs = [2 -5 6 -3 4 -4 0 -7 8];  n0 = -5;  N9 = 9;
xt = @(n) xs(mod(n-n0,N9)+1);                       % 9-periodic extension
check('2.16a y[-3] after LEFT circular shift by 12',  xt(-3+12), -4);
check('2.16b z[2]  after RIGHT circular shift by 15', xt(2-15),  -5);

gs = [-3 0 4 9 2 0 -2 5];  g0 = -4;  N8 = 8;
gt = @(n) gs(mod(n-g0,N8)+1);
check('2.17a h[n] = right circular shift of g by 5', ...
      arrayfun(@(n) gt(n-5), -4:3), [9 2 0 -2 5 -3 0 4]);
check('2.17b w[n] = left  circular shift of g by 4', ...
      arrayfun(@(n) gt(n+4), -4:3), [2 0 -2 5 -3 0 4 9]);

%% -------------------------------------------------------------- 2.19
% Energy of sin(2*pi*k*n/N) over one period: N/2 unless 2k/N is an integer.
ok = true;
for N = 3:20
    for k = 0:2*N
        E  = sum(sin(2*pi*k*(0:N-1)/N).^2);
        Ep = (mod(2*k,N)~=0) * N/2;
        if abs(E-Ep) > 1e-10, ok = false; end
    end
end
report('2.19  E = N/2  (0 when 2k/N is an integer)', ok);

%% -------------------------------------------------------------- 2.20
[ev,od,nn] = evenodd(x,nx);
report('2.20  x_ev even, x_od odd, parts sum to x', ...
       isequal(ev,fliplr(ev)) && isequal(od,-fliplr(od)) && ...
       isequal(ev+od, embed(x,nx,nn(1),nn(end))));
check('2.20  x_ev[n], n = -5..5', ev, ...
      [-1.5 0.5 0 2.5 0.5 -4 0.5 2.5 0 0.5 -1.5]);
check('2.20  x_od[n], n = -5..5', od, ...
      [ 1.5 -0.5 0 -2.5 2.5 0 -2.5 2.5 0 0.5 -1.5]);
[ev,od] = evenodd(y,ny);
check('2.20  y_ev[n], n = -3..3', ev, [1.5 -1.5 3 3 3 -1.5 1.5]);
check('2.20  y_od[n], n = -3..3', od, [-6.5 0.5 -3 0 3 -0.5 6.5]);

%% -------------------------------------------------------------- 2.21
xc  = [-1+3i, 2-7i, 4-5i, 3+5i, -2-1i];        % -2 <= n <= 2
rev = conj(fliplr(xc));
check('2.21a x_cs', (xc+rev)/2, [-1.5+2i, 2.5-6i, 4+0i, 2.5+6i, -1.5-2i]);
check('2.21a x_ca', (xc-rev)/2, [ 0.5+1i, -0.5-1i, 0-5i, 0.5-1i, -0.5+1i]);
n = -20:20;
x2c = exp(1j*2*pi*n/5) + exp(1j*pi*n/3);
report('2.21b x2 is conjugate symmetric (x_ca = 0)', ...
       max(abs(x2c - conj(fliplr(x2c)))) < 1e-10);
x3c = 1j*cos(2*pi*n/7) - sin(2*pi*n/4);
report('2.21c x3 is conjugate antisymmetric (x_cs = 0)', ...
       max(abs(x3c + conj(fliplr(x3c)))) < 1e-10);

%% -------------------------------------------------------------- 2.37
check('2.37a  x~[n], N = 6', perext(x,nx,6), [-4 -2 5 0 1 0]);
check('2.37a  y~[n], N = 6', perext(y,ny,6), [ 3  6 -2 3 -1 0]);
check('2.37a  w~[n], N = 6', perext(w,nw,6), [ 0  1 -5 5  3 -4]);
check('2.37b  x~[n], N = 8', perext(x,nx,8), [-4 -2 5 0 1 -3 0 3]);
check('2.37b  y~[n], N = 8', perext(y,ny,8), [ 3  6 -2 8 0 -5 -1 0]);
check('2.37b  w~[n], N = 8', perext(w,nw,8), [-5  6  0 -1 3 -4 0 1]);

%% -------------------------------------------------------------- 2.38
n = 0:3;
check('2.38a  A = sqrt(2), w = pi/2,  phi = pi/4', ...
      sqrt(2)*sin(pi/2*n + pi/4),  [1 1 -1 -1]);
check('2.38b  A = 0.5,     w = pi,    phi = pi/2', ...
      0.5*sin(pi*n + pi/2),        [0.5 -0.5 0.5 -0.5]);
check('2.38c  A = 1,       w = 0.8pi, phi = 0', ...
      sin(0.8*pi*(0:4)),           [0 0.5878 -0.9511 0.9511 -0.5878], 1e-4);
check('2.38d  A = 2,       w = pi/2,  phi = pi/2', ...
      2*sin(pi/2*n + pi/2),        [2 0 -2 0]);

%% -------------------------------------------------------------- 2.39 / 2.40 / 2.41 / 2.42
check('2.39  fundamental periods', ...
      [fper(0.25*pi) lcmv(fper(0.6*pi)) ...
       lcmv([fper(pi/8) fper(pi/5)]) ...
       lcmv([fper(0.15*pi) fper(0.12*pi)]) ...
       lcmv([fper(0.1*pi) fper(0.8*pi) fper(1.3*pi)])], ...
      [8 10 80 200 20]);
check('2.40  fundamental periods', ...
      arrayfun(@fper, pi*[0.3 0.48 0.45 0.525 0.75 0.75]), ...
      [20 25 40 80 8 8]);
check('2.41  period of sin(0.06*pi*n) and two others', ...
      [fper(0.06*pi) fper(0.14*pi) fper(0.26*pi)], [100 100 100]);
check('2.42  fundamental periods', ...
      [fper(pi/3) fper(2*pi/5) fper(2*pi/7) fper(5*pi/7) ...
       lcmv([fper(2*pi/5) fper(3*pi/5)]) lcmv([fper(5*pi/3) fper(3*pi/5)])], ...
      [6 5 7 14 10 30]);
Pnum = @(s,N) sum(s(0:N-1).^2)/N;
check('2.42  average powers', ...
      [Pnum(@(n) 5*cos(pi*n/3),6),        Pnum(@(n) 2*cos(2*pi*n/5),5), ...
       Pnum(@(n) 2*cos(2*pi*n/7),7),      Pnum(@(n) 3*cos(5*pi*n/7),14), ...
       Pnum(@(n) 4*cos(2*pi*n/5)+3*cos(3*pi*n/5),10), ...
       Pnum(@(n) 4*cos(5*pi*n/3)+3*cos(3*pi*n/5),30)], ...
      [12.5 2 2 4.5 12.5 12.5], 1e-10);

%% -------------------------------------------------------------- 2.43 / 2.44
check('2.43b x[n] step coefficients',  stepcoef(x), [3 -7 2 7 -5 1 -4 3]);
check('2.43b y[n] step coefficients',  stepcoef(y), [-5 4 1 3 3 -8 10 -8]);
check('2.43b w[n] step coefficients',  stepcoef(w), [-1 4 -7 4 1 -6 11 -6]);
check('2.44  step coefficients',       stepcoef([2.1 -3.3 -1.7 5.2]), ...
      [2.1 -5.4 1.6 6.9 -5.2], 1e-12);

%% -------------------------------------------------------------- 2.46
al = 0.7;  n = 0:25;  L = numel(n);
c1 = conv(al.^n,      ones(1,L));
c2 = conv(n.*al.^n,   ones(1,L));
check('2.46a closed form', c1(1:L), (1-al.^(n+1))/(1-al), 1e-10);
check('2.46b closed form', c2(1:L), ...
      al*(1-(n+1).*al.^n + n.*al.^(n+1))/(1-al)^2, 1e-10);

%% -------------------------------------------------------------- 2.47
p1 = [-2 0 2];              q1 = -1;   % x1
p2 = [-1 0 3];              q2 =  0;   % x2
r1 = [1 0 0 -1.5 0 -1];     s1 = -3;   % h1
r2 = [-1 0 2 0 3];          s2 = -1;   % h2
check('2.47a y1 = x1 (*) h1  [n = -4..3]', conv(p1,r1), [-2 0 2 3 0 -1 0 -2]);
check('2.47b y2 = x2 (*) h2  [n = -1..5]', conv(p2,r2), [ 1 0 -5 0 3 0 9]);
check('2.47c y3 = x1 (*) h2  [n = -2..4]', conv(p1,r2), [ 2 0 -6 0 -2 0 6]);
check('2.47d y4 = x2 (*) h1  [n = -3..4]', conv(p2,r1), [-1 0 3 1.5 0 -3.5 0 -3]);
report('2.47  start indices (-4, -1, -2, -3)', ...
       isequal([q1+s1 q2+s2 q1+s2 q2+s1], [-4 -1 -2 -3]));

%% -------------------------------------------------------------- 2.48
ok = true;
for N = 6:14
    for M = 2:N-1
        xr = ones(1,N);          nxr = 0;      % mu[n] - mu[n-N]
        hr = ones(1,M);          nhr = 0;      % mu[n] - mu[n-M]
        gr = -ones(1,N-M);       ngr = M;      % mu[n-N] - mu[n-M]
        wr = ones(1,N+M);        nwr = -M;     % mu[n+M] - mu[n-N]
        ok = ok && peakis(conv(xr,xr), nxr+nxr,  N,        N-1);
        ok = ok && peakis(conv(hr,hr), nhr+nhr,  M,        M-1);
        ok = ok && peakis(conv(gr,gr), ngr+ngr,  N-M,      M+N-1);
        ok = ok && peakis(conv(wr,wr), nwr+nwr,  N+M,      N-M-1);
        ok = ok && plateauis(conv(xr,hr), nxr+nhr, M,       M-1,     N-1);
        ok = ok && plateauis(conv(xr,gr), nxr+ngr, -(N-M),  N-1,     N+M-1);
        ok = ok && plateauis(conv(xr,wr), nxr+nwr, N,       N-M-1,   N-1);
    end
end
report('2.48  peak values and locations (all N,M with 6<=N<=14)', ok);

%% -------------------------------------------------------------- 2.51
check('2.51  period of cos(30 * pi/6 * n) is 2', fper(30*pi/6), 2);

%% -------------------------------------------------------------- 2.52
check('2.52a r_xx  [l = -6..6]', xcorrseq(x,x), ...
      [-9 15 2 -2 -21 -17 64 -17 -21 -2 2 15 -9]);
check('2.52a r_yy  [l = -6..6]', xcorrseq(y,y), ...
      [-40 2 -28 3 39 -5 139 -5 39 3 -28 2 -40]);
check('2.52a r_ww  [l = -6..6]', xcorrseq(w,w), ...
      [-6 23 -40 23 6 -50 88 -50 6 23 -40 23 -6]);
check('2.52b r_xy  [l = -4..8]', xcorrseq(x,y), ...
      [24 -38 10 29 -34 29 -22 34 -10 -34 -1 -2 15]);
check('2.52b r_xw  [l = -10..2]', xcorrseq(x,w), ...
      [18 -39 11 36 -39 36 -30 -6 14 -9 15 -10 3]);

%% -------------------------------------------------------------- 2.53
al = 0.8;  n = 0:400;  xe = al.^n;
r  = xcorrseq(xe,xe);  lag = -(numel(n)-1):(numel(n)-1);
check('2.53a r[l] = a^|l| / (1-a^2)', r(abs(lag)<=10), ...
      al.^abs(-10:10)/(1-al^2), 1e-6);
Nb = 9;  rb = xcorrseq(ones(1,Nb),ones(1,Nb));
check('2.53b r[l] = N - |l|', rb, Nb-abs(-(Nb-1):(Nb-1)));

%% -------------------------------------------------------------- 2.54
M = 4;  Np = 2*M;  n = 0:Np-1;  xp = cos(pi*n/M);
rp = arrayfun(@(l) sum(xp.*circshift(xp,[0 l]))/Np, 0:Np-1);
check('2.54a r~[l] = 0.5*cos(pi*l/M)', rp, 0.5*cos(pi*(0:Np-1)/M), 1e-12);
xp = mod(0:5,6);
rp = arrayfun(@(l) sum(xp.*circshift(xp,[0 l]))/6, 0:5);
check('2.54b r~[l] = [55 40 31 28 31 40]/6', rp, [55 40 31 28 31 40]/6, 1e-12);
xp = (-1).^(0:1);
rp = arrayfun(@(l) sum(xp.*circshift(xp,[0 l]))/2, 0:1);
check('2.54c r~[l] = (-1)^l', rp, [1 -1]);

fprintf('\n=== done ====================================================\n');
end

% ======================================================================
%                             helpers
% ======================================================================
function check(name, got, want, tol)
if nargin < 4, tol = 1e-12; end
ok = isequal(size(got(:)),size(want(:))) && max(abs(got(:)-want(:))) <= tol;
report(name, ok);
if ~ok
    fprintf('        got  : %s\n', mat2str(round(got,4)));
    fprintf('        want : %s\n', mat2str(round(want,4)));
end
end

function report(name, ok)
if ok, fprintf('  PASS  %s\n', name);
else,  fprintf('  FAIL  %s\n', name);
end
end

function xv = deconv_causal(yv, hv)
%DECONV_CAUSAL  Solve h (*) x = y for causal x by forward substitution.
L  = numel(yv) - numel(hv) + 1;
xv = zeros(1,L);
for n = 1:L
    acc = yv(n);
    for k = 2:min(n,numel(hv))
        acc = acc - hv(k)*xv(n-k+1);
    end
    xv(n) = acc/hv(1);
end
end

function v = embed(s, n0, lo, hi)
v = zeros(1, hi-lo+1);
v(n0-lo+1 : n0-lo+numel(s)) = s;
end

function [ev, od, nn] = evenodd(s, n0)
L  = max(abs(n0), abs(n0+numel(s)-1));
nn = -L:L;
f  = embed(s, n0, -L, L);
ev = (f + fliplr(f))/2;
od = (f - fliplr(f))/2;
end

function p = perext(s, n0, N)
%PEREXT  One period (n = 0..N-1) of the N-periodic extension of s.
p = zeros(1,N);
for i = 1:numel(s)
    p(mod(n0+i-1, N)+1) = p(mod(n0+i-1, N)+1) + s(i);
end
end

function N = fper(w)
%FPER  Fundamental period of exp(j*w*n): smallest N with w*N = 2*pi*r.
[num, den] = rat(w/(2*pi), 1e-12);      % w/2pi = num/den in lowest terms
if num == 0, N = 1; else, N = den; end
end

function L = lcmv(v)
L = v(1);
for k = 2:numel(v), L = lcm(L, v(k)); end
end

function c = stepcoef(s)
%STEPCOEF  First differences: the coefficients of the delayed unit steps.
c = diff([0 s 0]);
end

function [r, lag] = xcorrseq(a, b)
%XCORRSEQ  r_ab[l] = sum_n a[n] b[n-l]  (linear cross-correlation).
r   = conv(a, fliplr(b));
lag = -(numel(b)-1) : (numel(a)-1);
end

function ok = peakis(c, n0, val, loc)
[m,k] = max(c);
ok = (abs(m-val) < 1e-9) && ((k-1+n0) == loc);
end

function ok = plateauis(c, n0, val, lo, hi)
idx = (lo:hi) - n0 + 1;
ok  = all(abs(c(idx) - val) < 1e-9) && (abs(max(abs(c)) - abs(val)) < 1e-9);
end
