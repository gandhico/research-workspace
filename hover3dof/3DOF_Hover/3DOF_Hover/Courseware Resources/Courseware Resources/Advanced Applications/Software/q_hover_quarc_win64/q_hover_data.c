/*
 * q_hover_data.c
 *
 * Academic License - for use in teaching, academic research, and meeting
 * course requirements at degree granting institutions only.  Not for
 * government, commercial, or other organizational use.
 *
 * Code generation for model "q_hover".
 *
 * Model version              : 24.0
 * Simulink Coder version : 24.1 (R2024a) 19-Nov-2023
 * C source code generated on : Fri Aug 15 14:26:51 2025
 *
 * Target selection: quarc_win64.tlc
 * Note: GRT includes extra infrastructure and instrumentation for prototyping
 * Embedded hardware selection: Intel->x86-64 (Windows64)
 * Code generation objectives: Unspecified
 * Validation result: Not run
 */

#include "q_hover.h"

/* Block parameters (default storage) */
P_q_hover_T q_hover_P = {
  /* Variable: CMD_RATE_LIMIT
   * Referenced by:
   *   '<S2>/Limit Rate of Desired Angle'
   *   '<S3>/Limit Rate of Desired Angle'
   */
  1.0471975511965976,

  /* Variable: INT_JOYSTICK_SAT_LOWER
   * Referenced by:
   *   '<S3>/Des Position:  Pitch (deg)'
   *   '<S3>/Des Position:  Roll (deg)'
   *   '<S3>/Des Position:  Roll (deg)1'
   */
  -10.0,

  /* Variable: INT_JOYSTICK_SAT_UPPER
   * Referenced by:
   *   '<S3>/Des Position:  Pitch (deg)'
   *   '<S3>/Des Position:  Roll (deg)'
   *   '<S3>/Des Position:  Roll (deg)1'
   */
  10.0,

  /* Variable: JOYSTICK_X_DZ
   * Referenced by: '<S3>/Dead Zone: X (V)'
   */
  0.25,

  /* Variable: JOYSTICK_Y_DZ
   * Referenced by: '<S3>/Dead Zone: Y (V)'
   */
  0.25,

  /* Variable: K
   * Referenced by: '<S4>/Control Gain: K'
   */
  { -111.80339887498891, -111.80339887498886, 111.80339887498963,
    111.80339887498951, 132.28756555322951, -132.2875655532296,
    3.9777313617111264E-14, 1.3359172353559403E-13, -9.0050401353987134E-14,
    -6.7537801015490344E-14, 132.28756555322965, -132.28756555322931,
    -41.412755259045184, -41.41275525904517, 41.412755259045262,
    41.412755259045248, 36.226782591268922, -36.226782591268936,
    -5.7188462908587927E-15, 1.0819990308469102E-14, 4.458880494263205E-15,
    -1.1920703800480215E-15, 36.226782591268929, -36.2267825912689 },

  /* Variable: K_AMP
   * Referenced by:
   *   '<S1>/Cable Gain'
   *   '<S1>/Cable Gain Pre-Compensation'
   */
  3.0,

  /* Variable: K_EC_P
   * Referenced by: '<S1>/Encoder Resolution: Pitch'
   */
  0.00076699039394282058,

  /* Variable: K_EC_R
   * Referenced by: '<S1>/Encoder Resolution: Roll '
   */
  0.00076699039394282058,

  /* Variable: K_EC_Y
   * Referenced by: '<S1>/Encoder Resolution: Yaw'
   */
  -0.00076699039394282058,

  /* Variable: K_JOYSTICK_X
   * Referenced by: '<S3>/Calibration: X  (deg//s//V)'
   */
  -25.0,

  /* Variable: K_JOYSTICK_Y
   * Referenced by: '<S3>/Calibration: Y  (deg//s//V)'
   */
  25.0,

  /* Variable: VMAX_AMP
   * Referenced by: '<S1>/UPM Voltage Limit: 0 to VMAX_AMP'
   */
  24.0,

  /* Variable: V_bias
   * Referenced by: '<S4>/Bias Voltage'
   */
  2.0,

  /* Mask Parameter: HILWriteAnalog_channels
   * Referenced by: '<S1>/HIL Write Analog'
   */
  { 0U, 1U, 3U, 2U },

  /* Expression: [1 0 0; 0 1 0; 0 0 1; 0 0 0; 0 0 0; 0 0 0];
   * Referenced by: '<S2>/Convert to State with 6 Elements'
   */
  { 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0,
    0.0, 0.0, 0.0 },

  /* Expression: [1 0 0; 0 1 0; 0 0 1; 0 0 0; 0 0 0; 0 0 0];
   * Referenced by: '<S3>/Convert to State with 6 Elements'
   */
  { 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0,
    0.0, 0.0, 0.0 },

  /* Expression: set_other_outputs_at_terminate
   * Referenced by: '<S1>/HIL Initialize'
   */
  0.0,

  /* Expression: set_other_outputs_at_switch_out
   * Referenced by: '<S1>/HIL Initialize'
   */
  0.0,

  /* Expression: set_other_outputs_at_start
   * Referenced by: '<S1>/HIL Initialize'
   */
  0.0,

  /* Expression: set_other_outputs_at_switch_in
   * Referenced by: '<S1>/HIL Initialize'
   */
  0.0,

  /* Expression: final_analog_outputs
   * Referenced by: '<S1>/HIL Initialize'
   */
  0.0,

  /* Expression: final_pwm_outputs
   * Referenced by: '<S1>/HIL Initialize'
   */
  0.0,

  /* Expression: analog_input_maximums
   * Referenced by: '<S1>/HIL Initialize'
   */
  10.0,

  /* Expression: analog_input_minimums
   * Referenced by: '<S1>/HIL Initialize'
   */
  -10.0,

  /* Expression: analog_output_maximums
   * Referenced by: '<S1>/HIL Initialize'
   */
  10.0,

  /* Expression: analog_output_minimums
   * Referenced by: '<S1>/HIL Initialize'
   */
  -10.0,

  /* Expression: initial_analog_outputs
   * Referenced by: '<S1>/HIL Initialize'
   */
  0.0,

  /* Expression: watchdog_analog_outputs
   * Referenced by: '<S1>/HIL Initialize'
   */
  0.0,

  /* Expression: pwm_frequency
   * Referenced by: '<S1>/HIL Initialize'
   */
  24305.934065934067,

  /* Expression: pwm_leading_deadband
   * Referenced by: '<S1>/HIL Initialize'
   */
  0.0,

  /* Expression: pwm_trailing_deadband
   * Referenced by: '<S1>/HIL Initialize'
   */
  0.0,

  /* Expression: initial_pwm_outputs
   * Referenced by: '<S1>/HIL Initialize'
   */
  0.0,

  /* Expression: watchdog_pwm_outputs
   * Referenced by: '<S1>/HIL Initialize'
   */
  0.0,

  /* Computed Parameter: DerivativeFilterPitch_A
   * Referenced by: '<S1>/Derivative Filter: Pitch'
   */
  { -201.06192982974676, -15791.367041742973 },

  /* Computed Parameter: DerivativeFilterPitch_C
   * Referenced by: '<S1>/Derivative Filter: Pitch'
   */
  { 15791.367041742973, 0.0 },

  /* Computed Parameter: DerivativeFilterRoll_A
   * Referenced by: '<S1>/Derivative Filter: Roll'
   */
  { -201.06192982974676, -15791.367041742973 },

  /* Computed Parameter: DerivativeFilterRoll_C
   * Referenced by: '<S1>/Derivative Filter: Roll'
   */
  { 15791.367041742973, 0.0 },

  /* Computed Parameter: DerivativeFilterYaw_A
   * Referenced by: '<S1>/Derivative Filter: Yaw'
   */
  { -201.06192982974676, -15791.367041742973 },

  /* Computed Parameter: DerivativeFilterYaw_C
   * Referenced by: '<S1>/Derivative Filter: Yaw'
   */
  { 15791.367041742973, 0.0 },

  /* Expression: [1; 1; 1; 1]
   * Referenced by: '<S4>/Convert to  Vector'
   */
  { 1.0, 1.0, 1.0, 1.0 },

  /* Expression: 1
   * Referenced by: '<S2>/Signal Generator: Yaw'
   */
  1.0,

  /* Expression: 0.04
   * Referenced by: '<S2>/Signal Generator: Yaw'
   */
  0.04,

  /* Expression: 5
   * Referenced by: '<S2>/Amplitude: Yaw (deg)'
   */
  5.0,

  /* Expression: 0
   * Referenced by: '<S2>/Constant: Yaw (deg)'
   */
  0.0,

  /* Expression: pi/180
   * Referenced by: '<S8>/Gain1'
   */
  0.017453292519943295,

  /* Expression: 1
   * Referenced by: '<S2>/Signal Generator: Pitch'
   */
  1.0,

  /* Expression: 0.1
   * Referenced by: '<S2>/Signal Generator: Pitch'
   */
  0.1,

  /* Expression: 4
   * Referenced by: '<S2>/Amplitude: Pitch (deg)'
   */
  4.0,

  /* Expression: 0
   * Referenced by: '<S2>/Constant: Pitch (deg)'
   */
  0.0,

  /* Expression: pi/180
   * Referenced by: '<S6>/Gain1'
   */
  0.017453292519943295,

  /* Expression: 1
   * Referenced by: '<S2>/Signal Generator: Roll'
   */
  1.0,

  /* Expression: 0.08
   * Referenced by: '<S2>/Signal Generator: Roll'
   */
  0.08,

  /* Expression: 4
   * Referenced by: '<S2>/Amplitude: Roll (deg)'
   */
  4.0,

  /* Expression: 0
   * Referenced by: '<S2>/Constant: Roll (deg)'
   */
  0.0,

  /* Expression: pi/180
   * Referenced by: '<S7>/Gain1'
   */
  0.017453292519943295,

  /* Expression: 0
   * Referenced by: '<S3>/Des Position:  Roll (deg)1'
   */
  0.0,

  /* Expression: 0
   * Referenced by: '<S3>/Des Position:  Pitch (deg)'
   */
  0.0,

  /* Expression: 0
   * Referenced by: '<S3>/Des Position:  Roll (deg)'
   */
  0.0,

  /* Expression: pi/180
   * Referenced by: '<S10>/Gain1'
   */
  0.017453292519943295,

  /* Expression: 0
   * Referenced by: '<S1>/UPM Voltage Limit: 0 to VMAX_AMP'
   */
  0.0,

  /* Expression: 180/pi
   * Referenced by: '<S11>/Gain'
   */
  57.295779513082323,

  /* Expression: 180/pi
   * Referenced by: '<S12>/Gain'
   */
  57.295779513082323,

  /* Expression: 0
   * Referenced by: '<S3>/Rate Transition'
   */
  0.0,

  /* Expression: 0
   * Referenced by: '<S3>/Rate Transition1'
   */
  0.0,

  /* Expression: 0
   * Referenced by: '<S3>/Rate Transition2'
   */
  0.0,

  /* Expression: -1
   * Referenced by: '<S9>/Inverse'
   */
  -1.0,

  /* Expression: 1
   * Referenced by: '<S9>/Bias'
   */
  1.0,

  /* Expression: 2
   * Referenced by: '<S9>/Constant'
   */
  2.0,

  /* Expression: 30
   * Referenced by: '<S3>/Calibration: X  (deg//s//V)1'
   */
  30.0,

  /* Computed Parameter: HILInitialize_CKChannels
   * Referenced by: '<S1>/HIL Initialize'
   */
  { 0, 1, 2 },

  /* Computed Parameter: HILInitialize_DOWatchdog
   * Referenced by: '<S1>/HIL Initialize'
   */
  0,

  /* Computed Parameter: HILInitialize_EIInitial
   * Referenced by: '<S1>/HIL Initialize'
   */
  0,

  /* Computed Parameter: HILInitialize_POModes
   * Referenced by: '<S1>/HIL Initialize'
   */
  0,

  /* Computed Parameter: HILInitialize_POConfiguration
   * Referenced by: '<S1>/HIL Initialize'
   */
  0,

  /* Computed Parameter: HILInitialize_POAlignment
   * Referenced by: '<S1>/HIL Initialize'
   */
  0,

  /* Computed Parameter: HILInitialize_POPolarity
   * Referenced by: '<S1>/HIL Initialize'
   */
  1,

  /* Computed Parameter: HILReadEncoderTimebase_Clock
   * Referenced by: '<S1>/HIL Read Encoder Timebase'
   */
  0,

  /* Computed Parameter: HILInitialize_AIChannels
   * Referenced by: '<S1>/HIL Initialize'
   */
  { 0U, 1U, 2U, 3U, 4U, 5U, 6U, 7U },

  /* Computed Parameter: HILInitialize_AOChannels
   * Referenced by: '<S1>/HIL Initialize'
   */
  { 0U, 1U, 2U, 3U, 4U, 5U, 6U, 7U },

  /* Computed Parameter: HILInitialize_DOChannels
   * Referenced by: '<S1>/HIL Initialize'
   */
  { 0U, 1U, 2U, 3U },

  /* Computed Parameter: HILInitialize_EIChannels
   * Referenced by: '<S1>/HIL Initialize'
   */
  { 0U, 1U, 2U, 3U, 4U, 5U, 6U, 7U },

  /* Computed Parameter: HILInitialize_EIQuadrature
   * Referenced by: '<S1>/HIL Initialize'
   */
  4U,

  /* Computed Parameter: HILInitialize_POChannels
   * Referenced by: '<S1>/HIL Initialize'
   */
  { 0U, 1U, 2U, 3U, 4U, 5U, 6U, 7U },

  /* Computed Parameter: HILReadEncoderTimebase_Channels
   * Referenced by: '<S1>/HIL Read Encoder Timebase'
   */
  { 0U, 1U, 2U },

  /* Computed Parameter: HILReadEncoderTimebase_SamplesI
   * Referenced by: '<S1>/HIL Read Encoder Timebase'
   */
  500U,

  /* Computed Parameter: GameController_BufferSize
   * Referenced by: '<S3>/Game Controller'
   */
  12U,

  /* Computed Parameter: HILInitialize_Active
   * Referenced by: '<S1>/HIL Initialize'
   */
  true,

  /* Computed Parameter: HILInitialize_AOTerminate
   * Referenced by: '<S1>/HIL Initialize'
   */
  true,

  /* Computed Parameter: HILInitialize_AOExit
   * Referenced by: '<S1>/HIL Initialize'
   */
  false,

  /* Computed Parameter: HILInitialize_DOTerminate
   * Referenced by: '<S1>/HIL Initialize'
   */
  true,

  /* Computed Parameter: HILInitialize_DOExit
   * Referenced by: '<S1>/HIL Initialize'
   */
  false,

  /* Computed Parameter: HILInitialize_POTerminate
   * Referenced by: '<S1>/HIL Initialize'
   */
  true,

  /* Computed Parameter: HILInitialize_POExit
   * Referenced by: '<S1>/HIL Initialize'
   */
  false,

  /* Computed Parameter: HILInitialize_CKPStart
   * Referenced by: '<S1>/HIL Initialize'
   */
  false,

  /* Computed Parameter: HILInitialize_CKPEnter
   * Referenced by: '<S1>/HIL Initialize'
   */
  false,

  /* Computed Parameter: HILInitialize_CKStart
   * Referenced by: '<S1>/HIL Initialize'
   */
  false,

  /* Computed Parameter: HILInitialize_CKEnter
   * Referenced by: '<S1>/HIL Initialize'
   */
  false,

  /* Computed Parameter: HILInitialize_AIPStart
   * Referenced by: '<S1>/HIL Initialize'
   */
  true,

  /* Computed Parameter: HILInitialize_AIPEnter
   * Referenced by: '<S1>/HIL Initialize'
   */
  false,

  /* Computed Parameter: HILInitialize_AOPStart
   * Referenced by: '<S1>/HIL Initialize'
   */
  true,

  /* Computed Parameter: HILInitialize_AOPEnter
   * Referenced by: '<S1>/HIL Initialize'
   */
  false,

  /* Computed Parameter: HILInitialize_AOStart
   * Referenced by: '<S1>/HIL Initialize'
   */
  true,

  /* Computed Parameter: HILInitialize_AOEnter
   * Referenced by: '<S1>/HIL Initialize'
   */
  false,

  /* Computed Parameter: HILInitialize_AOReset
   * Referenced by: '<S1>/HIL Initialize'
   */
  false,

  /* Computed Parameter: HILInitialize_DOPStart
   * Referenced by: '<S1>/HIL Initialize'
   */
  false,

  /* Computed Parameter: HILInitialize_DOPEnter
   * Referenced by: '<S1>/HIL Initialize'
   */
  false,

  /* Computed Parameter: HILInitialize_DOStart
   * Referenced by: '<S1>/HIL Initialize'
   */
  true,

  /* Computed Parameter: HILInitialize_DOEnter
   * Referenced by: '<S1>/HIL Initialize'
   */
  false,

  /* Computed Parameter: HILInitialize_DOReset
   * Referenced by: '<S1>/HIL Initialize'
   */
  false,

  /* Computed Parameter: HILInitialize_EIPStart
   * Referenced by: '<S1>/HIL Initialize'
   */
  true,

  /* Computed Parameter: HILInitialize_EIPEnter
   * Referenced by: '<S1>/HIL Initialize'
   */
  false,

  /* Computed Parameter: HILInitialize_EIStart
   * Referenced by: '<S1>/HIL Initialize'
   */
  true,

  /* Computed Parameter: HILInitialize_EIEnter
   * Referenced by: '<S1>/HIL Initialize'
   */
  false,

  /* Computed Parameter: HILInitialize_POPStart
   * Referenced by: '<S1>/HIL Initialize'
   */
  true,

  /* Computed Parameter: HILInitialize_POPEnter
   * Referenced by: '<S1>/HIL Initialize'
   */
  false,

  /* Computed Parameter: HILInitialize_POStart
   * Referenced by: '<S1>/HIL Initialize'
   */
  true,

  /* Computed Parameter: HILInitialize_POEnter
   * Referenced by: '<S1>/HIL Initialize'
   */
  false,

  /* Computed Parameter: HILInitialize_POReset
   * Referenced by: '<S1>/HIL Initialize'
   */
  false,

  /* Computed Parameter: HILInitialize_OOReset
   * Referenced by: '<S1>/HIL Initialize'
   */
  false,

  /* Computed Parameter: HILInitialize_DOFinal
   * Referenced by: '<S1>/HIL Initialize'
   */
  false,

  /* Computed Parameter: HILInitialize_DOInitial
   * Referenced by: '<S1>/HIL Initialize'
   */
  false,

  /* Computed Parameter: HILReadEncoderTimebase_Active
   * Referenced by: '<S1>/HIL Read Encoder Timebase'
   */
  true,

  /* Computed Parameter: HILWriteAnalog_Active
   * Referenced by: '<S1>/HIL Write Analog'
   */
  false,

  /* Computed Parameter: GameController_AutoCenter
   * Referenced by: '<S3>/Game Controller'
   */
  false,

  /* Computed Parameter: GameController_Enabled
   * Referenced by: '<S3>/Game Controller'
   */
  true,

  /* Computed Parameter: HILReadEncoderTimebase_Overflow
   * Referenced by: '<S1>/HIL Read Encoder Timebase'
   */
  1U,

  /* Computed Parameter: ManualSwitch_CurrentSetting
   * Referenced by: '<Root>/Manual Switch'
   */
  1U,

  /* Computed Parameter: GameController_ControllerNumber
   * Referenced by: '<S3>/Game Controller'
   */
  1U
};
