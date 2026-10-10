%% hw4_verify_all.m
%  Numerical verification of every hand-derived result in HW #4
%  (Mitra 4th ed., Chapter 5: Problems 5.11, 5.13, 5.18, 5.20, 5.23, 5.58, 5.65)
function hw4_verify_all()
clc;
pass = 0; fail = 0;
tol  = 1e-9;

fprintf('===========================================================\n');
fprintf('  HW #4  --  verification of hand-derived results\n');
fprintf('===========================================================\n\n');

%% ---------------- Problem 5.11 :  F^4{x[n]} = N^2 x[n] -------------
fprintf('Problem 5.11   y[n] = F{F{F{F{x[n]}}}} = N^2 x[n]\n');
for N = [4 5 8 12]
    x  = randn(1,N) + 1j*randn(1,N);
    y  = fft(fft(fft(fft(x))));
    check(sprintf('N=%2d : F^4{x} = N^2 x', N), max(abs(y - N^2*x)) < tol*N^3);
    % intermediate identity  F^2{x}[k] = N x[<-k>_N]
    x2 = fft(fft(x));
    check(sprintf('N=%2d : F^2{x}[k] = N x[<-k>_N]', N), ...
          max(abs(x2 - N*x(mod(-(0:N-1),N)+1))) < tol*N^2);
end
fprintf('\n');

%% ---------------- Problem 5.13 : DIF butterfly ---------------------
fprintf('Problem 5.13   X[2l] = G[l],  X[2l+1] = H[l]\n');
for N = [6 8 12 16]
    x  = randn(1,N);
    M  = N/2;  n = 0:M-1;
    WN = exp(-1j*2*pi/N);
    g  = x(n+1) + x(n+M+1);
    h  = (x(n+1) - x(n+M+1)) .* WN.^n;
    G  = fft(g);  H = fft(h);
    X  = fft(x);
    check(sprintf('N=%2d : X[2l]   = G[l]',   N), max(abs(X(2*(0:M-1)+1)   - G)) < tol*N);
    check(sprintf('N=%2d : X[2l+1] = H[l]',   N), max(abs(X(2*(0:M-1)+2)   - H)) < tol*N);
end
fprintf('\n');

%% ---------------- Problem 5.18 : X[k] = Y[kM] ----------------------
fprintf('Problem 5.18   X[k] = Y[kM]  (zero-padding by factor M)\n');
for N = [5 7 8]
    for M = [2 3 4]
        x  = randn(1,N);
        xe = [x zeros(1,(M-1)*N)];     % length MN
        Y  = fft(xe);                  % MN-point DFT
        X  = fft(x);                   % N-point DFT
        check(sprintf('N=%d, M=%d : X[k] = Y[kM]', N, M), ...
              max(abs(X - Y(M*(0:N-1)+1))) < tol*N*M);
    end
end
fprintf('\n');

%% ---------------- Problem 5.20 : zero interpolation ----------------
fprintf('Problem 5.20   Y[k] = X[<k>_N]  (L-fold zero interpolation)\n');
for N = [4 5 6]
    for L = [2 3 4]
        x = randn(1,N);
        y = zeros(1, N*L);
        y(L*(0:N-1)+1) = x;            % Eq. (5.202)
        Y = fft(y);                    % NL-point DFT
        X = fft(x);                    % N-point DFT
        check(sprintf('N=%d, L=%d : Y[k] = X[<k>_N]', N, L), ...
              max(abs(Y - X(mod(0:N*L-1, N)+1))) < tol*N*L);
    end
end
% part (b) : the specific sketch
X5 = [1 1 4 3 2];  L = 4;
y  = zeros(1,20);  x5 = ifft(X5);  y(L*(0:4)+1) = x5;
Y20 = fft(y);
check('part (b) : Y[k] = four periods of {1,1,4,3,2}', ...
      max(abs(Y20 - repmat(X5,1,4))) < tol*20);
fprintf('       Y[k] = [%s]\n\n', strtrim(sprintf(' %.4g', real(Y20))));

%% ---------------- Problem 5.23 : rational DTFT ---------------------
fprintf('Problem 5.23   p[n], d[n] from P[k], D[k]\n');
P = [3.5, -0.5-9.5j, 2.5, -0.5+9.5j];
D = [17,   7.4+12j,  17.8, 7.4-12j ];
p = ifft(P);  d = ifft(D);
check('p[n] is real', max(abs(imag(p))) < tol);
check('d[n] is real', max(abs(imag(d))) < tol);
p = real(p);  d = real(d);
fprintf('       p[n] = [%s]\n', strtrim(sprintf(' %g', p)));
fprintf('       d[n] = [%s]\n', strtrim(sprintf(' %g', d)));
check('p[n] = {1.25, 5, 1.75, -4.5}', max(abs(p - [1.25 5 1.75 -4.5])) < 1e-10);
check('d[n] = {12.4, -6.2, 5, 5.8}', max(abs(d - [12.4 -6.2 5 5.8])) < 1e-10);
% the recovered X(e^jw) must reproduce P[k]/D[k] on the 4-point grid
w   = 2*pi*(0:3)/4;
num = p * exp(-1j*(0:3).'*w);
den = d * exp(-1j*(0:3).'*w);
check('numerator  matches P[k] on w = 2pi k/4', max(abs(num - P)) < 1e-9);
check('denominator matches D[k] on w = 2pi k/4', max(abs(den - D)) < 1e-9);
fprintf('       X(e^jw) = (1.25 + 5e^-jw + 1.75e^-j2w - 4.5e^-j3w)\n');
fprintf('               / (12.4 - 6.2e^-jw + 5e^-j2w + 5.8e^-j3w)\n\n');

%% ---------------- Problem 5.58 : circular cross-correlation --------
fprintf('Problem 5.58   DFT{r_xy[l]} = X[k] * conj(Y[k])\n');
for N = [4 5 8]
    x = randn(1,N);  y = randn(1,N);
    r = zeros(1,N);
    for l = 0:N-1                      % Eq. (5.203), from the definition
        r(l+1) = sum( x .* y(mod((0:N-1)-l, N)+1) );
    end
    R = fft(r);  X = fft(x);  Y = fft(y);
    check(sprintf('N=%d : R_xy[k] = X[k] conj(Y[k])', N), max(abs(R - X.*conj(Y))) < tol*N^2);
    check(sprintf('N=%d : R_xy[k] = X[k] Y[<-k>_N]',  N), ...
          max(abs(R - X.*Y(mod(-(0:N-1),N)+1))) < tol*N^2);
    % autocorrelation special case
    ra = zeros(1,N);
    for l = 0:N-1, ra(l+1) = sum( x .* x(mod((0:N-1)-l,N)+1) ); end
    check(sprintf('N=%d : R_xx[k] = |X[k]|^2', N), max(abs(fft(ra) - abs(X).^2)) < tol*N^2);
end
fprintf('\n');

%% ---------------- Problem 5.65 : circular shift --------------------
fprintf('Problem 5.65   G[k] = W12^(5k) H[k]\n');
Hh = [4.0, 17.19+1.46j, -9.0+3.46j, -9.0+5.0j, 1.0+24.25j, 6.8-5.46j, 6.0];
H  = [Hh, conj(Hh(6:-1:2))];              % fill in by conjugate symmetry
check('H[k] has length 12', numel(H) == 12);
h  = ifft(H);
check('h[n] is real', max(abs(imag(h))) < 1e-9);
h  = real(h);
fprintf('       h[n] = [%s]   (integers, as expected)\n', strtrim(sprintf(' %.3f', h)));
k  = 0:11;
G  = exp(-1j*2*pi*5*k/12) .* H;           % circular time-shift theorem
g  = real(ifft(G));
check('g[n] = h[<n-17>_12] = h[<n-5>_12]', max(abs(g - h(mod((0:11)-5,12)+1))) < 1e-9);
check('G[0] = H[0] = 4  (real)', abs(G(1) - 4) < 1e-9);
check('G[6] = -H[6] = -6 (real)', abs(G(7) + 6) < 1e-9);
check('G[k] conjugate symmetric', max(abs(G - conj(G(mod(-(0:11),12)+1)))) < 1e-9);
fprintf('\n       k |          G[k]\n      ---+---------------------\n');
for kk = 0:11
    fprintf('      %2d | %10.4f %+9.4fj\n', kk, real(G(kk+1)), imag(G(kk+1)));
end

%% ---------------- summary ------------------------------------------
fprintf('\n===========================================================\n');
fprintf('  %d/%d checks PASSED', pass, pass+fail);
if fail > 0, fprintf('   (%d FAILED)', fail); end
fprintf('\n===========================================================\n');

%% ---------------- nested helper -------------------------------------
    function check(name, cond)
        if cond
            fprintf('  PASS  %s\n', name); pass = pass + 1;
        else
            fprintf('  FAIL  %s\n', name); fail = fail + 1;
        end
    end
end
