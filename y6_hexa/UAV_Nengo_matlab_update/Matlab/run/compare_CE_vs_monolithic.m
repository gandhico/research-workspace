function compare_CE_vs_monolithic()
%COMPARE_CE_VS_MONOLITHIC Verify channel-explicit twins match the originals.
% Builds both model sets, simulates each pair, and reports the maximum absolute
% difference of every logged signal. Differences should be 0 (or float round-off
% ~1e-12) because the per-channel control math is copied verbatim.

rootDir = fileparts(fileparts(mfilename('fullpath')));
addpath(fullfile(rootDir,'params'), fullfile(rootDir,'build'), fullfile(rootDir,'run'));
run(fullfile(rootDir,'params','victor_pid_params.m'));
modelDir = fullfile(rootDir,'models');

% Make sure both versions exist (non-destructive: different file names).
build_victor_pid_R2025a;                  % originals  *.slx
build_victor_pid_R2025a_channel_explicit; % twins      *_CE.slx

bases = ["Modelo_1gdl_PID_R2025a";
         "Quadri_Sub_Por_Partes_PID_R2025a";
         "Quadri_Victor_combination_PID_R2025a";
         "Quadrotor_model_2020_PID_R2025a"];
vars = {"pid_reference","pid_state","pid_command","pid_error"};

worst = 0;
for i = 1:numel(bases)
    base = bases(i);
    ce = base + "_CE";
    outA = sim_model(modelDir, base);
    outB = sim_model(modelDir, ce);
    fprintf('\n=== %s  vs  %s ===\n', base, ce);
    for v = 1:numel(vars)
        A = signal_matrix(outA.get(char(vars{v})));
        B = signal_matrix(outB.get(char(vars{v})));
        if ~isequal(size(A), size(B))
            fprintf('  %-14s SIZE MISMATCH %s vs %s\n', vars{v}, mat2str(size(A)), mat2str(size(B)));
            worst = inf;
            continue;
        end
        d = max(abs(A(:) - B(:)));
        worst = max(worst, d);
        fprintf('  %-14s max|diff| = %.3e\n', vars{v}, d);
    end
end

fprintf('\nWorst-case difference across all signals: %.3e\n', worst);
if worst < 1e-9
    fprintf('PASS: channel-explicit twins are numerically equivalent.\n');
else
    fprintf('CHECK: differences exceed 1e-9 - inspect the channels above.\n');
end
end

function out = sim_model(modelDir, name)
mdl = fullfile(modelDir, name + ".slx");
load_system(mdl);
out = sim(char(name), 'ReturnWorkspaceOutputs', 'on');
close_system(char(name), 0);
end

function V = signal_matrix(logStruct)
t = logStruct.time(:);
V = squeeze(logStruct.signals.values);
if isvector(V)
    V = V(:);
elseif size(V,2) == numel(t) && size(V,1) ~= numel(t)
    V = V.';
end
end
