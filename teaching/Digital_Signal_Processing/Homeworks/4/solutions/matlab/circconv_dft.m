function y = circconv_dft(g, h)
%CIRCCONV_DFT  N-point circular convolution of two length-N sequences via the DFT.
%
%   y = CIRCCONV_DFT(g,h) returns y[n] = g[n] (N) h[n], the N-point circular
%   convolution, computed with the DFT-based approach of Table 5.3:
%
%           g[n] (N) h[n]   <-->   G[k].H[k]
%
%   so that  y = IDFT{ DFT(g) .* DFT(h) }.
%
%   g and h must have the same length N.  If both inputs are real the tiny
%   imaginary residue left by round-off is discarded; complex inputs are
%   returned unchanged.
%
%   Solution to Problem M5.2, Mitra 4th ed., Chapter 5.

g = g(:).';  h = h(:).';
if length(g) ~= length(h)
    error('circconv_dft:lengthMismatch', ...
          'Sequences must have equal length (g: %d, h: %d).', length(g), length(h));
end

G = fft(g);                 % N-point DFT of g[n]
H = fft(h);                 % N-point DFT of h[n]
y = ifft(G .* H);           % N-point IDFT of the product

if isreal(g) && isreal(h)
    y = real(y);            % kill round-off imaginary part
end
end
