function build_victor_pid_R2025a()
%BUILD_VICTOR_PID_R2025A Build R2025a-native PID conversions of Victor baseline models.
% The original PD/open-loop models are not modified.
rootDir = fileparts(fileparts(mfilename('fullpath')));   % .../Matlab
modelDir = fullfile(rootDir, "models");
codeDir = fullfile(rootDir, "build", "matlab_function_code");
paramFile = fullfile(rootDir, "params", "victor_pid_params.m");
if ~exist(modelDir, 'dir'), mkdir(modelDir); end
evalin('base', "run('" + strrep(paramFile,"'","''") + "')");
bdclose('all');

build_discrete_closed_loop("Modelo_1gdl_PID_R2025a", modelDir, codeDir, paramFile, ...
    "ref_1gdl_pid.m", "pid_1gdl_controller.m", "plant_1gdl_rk4.m", ...
    "pid1_x0", "pid1_t_stop", "1-DOF Hover PID Controller", "1-DOF Vertical Hover Plant RK4");

build_discrete_closed_loop("Quadri_Sub_Por_Partes_PID_R2025a", modelDir, codeDir, paramFile, ...
    "ref_quad_local_pid.m", "pid_quad_controller.m", "plant_quad_victor_rk4.m", ...
    "quad_x0", "quad_t_stop", "Separated Cascaded PID Controller", "Victor Quadrotor RK4 Plant");

build_discrete_closed_loop("Quadri_Victor_combination_PID_R2025a", modelDir, codeDir, paramFile, ...
    "ref_quad_local_pid.m", "pid_quad_controller.m", "plant_quad_victor_rk4.m", ...
    "quad_x0", "quad_t_stop", "Combined Cascaded PID Controller", "Victor Quadrotor RK4 Plant");

build_discrete_closed_loop("Quadrotor_model_2020_PID_R2025a", modelDir, codeDir, paramFile, ...
    "ref_quadrotor_2020_pid.m", "pid_quadrotor_2020_controller.m", "plant_quadrotor_2020_rk4.m", ...
    "q2020_x0", "q2020_t_stop", "2020 Cascaded PID Controller", "Quadrotor 2020 RK4 Plant");

disp("PID R2025a models written to:");
disp(modelDir);
end

function build_discrete_closed_loop(model, modelDir, codeDir, paramFile, refScript, ctrlScript, plantScript, x0Var, stopVar, ctrlName, plantName)
if bdIsLoaded(model), close_system(model, 0); end
new_system(model);
load_system(model);
delete_if_present(model + "/Powered by QUARC");
delete_if_present(model + "/Quanser");
% Portable callback: params/ is resolved relative to the saved model file (models/..)
initCmd = "run(fullfile(fileparts(fileparts(get_param(bdroot,'FileName'))),'params','victor_pid_params.m'))";
set_param(model, 'InitFcn', initCmd);
set_param(model, 'SolverType', 'Fixed-step');
set_param(model, 'Solver', 'FixedStepDiscrete');
set_param(model, 'FixedStep', 'pid_dt');
set_param(model, 'StopTime', stopVar);

add_block('simulink/Sources/Clock', model + "/Clock", 'Position', [45 60 75 90]);
if contains(model, "1gdl")
    paramVar = "pid1_param_vec";
    paramSize = "[14 1]";
    refName = "Altitude Reference Generator";
    stateName = "Altitude State Memory";
    intName = "Altitude PID Integral Memory";
    stateScopeName = "Altitude Scope";
    commandScopeName = "Thrust Scope";
elseif contains(model, "2020")
    paramVar = "q2020_param_vec";
    paramSize = "[32 1]";
    refName = "2020 Reference Schedule";
    stateName = "State Memory";
    intName = "PID Integral Memory";
    stateScopeName = "State Scope";
    commandScopeName = "Command Scope";
else
    paramVar = "quad_param_vec";
    paramSize = "[36 1]";
    refName = "Sigmoid Reference Generator";
    stateName = "State Memory";
    intName = "PID Integral Memory";
    stateScopeName = "State Scope";
    commandScopeName = "Command Scope";
end
add_block('simulink/Sources/Constant', model + "/Parameter Vector", 'Position', [45 175 145 225]);
set_param(model + "/Parameter Vector", 'Value', paramVar);
add_mfunction(model + "/" + refName, fullfile(codeDir, refScript), [130 35 270 115]);
add_block('simulink/Discrete/Unit Delay', model + "/" + stateName, 'Position', [365 155 435 215]);
set_param(model + "/" + stateName, 'InitialCondition', x0Var, 'SampleTime', 'pid_dt');
if contains(model, "1gdl")
    int0Var = "pid1_int0";
elseif contains(model, "2020")
    int0Var = "q2020_int0";
else
    int0Var = "quad_int0";
end
add_block('simulink/Discrete/Unit Delay', model + "/" + intName, 'Position', [365 285 435 345]);
set_param(model + "/" + intName, 'InitialCondition', int0Var, 'SampleTime', 'pid_dt');
add_mfunction(model + "/" + ctrlName, fullfile(codeDir, ctrlScript), [340 35 545 120]);
add_mfunction(model + "/" + plantName, fullfile(codeDir, plantScript), [625 85 820 175]);

if contains(model, "1gdl")
    set_mf_size(model + "/" + refName, "t", "[1 1]");
    set_mf_size(model + "/" + refName, "p", paramSize);
    set_mf_size(model + "/" + refName, "ref", "[2 1]");
    set_mf_size(model + "/" + ctrlName, "t", "[1 1]");
    set_mf_size(model + "/" + ctrlName, "ref", "[2 1]");
    set_mf_size(model + "/" + ctrlName, "state", "[2 1]");
    set_mf_size(model + "/" + ctrlName, "int_state", "[1 1]");
    set_mf_size(model + "/" + ctrlName, "p", paramSize);
    set_mf_size(model + "/" + ctrlName, "ctrl", "[6 1]");
    set_mf_size(model + "/" + ctrlName, "err", "[3 1]");
    set_mf_size(model + "/" + ctrlName, "int_next", "[1 1]");
    set_mf_size(model + "/" + plantName, "state", "[2 1]");
    set_mf_size(model + "/" + plantName, "ctrl", "[6 1]");
    set_mf_size(model + "/" + plantName, "p", paramSize);
    set_mf_size(model + "/" + plantName, "state_next", "[2 1]");
else
    set_mf_size(model + "/" + refName, "t", "[1 1]");
    set_mf_size(model + "/" + refName, "p", paramSize);
    set_mf_size(model + "/" + refName, "ref", "[7 1]");
    set_mf_size(model + "/" + ctrlName, "t", "[1 1]");
    set_mf_size(model + "/" + ctrlName, "ref", "[7 1]");
    set_mf_size(model + "/" + ctrlName, "state", "[12 1]");
    set_mf_size(model + "/" + ctrlName, "int_state", "[6 1]");
    set_mf_size(model + "/" + ctrlName, "p", paramSize);
    set_mf_size(model + "/" + ctrlName, "cmd", "[9 1]");
    set_mf_size(model + "/" + ctrlName, "err", "[12 1]");
    set_mf_size(model + "/" + ctrlName, "int_next", "[6 1]");
    set_mf_size(model + "/" + plantName, "state", "[12 1]");
    set_mf_size(model + "/" + plantName, "cmd", "[9 1]");
    set_mf_size(model + "/" + plantName, "p", paramSize);
    set_mf_size(model + "/" + plantName, "state_next", "[12 1]");
end

add_toworkspace(model + "/log_reference", "pid_reference", [890 15 1010 45]);
add_toworkspace(model + "/log_state", "pid_state", [890 65 1010 95]);
add_toworkspace(model + "/log_command", "pid_command", [890 115 1010 145]);
add_toworkspace(model + "/log_error", "pid_error", [890 165 1010 195]);
add_block('simulink/Sinks/Scope', model + "/" + stateScopeName, 'Position', [1040 60 1090 100]);
add_block('simulink/Sinks/Scope', model + "/" + commandScopeName, 'Position', [1040 115 1090 155]);

add_line(model, "Clock/1", refName + "/1", 'autorouting', 'on');
add_line(model, "Parameter Vector/1", refName + "/2", 'autorouting', 'on');
add_line(model, "Clock/1", ctrlName + "/1", 'autorouting', 'on');
add_line(model, refName + "/1", ctrlName + "/2", 'autorouting', 'on');
add_line(model, stateName + "/1", ctrlName + "/3", 'autorouting', 'on');
add_line(model, intName + "/1", ctrlName + "/4", 'autorouting', 'on');
add_line(model, "Parameter Vector/1", ctrlName + "/5", 'autorouting', 'on');
add_line(model, stateName + "/1", plantName + "/1", 'autorouting', 'on');
add_line(model, ctrlName + "/1", plantName + "/2", 'autorouting', 'on');
add_line(model, "Parameter Vector/1", plantName + "/3", 'autorouting', 'on');
add_line(model, ctrlName + "/3", intName + "/1", 'autorouting', 'on');
add_line(model, plantName + "/1", stateName + "/1", 'autorouting', 'on');
add_line(model, refName + "/1", "log_reference/1", 'autorouting', 'on');
add_line(model, stateName + "/1", "log_state/1", 'autorouting', 'on');
add_line(model, ctrlName + "/1", "log_command/1", 'autorouting', 'on');
add_line(model, ctrlName + "/2", "log_error/1", 'autorouting', 'on');
add_line(model, stateName + "/1", stateScopeName + "/1", 'autorouting', 'on');
add_line(model, ctrlName + "/1", commandScopeName + "/1", 'autorouting', 'on');

Simulink.BlockDiagram.arrangeSystem(model);
save_system(model, fullfile(modelDir, model + ".slx"), 'OverwriteIfChangedOnDisk', true);
close_system(model, 0);
end

function add_mfunction(blockPath, scriptFile, pos)
add_block('simulink/User-Defined Functions/MATLAB Function', blockPath, 'Position', pos);
rt = sfroot;
chart = rt.find('-isa', 'Stateflow.EMChart', 'Path', char(blockPath));
if isempty(chart)
    error('Could not find MATLAB Function chart for %s', blockPath);
end
chart.Script = fileread(scriptFile);
end

function set_mf_size(blockPath, dataName, dataSize)
rt = sfroot;
chart = rt.find('-isa', 'Stateflow.EMChart', 'Path', char(blockPath));
if isempty(chart)
    error('Could not find MATLAB Function chart for %s', blockPath);
end
data = chart.find('-isa', 'Stateflow.Data', 'Name', char(dataName));
if isempty(data)
    warning('Could not find data %s in %s', dataName, blockPath);
else
    data.Props.Array.Size = char(dataSize);
end
end

function add_toworkspace(blockPath, varName, pos)
add_block('simulink/Sinks/To Workspace', blockPath, 'Position', pos);
set_param(blockPath, 'VariableName', varName, 'SaveFormat', 'StructureWithTime');
end

function delete_if_present(blockPath)
try
    if getSimulinkBlockHandle(blockPath) ~= -1
        delete_block(blockPath);
    end
catch
end
end
