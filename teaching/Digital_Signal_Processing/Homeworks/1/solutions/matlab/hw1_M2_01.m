%HW1_M2_01  Exercise M2.1
%   Conjugate-symmetric and conjugate-antisymmetric parts of a finite-length
%   complex sequence, and verification of the text's Example 2.11.
%
%   Example 2.11 (the "Generation of symmetric parts of a complex sequence"
%   example):  g[n] = {0, 1+j4, -2+j3, 4-j2, -5-j6, -j2, 3},  -3 <= n <= 3.

clc; close all;

g  = [0, 1+4i, -2+3i, 4-2i, -5-6i, -2i, 3];
n0 = -3;
n  = n0:n0+numel(g)-1;

[gcs, gca] = symparts(g);

prow('n       ', n);
prow('g[n]    ', g);
prow('g_cs[n] ', gcs);
prow('g_ca[n] ', gca);
fprintf('\n');

% --- verification against the values printed in the text -------------------
gcs_book = [1.5, 0.5+3i, -3.5+4.5i, 4, -3.5-4.5i, 0.5-3i, 1.5];
gca_book = [-1.5, 0.5+1i, 1.5-1.5i, -2i, -1.5-1.5i, -0.5+1i, 1.5];
fprintf('matches the text''s g_cs : %d\n', max(abs(gcs-gcs_book)) < 1e-12);
fprintf('matches the text''s g_ca : %d\n', max(abs(gca-gca_book)) < 1e-12);

% --- the two defining symmetries, checked numerically ---------------------
fprintf('g_cs[n] == conj(g_cs[-n]) : %d\n', ...
        max(abs(gcs - conj(fliplr(gcs)))) < 1e-12);
fprintf('g_ca[n] == -conj(g_ca[-n]): %d\n', ...
        max(abs(gca + conj(fliplr(gca)))) < 1e-12);
fprintf('g_cs + g_ca == g          : %d\n', max(abs(gcs+gca-g)) < 1e-12);

% --- plots ----------------------------------------------------------------
figure('Name','M2.1  symmetric parts','Position',[80 80 900 520]);
rows = {g,'g[n]'; gcs,'g_{cs}[n]'; gca,'g_{ca}[n]'};
for k = 1:3
    subplot(3,2,2*k-1); stem(n,real(rows{k,1}),'filled'); grid on
    ylabel(rows{k,2}); if k==1, title('Real part'); end
    subplot(3,2,2*k);   stem(n,imag(rows{k,1}),'filled','Color',[0.85 0.33 0.1]); grid on
    if k==1, title('Imaginary part'); end
end
xlabel('Time index n');

% ==========================================================================
function [xcs, xca] = symparts(x)
%SYMPARTS  Conjugate-symmetric and conjugate-antisymmetric parts.
%   The sequence is assumed to be indexed symmetrically about its own centre,
%   so that time reversal is simply FLIPLR.
xr  = conj(fliplr(x));          % x*[-n]
xcs = (x + xr)/2;
xca = (x - xr)/2;
end

function prow(label, v)
%PROW  Print one row of a (possibly complex) sequence in a fixed-width table.
fprintf('%s:', label);
for z = v
    if isreal(v) && all(v == fix(v))
        fprintf('%14d', z);
    elseif imag(z) == 0
        fprintf('%14g', real(z));
    else
        fprintf('%14s', sprintf('%g%+gi', real(z), imag(z)));
    end
end
fprintf('\n');
end
