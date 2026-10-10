function [G, H, X] = dft2real(g, h)
%DFT2REAL  N-point DFTs of two real length-N sequences from ONE N-point DFT.
%
%   [G,H] = DFT2REAL(g,h) returns the N-point DFTs of the two real sequences
%   g[n] and h[n] using the method of Section 5.9.1 (Mitra 4th ed.):
%
%       x[n] = g[n] + j h[n]                                    (5.116)
%       G[k] = ( X[k] + X*[<-k>_N] ) / 2                        (5.117)
%       H[k] = ( X[k] - X*[<-k>_N] ) / (2j)                     (5.118)
%
%   One length-N complex FFT replaces two length-N real FFTs.
%   [G,H,X] = DFT2REAL(...) also returns the intermediate DFT X[k].
%
%   Solution to Problem M5.6, Mitra 4th ed., Chapter 5.

g = g(:).';  h = h(:).';
if length(g) ~= length(h)
    error('dft2real:lengthMismatch', ...
          'Sequences must have equal length (g: %d, h: %d).', length(g), length(h));
end
if ~isreal(g) || ~isreal(h)
    error('dft2real:notReal', 'Both input sequences must be real-valued.');
end

N = length(g);
x = g + 1j*h;               % (5.116)  pack the two real sequences
X = fft(x);                 %          ONE N-point DFT

k    = 0:N-1;
Xrev = conj(X(mod(-k, N) + 1));   % X*[<-k>_N] = X*[<N-k>_N]

G = (X + Xrev) / 2;               % (5.117)  conjugate-symmetric part
H = (X - Xrev) / (2j);            % (5.118)  conjugate-antisymmetric part
end
