function hw4_figures()
%HW4_FIGURES  Generate the result figures for the MATLAB exercises of HW #4.
%
%   Writes  ../figures/m5_2.png,  ../figures/m5_6.png
%   (M5.10's figure is produced by m5_10.m itself.)
%
%       >> hw4_figures
clc;
outdir = fullfile('..','figures');
if ~exist(outdir,'dir'), mkdir(outdir); end

%% ================= M5.2 : circular convolution via the DFT =============
ga = [3 2 -2 1 0 1];          ha = [-5 -1 3 -2 4 4];
xb = [3-2j, 4-1j, -2+3j, 1j, 0];  vb = [1-3j, -2-1j, 2+2j, 3, -2+4j];
nc = 0:4;  xc = cos(pi*nc/2);     yc = 3.^nc;

ya = circconv_dft(ga,ha);   ea = max(abs(ya - circonv(ga,ha)));
yb = circconv_dft(xb,vb);   eb = max(abs(yb - circonv(xb,vb)));
ycc= circconv_dft(xc,yc);   ec = max(abs(ycc- circonv(xc,yc)));

f = figure('Name','M5.2','Position',[60 60 980 640],'Color','w');

subplot(2,2,1);
stem(0:5, ya, 'filled','LineWidth',1.2); grid on
xlabel('n'); ylabel('y[n]'); title('(a)  g[n] \otimes_6 h[n]');
xlim([-0.5 5.5]); ylim([min(ya)-6 max(ya)+6]);
text(0:5, ya, compose('%g', round(ya)), ...
     'VerticalAlignment','bottom','HorizontalAlignment','center','FontSize',8);

subplot(2,2,2);
stem(0:4, real(yb), 'filled','LineWidth',1.2); hold on
stem(0:4, imag(yb), 'filled','LineWidth',1.2); grid on
xlabel('n'); ylabel('y[n]'); title('(b)  x[n] \otimes_5 v[n]   (complex)');
legend('real','imag','Location','best'); xlim([-0.5 4.5]);

subplot(2,2,3);
stem(0:4, ycc, 'filled','LineWidth',1.2); grid on
xlabel('n'); ylabel('y[n]'); title('(c)  cos(\pi n/2) \otimes_5 3^n');
xlim([-0.5 4.5]); ylim([min(ycc)-25 max(ycc)+30]);
text(0:4, ycc, compose('%g', round(ycc)), ...
     'VerticalAlignment','bottom','HorizontalAlignment','center','FontSize',8);

subplot(2,2,4);
b = bar([ea eb ec] + eps, 'FaceColor',[0.30 0.55 0.80]); %#ok<NASGU>
set(gca,'YScale','log','XTickLabel',{'(a)','(b)','(c)'}); grid on
ylabel('max |y_{DFT} - y_{circonv}|');
title('DFT result vs. direct circular convolution');
ylim([1e-18 1e-10]);

sgtitle('M5.2   Circular convolution via the DFT:  y = IDFT\{G[k]H[k]\}');
exportgraphics(f, fullfile(outdir,'m5_2.png'), 'Resolution', 150);
fprintf('wrote %s\n', fullfile(outdir,'m5_2.png'));

%% ================= M5.6 : two real DFTs from one complex DFT ===========
pairs = { [-3 2 4 -6 1 2], [2 -1 3 -4 5 6], '(a)'; ...
          [ 5 -4 -2 6 1 3], [4 -5 5  1 -2 3], '(b)' };

f = figure('Name','M5.6','Position',[60 60 980 640],'Color','w');
for r = 1:2
    xr = pairs{r,1};  hr = pairs{r,2};  tag = pairs{r,3};
    [X,H,Xc] = dft2real(xr,hr);
    N = numel(xr);  k = 0:N-1;

    subplot(2,2,2*r-1);
    stem(k, real(Xc),'filled','LineWidth',1.2); hold on
    stem(k, imag(Xc),'filled','LineWidth',1.2); grid on
    xlabel('k'); ylabel('X_c[k]');
    title(sprintf('%s  packed  x[n] + j h[n]:  ONE %d-point DFT', tag, N));
    legend('real','imag','Location','best'); xlim([-0.5 N-0.5]);

    subplot(2,2,2*r);
    stem(k, abs(X),'filled','LineWidth',1.2); hold on
    stem(k, abs(H),'filled','LineWidth',1.2); grid on
    xlabel('k'); ylabel('magnitude');
    title(sprintf('%s  recovered  |X[k]|  and  |H[k]|', tag));
    legend('|X[k]|','|H[k]|','Location','best'); xlim([-0.5 N-0.5]);

    fprintf('%s  max err vs fft: X %.2e, H %.2e\n', tag, ...
            max(abs(X-fft(xr))), max(abs(H-fft(hr))));
end
sgtitle('M5.6   G[k] = (X[k] + X^*[\langle -k\rangle_N])/2,   H[k] = (X[k] - X^*[\langle -k\rangle_N])/2j');
exportgraphics(f, fullfile(outdir,'m5_6.png'), 'Resolution', 150);
fprintf('wrote %s\n', fullfile(outdir,'m5_6.png'));
end
