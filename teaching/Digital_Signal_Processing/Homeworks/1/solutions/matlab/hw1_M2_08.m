%HW1_M2_08  Exercise M2.8
%   Using the correlation program ("Program 2_5(new)"), determine the auto-
%   correlation and cross-correlation sequences of Problem 2.52, and compare
%   them with the values obtained by hand.
%
%   PROG_CORR below is a self-contained equivalent of the text's correlation
%   program: it computes  r_xy[l] = sum_n x[n]*y[n-l]  using CONV with one
%   sequence time-reversed, and returns the correct lag axis.

clc; close all;

x = [ 3 -4 -2  5  0  1 -3];  nx = -1;      % Problem 2.3
y = [-5 -1  0  3  6 -2  8];  ny = -3;
w = [-1  3 -4  0  1 -5  6];  nw =  3;

%% (a) autocorrelations
[rxx, lxx] = prog_corr(x,nx, x,nx);
[ryy, lyy] = prog_corr(y,ny, y,ny);
[rww, lww] = prog_corr(w,nw, w,nw);

%% (b) cross-correlations
[rxy, lxy] = prog_corr(x,nx, y,ny);
[rxw, lxw] = prog_corr(x,nx, w,nw);

show('r_xx', rxx, lxx, [-9 15 2 -2 -21 -17 64 -17 -21 -2 2 15 -9]);
show('r_yy', ryy, lyy, [-40 2 -28 3 39 -5 139 -5 39 3 -28 2 -40]);
show('r_ww', rww, lww, [-6 23 -40 23 6 -50 88 -50 6 23 -40 23 -6]);
show('r_xy', rxy, lxy, [24 -38 10 29 -34 29 -22 34 -10 -34 -1 -2 15]);
show('r_xw', rxw, lxw, [18 -39 11 36 -39 36 -30 -6 14 -9 15 -10 3]);

fprintf('\nProperties of the autocorrelations:\n');
fprintf('  r_xx even and peaked at l = 0 : %d,  r_xx[0] = E_x = %d\n', ...
        isequal(rxx, fliplr(rxx)) && max(rxx)==rxx(lxx==0), sum(x.^2));
fprintf('  r_yy even and peaked at l = 0 : %d,  r_yy[0] = E_y = %d\n', ...
        isequal(ryy, fliplr(ryy)) && max(ryy)==ryy(lyy==0), sum(y.^2));
fprintf('  r_ww even and peaked at l = 0 : %d,  r_ww[0] = E_w = %d\n', ...
        isequal(rww, fliplr(rww)) && max(rww)==rww(lww==0), sum(w.^2));
fprintf(['\nThe cross-correlations are NOT even -- instead ' ...
         'r_xy[l] = r_yx[-l].\n']);
[ryx, ~] = prog_corr(y,ny, x,nx);
fprintf('  r_xy[l] == r_yx[-l] : %d\n', isequal(rxy, fliplr(ryx)));

%% plots
figure('Name','M2.8  correlations','Position',[60 40 1000 760]);
sets = {rxx,lxx,'r_{xx}[\ell]'; ryy,lyy,'r_{yy}[\ell]'; rww,lww,'r_{ww}[\ell]'; ...
        rxy,lxy,'r_{xy}[\ell]'; rxw,lxw,'r_{xw}[\ell]'};
for k = 1:5
    subplot(5,1,k);
    stem(sets{k,2}, sets{k,1}, 'filled','MarkerSize',4); grid on
    ylabel(sets{k,3}); xlim([-11 9]);
end
xlabel('Lag index \ell');
sgtitle('Problem 2.52:  auto- and cross-correlation sequences');

% ==========================================================================
function [r, lag] = prog_corr(x, nx, y, ny)
%PROG_CORR  Cross-correlation of two finite-length sequences.
%   [R,LAG] = PROG_CORR(X,NX,Y,NY) returns  r[l] = sum_n x[n]*y[n-l],
%   where X starts at index NX and Y starts at index NY.
%
%   Setting Y = X gives the autocorrelation.
r   = conv(x, fliplr(y));
lag = (nx - (ny + numel(y) - 1)) : (nx + numel(x) - 1 - ny);
end

function show(name, r, lag, expected)
fprintf('%s :  l = %d..%d\n', name, lag(1), lag(end));
fprintf('        %s\n', mat2str(r));
fprintf('        matches the hand result : %d\n\n', isequal(r, expected));
end
