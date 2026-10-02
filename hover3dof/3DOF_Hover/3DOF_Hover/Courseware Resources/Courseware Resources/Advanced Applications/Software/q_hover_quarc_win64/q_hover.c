/*
 * q_hover.c
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
#include "rtwtypes.h"
#include <emmintrin.h>
#include <math.h>
#include "q_hover_private.h"
#include <string.h>
#include "rt_nonfinite.h"
#include "q_hover_dt.h"

/* Block signals (default storage) */
B_q_hover_T q_hover_B;

/* Continuous states */
X_q_hover_T q_hover_X;

/* Disabled State Vector */
XDis_q_hover_T q_hover_XDis;

/* Block states (default storage) */
DW_q_hover_T q_hover_DW;

/* Real-time model */
static RT_MODEL_q_hover_T q_hover_M_;
RT_MODEL_q_hover_T *const q_hover_M = &q_hover_M_;
static void rate_monotonic_scheduler(void);
time_T rt_SimUpdateDiscreteEvents(
  int_T rtmNumSampTimes, void *rtmTimingData, int_T *rtmSampleHitPtr, int_T
  *rtmPerTaskSampleHits )
{
  rtmSampleHitPtr[1] = rtmStepTask(q_hover_M, 1);
  rtmSampleHitPtr[2] = rtmStepTask(q_hover_M, 2);
  UNUSED_PARAMETER(rtmNumSampTimes);
  UNUSED_PARAMETER(rtmTimingData);
  UNUSED_PARAMETER(rtmPerTaskSampleHits);
  return(-1);
}

/*
 *         This function updates active task flag for each subrate
 *         and rate transition flags for tasks that exchange data.
 *         The function assumes rate-monotonic multitasking scheduler.
 *         The function must be called at model base rate so that
 *         the generated code self-manages all its subrates and rate
 *         transition flags.
 */
static void rate_monotonic_scheduler(void)
{
  /* To ensure a deterministic data transfer between two rates,
   * data is transferred at the priority of a fast task and the frequency
   * of the slow task.  The following flags indicate when the data transfer
   * happens.  That is, a rate interaction flag is set true when both rates
   * will run, and false otherwise.
   */

  /* tid 1 shares data with slower tid rate: 2 */
  if (q_hover_M->Timing.TaskCounters.TID[1] == 0) {
    q_hover_M->Timing.RateInteraction.TID1_2 =
      (q_hover_M->Timing.TaskCounters.TID[2] == 0);

    /* update PerTaskSampleHits matrix for non-inline sfcn */
    q_hover_M->Timing.perTaskSampleHits[5] =
      q_hover_M->Timing.RateInteraction.TID1_2;
  }

  /* Compute which subrates run during the next base time step.  Subrates
   * are an integer multiple of the base rate counter.  Therefore, the subtask
   * counter is reset when it reaches its limit (zero means run).
   */
  (q_hover_M->Timing.TaskCounters.TID[2])++;
  if ((q_hover_M->Timing.TaskCounters.TID[2]) > 4) {/* Sample time: [0.01s, 0.0s] */
    q_hover_M->Timing.TaskCounters.TID[2] = 0;
  }
}

/*
 * This function updates continuous states using the ODE1 fixed-step
 * solver algorithm
 */
static void rt_ertODEUpdateContinuousStates(RTWSolverInfo *si )
{
  time_T tnew = rtsiGetSolverStopTime(si);
  time_T h = rtsiGetStepSize(si);
  real_T *x = rtsiGetContStates(si);
  ODE1_IntgData *id = (ODE1_IntgData *)rtsiGetSolverData(si);
  real_T *f0 = id->f[0];
  int_T i;
  int_T nXc = 9;
  rtsiSetSimTimeStep(si,MINOR_TIME_STEP);
  rtsiSetdX(si, f0);
  q_hover_derivatives();
  rtsiSetT(si, tnew);
  for (i = 0; i < nXc; ++i) {
    x[i] += h * f0[i];
  }

  rtsiSetSimTimeStep(si,MAJOR_TIME_STEP);
}

/* Model output function for TID0 */
void q_hover_output0(void)             /* Sample time: [0.0s, 0.0s] */
{
  __m128d tmp;
  __m128d tmp_1;
  real_T rtb_ManualSwitch[6];
  real_T rtb_ManualSwitch_0[6];
  real_T tmp_0[2];
  real_T Gain1_mh_idx_0;
  real_T Gain1_mh_idx_1;
  real_T LimitRateofDesiredAngle_f;
  real_T fallValLimit;
  real_T rtb_DerivativeFilterYaw;
  real_T rtb_HILReadEncoderTimebase_o1;
  real_T rtb_HILReadEncoderTimebase_o2;
  real_T rtb_HILReadEncoderTimebase_o3;
  int32_T i;
  int32_T i_0;
  boolean_T limitedCache_idx_0;
  boolean_T limitedCache_idx_1;
  boolean_T limitedCache_idx_2;
  if (rtmIsMajorTimeStep(q_hover_M)) {
    /* set solver stop time */
    if (!(q_hover_M->Timing.clockTick0+1)) {
      rtsiSetSolverStopTime(&q_hover_M->solverInfo,
                            ((q_hover_M->Timing.clockTickH0 + 1) *
        q_hover_M->Timing.stepSize0 * 4294967296.0));
    } else {
      rtsiSetSolverStopTime(&q_hover_M->solverInfo,
                            ((q_hover_M->Timing.clockTick0 + 1) *
        q_hover_M->Timing.stepSize0 + q_hover_M->Timing.clockTickH0 *
        q_hover_M->Timing.stepSize0 * 4294967296.0));
    }

    {                                  /* Sample time: [0.0s, 0.0s] */
      rate_monotonic_scheduler();
    }
  }                                    /* end MajorTimeStep */

  /* Update absolute time of base rate at minor time step */
  if (rtmIsMinorTimeStep(q_hover_M)) {
    q_hover_M->Timing.t[0] = rtsiGetT(&q_hover_M->solverInfo);
  }

  if (rtmIsMajorTimeStep(q_hover_M)) {
    /* S-Function (hil_read_encoder_timebase_block): '<S1>/HIL Read Encoder Timebase' */

    /* S-Function Block: q_hover/3-DOF Hover/HIL Read Encoder Timebase (hil_read_encoder_timebase_block) */
    {
      t_error result;
      result = hil_task_read_encoder(q_hover_DW.HILReadEncoderTimebase_Task, 1,
        &q_hover_DW.HILReadEncoderTimebase_Buffer[0]);
      if (result < 0) {
        rtb_HILReadEncoderTimebase_o1 = 0;
        rtb_HILReadEncoderTimebase_o2 = 0;
        rtb_HILReadEncoderTimebase_o3 = 0;
        msg_get_error_messageA(NULL, result, _rt_error_message, sizeof
          (_rt_error_message));
        rtmSetErrorStatus(q_hover_M, _rt_error_message);
      } else {
        rtb_HILReadEncoderTimebase_o1 =
          q_hover_DW.HILReadEncoderTimebase_Buffer[0];
        rtb_HILReadEncoderTimebase_o2 =
          q_hover_DW.HILReadEncoderTimebase_Buffer[1];
        rtb_HILReadEncoderTimebase_o3 =
          q_hover_DW.HILReadEncoderTimebase_Buffer[2];
      }
    }

    /* Gain: '<S1>/Encoder Resolution: Pitch' */
    q_hover_B.pitch = q_hover_P.K_EC_P * rtb_HILReadEncoderTimebase_o1;

    /* Gain: '<S1>/Encoder Resolution: Roll ' */
    q_hover_B.roll = q_hover_P.K_EC_R * rtb_HILReadEncoderTimebase_o2;

    /* Gain: '<S1>/Encoder Resolution: Yaw' */
    q_hover_B.yaw = q_hover_P.K_EC_Y * rtb_HILReadEncoderTimebase_o3;

    /* Gain: '<S4>/Convert to  Vector' incorporates:
     *  Constant: '<S4>/Bias Voltage'
     */
    tmp_1 = _mm_set1_pd(q_hover_P.V_bias);

    /* Gain: '<S4>/Convert to  Vector' */
    _mm_storeu_pd(&q_hover_B.ConverttoVector[0], _mm_mul_pd(_mm_loadu_pd
      (&q_hover_P.ConverttoVector_Gain[0]), tmp_1));
    _mm_storeu_pd(&q_hover_B.ConverttoVector[2], _mm_mul_pd(_mm_loadu_pd
      (&q_hover_P.ConverttoVector_Gain[2]), tmp_1));
  }

  /* TransferFcn: '<S1>/Derivative Filter: Roll' incorporates:
   *  TransferFcn: '<S1>/Derivative Filter: Pitch'
   */
  _mm_storeu_pd(&tmp_0[0], _mm_add_pd(_mm_mul_pd(_mm_set_pd
    (q_hover_P.DerivativeFilterRoll_C[0], q_hover_P.DerivativeFilterPitch_C[0]),
    _mm_set_pd(q_hover_X.DerivativeFilterRoll_CSTATE[0],
               q_hover_X.DerivativeFilterPitch_CSTATE[0])), _mm_mul_pd
    (_mm_set_pd(q_hover_P.DerivativeFilterRoll_C[1],
                q_hover_P.DerivativeFilterPitch_C[1]), _mm_set_pd
     (q_hover_X.DerivativeFilterRoll_CSTATE[1],
      q_hover_X.DerivativeFilterPitch_CSTATE[1]))));

  /* TransferFcn: '<S1>/Derivative Filter: Yaw' */
  rtb_DerivativeFilterYaw = q_hover_P.DerivativeFilterYaw_C[0] *
    q_hover_X.DerivativeFilterYaw_CSTATE[0] + q_hover_P.DerivativeFilterYaw_C[1]
    * q_hover_X.DerivativeFilterYaw_CSTATE[1];

  /* SignalGenerator: '<S2>/Signal Generator: Yaw' incorporates:
   *  SignalGenerator: '<S2>/Signal Generator: Pitch'
   *  SignalGenerator: '<S2>/Signal Generator: Roll'
   */
  rtb_HILReadEncoderTimebase_o3 = q_hover_M->Timing.t[0];
  rtb_HILReadEncoderTimebase_o1 = q_hover_P.SignalGeneratorYaw_Frequency *
    rtb_HILReadEncoderTimebase_o3;

  /* SignalGenerator: '<S2>/Signal Generator: Pitch' */
  rtb_HILReadEncoderTimebase_o2 = q_hover_P.SignalGeneratorPitch_Frequency *
    rtb_HILReadEncoderTimebase_o3;

  /* SignalGenerator: '<S2>/Signal Generator: Roll' */
  rtb_HILReadEncoderTimebase_o3 *= q_hover_P.SignalGeneratorRoll_Frequency;

  /* SignalGenerator: '<S2>/Signal Generator: Yaw' */
  if (rtb_HILReadEncoderTimebase_o1 - floor(rtb_HILReadEncoderTimebase_o1) >=
      0.5) {
    LimitRateofDesiredAngle_f = q_hover_P.SignalGeneratorYaw_Amplitude;
  } else {
    LimitRateofDesiredAngle_f = -q_hover_P.SignalGeneratorYaw_Amplitude;
  }

  /* RateLimiter: '<S2>/Limit Rate of Desired Angle' incorporates:
   *  Constant: '<S2>/Constant: Yaw (deg)'
   *  Gain: '<S2>/Amplitude: Yaw (deg)'
   *  Gain: '<S8>/Gain1'
   *  SignalGenerator: '<S2>/Signal Generator: Yaw'
   *  Sum: '<S2>/Sum1'
   */
  Gain1_mh_idx_0 = (q_hover_P.AmplitudeYawdeg_Gain * LimitRateofDesiredAngle_f +
                    q_hover_P.ConstantYawdeg_Value) * q_hover_P.Gain1_Gain;

  /* SignalGenerator: '<S2>/Signal Generator: Pitch' */
  if (rtb_HILReadEncoderTimebase_o2 - floor(rtb_HILReadEncoderTimebase_o2) >=
      0.5) {
    LimitRateofDesiredAngle_f = q_hover_P.SignalGeneratorPitch_Amplitude;
  } else {
    LimitRateofDesiredAngle_f = -q_hover_P.SignalGeneratorPitch_Amplitude;
  }

  /* RateLimiter: '<S2>/Limit Rate of Desired Angle' incorporates:
   *  Constant: '<S2>/Constant: Pitch (deg)'
   *  Gain: '<S2>/Amplitude: Pitch (deg)'
   *  Gain: '<S6>/Gain1'
   *  SignalGenerator: '<S2>/Signal Generator: Pitch'
   *  Sum: '<S2>/Sum'
   */
  Gain1_mh_idx_1 = (q_hover_P.AmplitudePitchdeg_Gain * LimitRateofDesiredAngle_f
                    + q_hover_P.ConstantPitchdeg_Value) * q_hover_P.Gain1_Gain_c;

  /* SignalGenerator: '<S2>/Signal Generator: Roll' */
  if (rtb_HILReadEncoderTimebase_o3 - floor(rtb_HILReadEncoderTimebase_o3) >=
      0.5) {
    LimitRateofDesiredAngle_f = q_hover_P.SignalGeneratorRoll_Amplitude;
  } else {
    LimitRateofDesiredAngle_f = -q_hover_P.SignalGeneratorRoll_Amplitude;
  }

  /* RateLimiter: '<S2>/Limit Rate of Desired Angle' incorporates:
   *  Constant: '<S2>/Constant: Roll (deg)'
   *  Gain: '<S2>/Amplitude: Roll (deg)'
   *  Gain: '<S7>/Gain1'
   *  SignalGenerator: '<S2>/Signal Generator: Roll'
   *  Sum: '<S2>/Sum2'
   */
  rtb_HILReadEncoderTimebase_o3 = (q_hover_P.AmplitudeRolldeg_Gain *
    LimitRateofDesiredAngle_f + q_hover_P.ConstantRolldeg_Value) *
    q_hover_P.Gain1_Gain_d;
  if (q_hover_DW.LastMajorTime == (rtInf)) {
    /* RateLimiter: '<S2>/Limit Rate of Desired Angle' */
    q_hover_B.LimitRateofDesiredAngle[0] = Gain1_mh_idx_0;
    q_hover_B.LimitRateofDesiredAngle[1] = Gain1_mh_idx_1;
    q_hover_B.LimitRateofDesiredAngle[2] = rtb_HILReadEncoderTimebase_o3;
  } else {
    rtb_HILReadEncoderTimebase_o1 = q_hover_M->Timing.t[0];
    rtb_HILReadEncoderTimebase_o2 = rtb_HILReadEncoderTimebase_o1 -
      q_hover_DW.LastMajorTime;
    if (q_hover_DW.LastMajorTime == rtb_HILReadEncoderTimebase_o1) {
      if (q_hover_DW.PrevLimited[0]) {
        /* RateLimiter: '<S2>/Limit Rate of Desired Angle' */
        q_hover_B.LimitRateofDesiredAngle[0] = q_hover_DW.PrevY[0];
      } else {
        /* RateLimiter: '<S2>/Limit Rate of Desired Angle' */
        q_hover_B.LimitRateofDesiredAngle[0] = Gain1_mh_idx_0;
      }

      if (q_hover_DW.PrevLimited[1]) {
        /* RateLimiter: '<S2>/Limit Rate of Desired Angle' */
        q_hover_B.LimitRateofDesiredAngle[1] = q_hover_DW.PrevY[1];
      } else {
        /* RateLimiter: '<S2>/Limit Rate of Desired Angle' */
        q_hover_B.LimitRateofDesiredAngle[1] = Gain1_mh_idx_1;
      }

      if (q_hover_DW.PrevLimited[2]) {
        /* RateLimiter: '<S2>/Limit Rate of Desired Angle' */
        q_hover_B.LimitRateofDesiredAngle[2] = q_hover_DW.PrevY[2];
      } else {
        /* RateLimiter: '<S2>/Limit Rate of Desired Angle' */
        q_hover_B.LimitRateofDesiredAngle[2] = rtb_HILReadEncoderTimebase_o3;
      }
    } else {
      rtb_HILReadEncoderTimebase_o1 = Gain1_mh_idx_0 - q_hover_DW.PrevY[0];
      LimitRateofDesiredAngle_f = rtb_HILReadEncoderTimebase_o2 *
        q_hover_P.CMD_RATE_LIMIT;
      if (rtb_HILReadEncoderTimebase_o1 > LimitRateofDesiredAngle_f) {
        q_hover_B.LimitRateofDesiredAngle[0] = LimitRateofDesiredAngle_f +
          q_hover_DW.PrevY[0];
        limitedCache_idx_0 = true;
      } else {
        fallValLimit = rtb_HILReadEncoderTimebase_o2 * -q_hover_P.CMD_RATE_LIMIT;
        if (rtb_HILReadEncoderTimebase_o1 < fallValLimit) {
          q_hover_B.LimitRateofDesiredAngle[0] = q_hover_DW.PrevY[0] +
            fallValLimit;
          limitedCache_idx_0 = true;
        } else {
          q_hover_B.LimitRateofDesiredAngle[0] = Gain1_mh_idx_0;
          limitedCache_idx_0 = false;
        }
      }

      rtb_HILReadEncoderTimebase_o1 = Gain1_mh_idx_1 - q_hover_DW.PrevY[1];
      if (rtb_HILReadEncoderTimebase_o1 > LimitRateofDesiredAngle_f) {
        q_hover_B.LimitRateofDesiredAngle[1] = LimitRateofDesiredAngle_f +
          q_hover_DW.PrevY[1];
        limitedCache_idx_1 = true;
      } else {
        fallValLimit = rtb_HILReadEncoderTimebase_o2 * -q_hover_P.CMD_RATE_LIMIT;
        if (rtb_HILReadEncoderTimebase_o1 < fallValLimit) {
          q_hover_B.LimitRateofDesiredAngle[1] = q_hover_DW.PrevY[1] +
            fallValLimit;
          limitedCache_idx_1 = true;
        } else {
          q_hover_B.LimitRateofDesiredAngle[1] = Gain1_mh_idx_1;
          limitedCache_idx_1 = false;
        }
      }

      rtb_HILReadEncoderTimebase_o1 = rtb_HILReadEncoderTimebase_o3 -
        q_hover_DW.PrevY[2];
      if (rtb_HILReadEncoderTimebase_o1 > LimitRateofDesiredAngle_f) {
        q_hover_B.LimitRateofDesiredAngle[2] = LimitRateofDesiredAngle_f +
          q_hover_DW.PrevY[2];
        limitedCache_idx_2 = true;
      } else {
        fallValLimit = rtb_HILReadEncoderTimebase_o2 * -q_hover_P.CMD_RATE_LIMIT;
        if (rtb_HILReadEncoderTimebase_o1 < fallValLimit) {
          q_hover_B.LimitRateofDesiredAngle[2] = q_hover_DW.PrevY[2] +
            fallValLimit;
          limitedCache_idx_2 = true;
        } else {
          q_hover_B.LimitRateofDesiredAngle[2] = rtb_HILReadEncoderTimebase_o3;
          limitedCache_idx_2 = false;
        }
      }

      if (rtsiIsModeUpdateTimeStep(&q_hover_M->solverInfo)) {
        q_hover_DW.PrevLimited[0] = limitedCache_idx_0;
        q_hover_DW.PrevLimited[1] = limitedCache_idx_1;
        q_hover_DW.PrevLimited[2] = limitedCache_idx_2;
      }
    }
  }

  /* Integrator: '<S3>/Des Position:  Roll (deg)1' */
  /* Limited  Integrator  */
  if (q_hover_X.DesPositionRolldeg1_CSTATE >= q_hover_P.INT_JOYSTICK_SAT_UPPER)
  {
    q_hover_X.DesPositionRolldeg1_CSTATE = q_hover_P.INT_JOYSTICK_SAT_UPPER;
  } else if (q_hover_X.DesPositionRolldeg1_CSTATE <=
             q_hover_P.INT_JOYSTICK_SAT_LOWER) {
    q_hover_X.DesPositionRolldeg1_CSTATE = q_hover_P.INT_JOYSTICK_SAT_LOWER;
  }

  /* Integrator: '<S3>/Des Position:  Pitch (deg)' */
  /* Limited  Integrator  */
  if (q_hover_X.DesPositionPitchdeg_CSTATE >= q_hover_P.INT_JOYSTICK_SAT_UPPER)
  {
    q_hover_X.DesPositionPitchdeg_CSTATE = q_hover_P.INT_JOYSTICK_SAT_UPPER;
  } else if (q_hover_X.DesPositionPitchdeg_CSTATE <=
             q_hover_P.INT_JOYSTICK_SAT_LOWER) {
    q_hover_X.DesPositionPitchdeg_CSTATE = q_hover_P.INT_JOYSTICK_SAT_LOWER;
  }

  /* Integrator: '<S3>/Des Position:  Roll (deg)' */
  /* Limited  Integrator  */
  if (q_hover_X.DesPositionRolldeg_CSTATE >= q_hover_P.INT_JOYSTICK_SAT_UPPER) {
    q_hover_X.DesPositionRolldeg_CSTATE = q_hover_P.INT_JOYSTICK_SAT_UPPER;
  } else if (q_hover_X.DesPositionRolldeg_CSTATE <=
             q_hover_P.INT_JOYSTICK_SAT_LOWER) {
    q_hover_X.DesPositionRolldeg_CSTATE = q_hover_P.INT_JOYSTICK_SAT_LOWER;
  }

  /* Gain: '<S10>/Gain1' incorporates:
   *  Integrator: '<S3>/Des Position:  Pitch (deg)'
   *  Integrator: '<S3>/Des Position:  Roll (deg)'
   *  Integrator: '<S3>/Des Position:  Roll (deg)1'
   */
  Gain1_mh_idx_0 = q_hover_P.Gain1_Gain_m * q_hover_X.DesPositionRolldeg1_CSTATE;
  Gain1_mh_idx_1 = q_hover_P.Gain1_Gain_m * q_hover_X.DesPositionPitchdeg_CSTATE;
  rtb_HILReadEncoderTimebase_o3 = q_hover_P.Gain1_Gain_m *
    q_hover_X.DesPositionRolldeg_CSTATE;

  /* RateLimiter: '<S3>/Limit Rate of Desired Angle' */
  if (q_hover_DW.LastMajorTime_k == (rtInf)) {
    /* RateLimiter: '<S3>/Limit Rate of Desired Angle' */
    q_hover_B.LimitRateofDesiredAngle_f[0] = Gain1_mh_idx_0;
    q_hover_B.LimitRateofDesiredAngle_f[1] = Gain1_mh_idx_1;
    q_hover_B.LimitRateofDesiredAngle_f[2] = rtb_HILReadEncoderTimebase_o3;
  } else {
    rtb_HILReadEncoderTimebase_o1 = q_hover_M->Timing.t[0];
    rtb_HILReadEncoderTimebase_o2 = rtb_HILReadEncoderTimebase_o1 -
      q_hover_DW.LastMajorTime_k;
    if (q_hover_DW.LastMajorTime_k == rtb_HILReadEncoderTimebase_o1) {
      if (q_hover_DW.PrevLimited_l[0]) {
        /* RateLimiter: '<S3>/Limit Rate of Desired Angle' */
        q_hover_B.LimitRateofDesiredAngle_f[0] = q_hover_DW.PrevY_k[0];
      } else {
        /* RateLimiter: '<S3>/Limit Rate of Desired Angle' */
        q_hover_B.LimitRateofDesiredAngle_f[0] = Gain1_mh_idx_0;
      }

      if (q_hover_DW.PrevLimited_l[1]) {
        /* RateLimiter: '<S3>/Limit Rate of Desired Angle' */
        q_hover_B.LimitRateofDesiredAngle_f[1] = q_hover_DW.PrevY_k[1];
      } else {
        /* RateLimiter: '<S3>/Limit Rate of Desired Angle' */
        q_hover_B.LimitRateofDesiredAngle_f[1] = Gain1_mh_idx_1;
      }

      if (q_hover_DW.PrevLimited_l[2]) {
        /* RateLimiter: '<S3>/Limit Rate of Desired Angle' */
        q_hover_B.LimitRateofDesiredAngle_f[2] = q_hover_DW.PrevY_k[2];
      } else {
        /* RateLimiter: '<S3>/Limit Rate of Desired Angle' */
        q_hover_B.LimitRateofDesiredAngle_f[2] = rtb_HILReadEncoderTimebase_o3;
      }
    } else {
      rtb_HILReadEncoderTimebase_o1 = Gain1_mh_idx_0 - q_hover_DW.PrevY_k[0];
      LimitRateofDesiredAngle_f = rtb_HILReadEncoderTimebase_o2 *
        q_hover_P.CMD_RATE_LIMIT;
      if (rtb_HILReadEncoderTimebase_o1 > LimitRateofDesiredAngle_f) {
        q_hover_B.LimitRateofDesiredAngle_f[0] = LimitRateofDesiredAngle_f +
          q_hover_DW.PrevY_k[0];
        limitedCache_idx_0 = true;
      } else {
        fallValLimit = rtb_HILReadEncoderTimebase_o2 * -q_hover_P.CMD_RATE_LIMIT;
        if (rtb_HILReadEncoderTimebase_o1 < fallValLimit) {
          q_hover_B.LimitRateofDesiredAngle_f[0] = q_hover_DW.PrevY_k[0] +
            fallValLimit;
          limitedCache_idx_0 = true;
        } else {
          q_hover_B.LimitRateofDesiredAngle_f[0] = Gain1_mh_idx_0;
          limitedCache_idx_0 = false;
        }
      }

      rtb_HILReadEncoderTimebase_o1 = Gain1_mh_idx_1 - q_hover_DW.PrevY_k[1];
      if (rtb_HILReadEncoderTimebase_o1 > LimitRateofDesiredAngle_f) {
        q_hover_B.LimitRateofDesiredAngle_f[1] = LimitRateofDesiredAngle_f +
          q_hover_DW.PrevY_k[1];
        limitedCache_idx_1 = true;
      } else {
        fallValLimit = rtb_HILReadEncoderTimebase_o2 * -q_hover_P.CMD_RATE_LIMIT;
        if (rtb_HILReadEncoderTimebase_o1 < fallValLimit) {
          q_hover_B.LimitRateofDesiredAngle_f[1] = q_hover_DW.PrevY_k[1] +
            fallValLimit;
          limitedCache_idx_1 = true;
        } else {
          q_hover_B.LimitRateofDesiredAngle_f[1] = Gain1_mh_idx_1;
          limitedCache_idx_1 = false;
        }
      }

      rtb_HILReadEncoderTimebase_o1 = rtb_HILReadEncoderTimebase_o3 -
        q_hover_DW.PrevY_k[2];
      if (rtb_HILReadEncoderTimebase_o1 > LimitRateofDesiredAngle_f) {
        q_hover_B.LimitRateofDesiredAngle_f[2] = LimitRateofDesiredAngle_f +
          q_hover_DW.PrevY_k[2];
        limitedCache_idx_2 = true;
      } else {
        fallValLimit = rtb_HILReadEncoderTimebase_o2 * -q_hover_P.CMD_RATE_LIMIT;
        if (rtb_HILReadEncoderTimebase_o1 < fallValLimit) {
          q_hover_B.LimitRateofDesiredAngle_f[2] = q_hover_DW.PrevY_k[2] +
            fallValLimit;
          limitedCache_idx_2 = true;
        } else {
          q_hover_B.LimitRateofDesiredAngle_f[2] = rtb_HILReadEncoderTimebase_o3;
          limitedCache_idx_2 = false;
        }
      }

      if (rtsiIsModeUpdateTimeStep(&q_hover_M->solverInfo)) {
        q_hover_DW.PrevLimited_l[0] = limitedCache_idx_0;
        q_hover_DW.PrevLimited_l[1] = limitedCache_idx_1;
        q_hover_DW.PrevLimited_l[2] = limitedCache_idx_2;
      }
    }
  }

  /* End of RateLimiter: '<S3>/Limit Rate of Desired Angle' */

  /* ManualSwitch: '<Root>/Manual Switch' incorporates:
   *  Gain: '<S2>/Convert to State with 6 Elements'
   *  Gain: '<S3>/Convert to State with 6 Elements'
   */
  if (q_hover_P.ManualSwitch_CurrentSetting == 1) {
    /* Gain: '<S2>/Convert to State with 6 Elements' */
    rtb_HILReadEncoderTimebase_o2 = q_hover_B.LimitRateofDesiredAngle[1];
    LimitRateofDesiredAngle_f = q_hover_B.LimitRateofDesiredAngle[0];
    Gain1_mh_idx_0 = q_hover_B.LimitRateofDesiredAngle[2];
    for (i = 0; i <= 4; i += 2) {
      _mm_storeu_pd(&rtb_ManualSwitch[i], _mm_add_pd(_mm_add_pd(_mm_mul_pd
        (_mm_loadu_pd(&q_hover_P.ConverttoStatewith6Elements_Gai[i + 6]),
         _mm_set1_pd(rtb_HILReadEncoderTimebase_o2)), _mm_mul_pd(_mm_loadu_pd
        (&q_hover_P.ConverttoStatewith6Elements_Gai[i]), _mm_set1_pd
        (LimitRateofDesiredAngle_f))), _mm_mul_pd(_mm_loadu_pd
        (&q_hover_P.ConverttoStatewith6Elements_Gai[i + 12]), _mm_set1_pd
        (Gain1_mh_idx_0))));
    }
  } else {
    /* Gain: '<S3>/Convert to State with 6 Elements' */
    rtb_HILReadEncoderTimebase_o2 = q_hover_B.LimitRateofDesiredAngle_f[1];
    LimitRateofDesiredAngle_f = q_hover_B.LimitRateofDesiredAngle_f[0];
    Gain1_mh_idx_0 = q_hover_B.LimitRateofDesiredAngle_f[2];
    for (i = 0; i <= 4; i += 2) {
      _mm_storeu_pd(&rtb_ManualSwitch[i], _mm_add_pd(_mm_add_pd(_mm_mul_pd
        (_mm_loadu_pd(&q_hover_P.ConverttoStatewith6Elements_G_i[i + 6]),
         _mm_set1_pd(rtb_HILReadEncoderTimebase_o2)), _mm_mul_pd(_mm_loadu_pd
        (&q_hover_P.ConverttoStatewith6Elements_G_i[i]), _mm_set1_pd
        (LimitRateofDesiredAngle_f))), _mm_mul_pd(_mm_loadu_pd
        (&q_hover_P.ConverttoStatewith6Elements_G_i[i + 12]), _mm_set1_pd
        (Gain1_mh_idx_0))));
    }
  }

  /* End of ManualSwitch: '<Root>/Manual Switch' */

  /* Gain: '<S1>/Cable Gain Pre-Compensation' */
  rtb_HILReadEncoderTimebase_o1 = 1.0 / q_hover_P.K_AMP;

  /* Sum: '<S4>/Sum5' */
  tmp_1 = _mm_sub_pd(_mm_loadu_pd(&rtb_ManualSwitch[0]), _mm_set_pd
                     (q_hover_B.pitch, q_hover_B.yaw));
  _mm_storeu_pd(&rtb_ManualSwitch_0[0], tmp_1);
  tmp_1 = _mm_sub_pd(_mm_loadu_pd(&rtb_ManualSwitch[2]), _mm_set_pd
                     (rtb_DerivativeFilterYaw, q_hover_B.roll));
  _mm_storeu_pd(&rtb_ManualSwitch_0[2], tmp_1);
  tmp_1 = _mm_sub_pd(_mm_loadu_pd(&rtb_ManualSwitch[4]), _mm_set_pd(tmp_0[1],
    tmp_0[0]));
  _mm_storeu_pd(&rtb_ManualSwitch_0[4], tmp_1);
  for (i = 0; i < 4; i++) {
    /* Sum: '<S4>/Sum4' incorporates:
     *  Gain: '<S4>/Control Gain: K'
     */
    LimitRateofDesiredAngle_f = 0.0;
    for (i_0 = 0; i_0 < 6; i_0++) {
      LimitRateofDesiredAngle_f += q_hover_P.K[(i_0 << 2) + i] *
        rtb_ManualSwitch_0[i_0];
    }

    LimitRateofDesiredAngle_f += q_hover_B.ConverttoVector[i];

    /* End of Sum: '<S4>/Sum4' */

    /* Saturate: '<S1>/UPM Voltage Limit: 0 to VMAX_AMP' */
    if (LimitRateofDesiredAngle_f > q_hover_P.VMAX_AMP) {
      LimitRateofDesiredAngle_f = q_hover_P.VMAX_AMP;
    } else if (LimitRateofDesiredAngle_f <
               q_hover_P.UPMVoltageLimit0toVMAX_AMP_Lowe) {
      LimitRateofDesiredAngle_f = q_hover_P.UPMVoltageLimit0toVMAX_AMP_Lowe;
    }

    /* Gain: '<S1>/Cable Gain Pre-Compensation' incorporates:
     *  Saturate: '<S1>/UPM Voltage Limit: 0 to VMAX_AMP'
     */
    q_hover_B.CableGainPreCompensation[i] = rtb_HILReadEncoderTimebase_o1 *
      LimitRateofDesiredAngle_f;
  }

  if (rtmIsMajorTimeStep(q_hover_M)) {
    /* S-Function (hil_write_analog_block): '<S1>/HIL Write Analog' */

    /* S-Function Block: q_hover/3-DOF Hover/HIL Write Analog (hil_write_analog_block) */
    {
      t_error result;
      result = hil_write_analog(q_hover_DW.HILInitialize_Card,
        q_hover_P.HILWriteAnalog_channels, 4,
        &q_hover_B.CableGainPreCompensation[0]);
      if (result < 0) {
        msg_get_error_messageA(NULL, result, _rt_error_message, sizeof
          (_rt_error_message));
        rtmSetErrorStatus(q_hover_M, _rt_error_message);
      }
    }
  }

  /* Gain: '<S1>/Cable Gain' */
  tmp_1 = _mm_set1_pd(q_hover_P.K_AMP);
  tmp = _mm_mul_pd(tmp_1, _mm_loadu_pd(&q_hover_B.CableGainPreCompensation[0]));

  /* Gain: '<S1>/Cable Gain' */
  _mm_storeu_pd(&q_hover_B.CableGain[0], tmp);

  /* Gain: '<S1>/Cable Gain' */
  tmp_1 = _mm_mul_pd(tmp_1, _mm_loadu_pd(&q_hover_B.CableGainPreCompensation[2]));

  /* Gain: '<S1>/Cable Gain' */
  _mm_storeu_pd(&q_hover_B.CableGain[2], tmp_1);
  for (i = 0; i <= 4; i += 2) {
    /* Gain: '<S11>/Gain' */
    tmp_1 = _mm_loadu_pd(&rtb_ManualSwitch[i]);

    /* Gain: '<S11>/Gain' */
    _mm_storeu_pd(&q_hover_B.Gain[i], _mm_mul_pd(_mm_set1_pd(q_hover_P.Gain_Gain),
      tmp_1));
  }

  /* Gain: '<S12>/Gain' */
  q_hover_B.Gain_p[0] = q_hover_P.Gain_Gain_g * q_hover_B.yaw;
  q_hover_B.Gain_p[1] = q_hover_P.Gain_Gain_g * q_hover_B.pitch;
  q_hover_B.Gain_p[2] = q_hover_P.Gain_Gain_g * q_hover_B.roll;
  q_hover_B.Gain_p[3] = q_hover_P.Gain_Gain_g * rtb_DerivativeFilterYaw;
  q_hover_B.Gain_p[4] = q_hover_P.Gain_Gain_g * tmp_0[0];
  q_hover_B.Gain_p[5] = q_hover_P.Gain_Gain_g * tmp_0[1];
  if (rtmIsMajorTimeStep(q_hover_M)) {
    /* RateTransition: '<S3>/Rate Transition' */
    if (q_hover_M->Timing.RateInteraction.TID1_2) {
      /* RateTransition: '<S3>/Rate Transition' */
      q_hover_B.RateTransition = q_hover_DW.RateTransition_Buffer0;

      /* RateTransition: '<S3>/Rate Transition1' */
      q_hover_B.RateTransition1 = q_hover_DW.RateTransition1_Buffer0;

      /* RateTransition: '<S3>/Rate Transition2' */
      q_hover_B.RateTransition2 = q_hover_DW.RateTransition2_Buffer0;
    }

    /* End of RateTransition: '<S3>/Rate Transition' */
  }
}

/* Model update function for TID0 */
void q_hover_update0(void)             /* Sample time: [0.0s, 0.0s] */
{
  real_T LastMajorTime_tmp;

  /* Update for RateLimiter: '<S2>/Limit Rate of Desired Angle' incorporates:
   *  RateLimiter: '<S3>/Limit Rate of Desired Angle'
   */
  LastMajorTime_tmp = q_hover_M->Timing.t[0];
  q_hover_DW.LastMajorTime = LastMajorTime_tmp;
  q_hover_DW.PrevY[0] = q_hover_B.LimitRateofDesiredAngle[0];

  /* Update for RateLimiter: '<S3>/Limit Rate of Desired Angle' */
  q_hover_DW.PrevY_k[0] = q_hover_B.LimitRateofDesiredAngle_f[0];

  /* Update for RateLimiter: '<S2>/Limit Rate of Desired Angle' */
  q_hover_DW.PrevY[1] = q_hover_B.LimitRateofDesiredAngle[1];

  /* Update for RateLimiter: '<S3>/Limit Rate of Desired Angle' */
  q_hover_DW.PrevY_k[1] = q_hover_B.LimitRateofDesiredAngle_f[1];

  /* Update for RateLimiter: '<S2>/Limit Rate of Desired Angle' */
  q_hover_DW.PrevY[2] = q_hover_B.LimitRateofDesiredAngle[2];

  /* Update for RateLimiter: '<S3>/Limit Rate of Desired Angle' */
  q_hover_DW.PrevY_k[2] = q_hover_B.LimitRateofDesiredAngle_f[2];
  q_hover_DW.LastMajorTime_k = LastMajorTime_tmp;
  if (rtmIsMajorTimeStep(q_hover_M)) {
    rt_ertODEUpdateContinuousStates(&q_hover_M->solverInfo);
  }

  /* Update absolute time */
  /* The "clockTick0" counts the number of times the code of this task has
   * been executed. The absolute time is the multiplication of "clockTick0"
   * and "Timing.stepSize0". Size of "clockTick0" ensures timer will not
   * overflow during the application lifespan selected.
   * Timer of this task consists of two 32 bit unsigned integers.
   * The two integers represent the low bits Timing.clockTick0 and the high bits
   * Timing.clockTickH0. When the low bit overflows to 0, the high bits increment.
   */
  if (!(++q_hover_M->Timing.clockTick0)) {
    ++q_hover_M->Timing.clockTickH0;
  }

  q_hover_M->Timing.t[0] = rtsiGetSolverStopTime(&q_hover_M->solverInfo);

  /* Update absolute time */
  /* The "clockTick1" counts the number of times the code of this task has
   * been executed. The absolute time is the multiplication of "clockTick1"
   * and "Timing.stepSize1". Size of "clockTick1" ensures timer will not
   * overflow during the application lifespan selected.
   * Timer of this task consists of two 32 bit unsigned integers.
   * The two integers represent the low bits Timing.clockTick1 and the high bits
   * Timing.clockTickH1. When the low bit overflows to 0, the high bits increment.
   */
  if (!(++q_hover_M->Timing.clockTick1)) {
    ++q_hover_M->Timing.clockTickH1;
  }

  q_hover_M->Timing.t[1] = q_hover_M->Timing.clockTick1 *
    q_hover_M->Timing.stepSize1 + q_hover_M->Timing.clockTickH1 *
    q_hover_M->Timing.stepSize1 * 4294967296.0;
}

/* Derivatives for root system: '<Root>' */
void q_hover_derivatives(void)
{
  XDot_q_hover_T *_rtXdot;
  boolean_T lsat;
  boolean_T usat;
  _rtXdot = ((XDot_q_hover_T *) q_hover_M->derivs);

  /* Derivatives for TransferFcn: '<S1>/Derivative Filter: Pitch' */
  _rtXdot->DerivativeFilterPitch_CSTATE[0] = q_hover_P.DerivativeFilterPitch_A[0]
    * q_hover_X.DerivativeFilterPitch_CSTATE[0];
  _rtXdot->DerivativeFilterPitch_CSTATE[0] += q_hover_P.DerivativeFilterPitch_A
    [1] * q_hover_X.DerivativeFilterPitch_CSTATE[1];
  _rtXdot->DerivativeFilterPitch_CSTATE[1] =
    q_hover_X.DerivativeFilterPitch_CSTATE[0];
  _rtXdot->DerivativeFilterPitch_CSTATE[0] += q_hover_B.pitch;

  /* Derivatives for TransferFcn: '<S1>/Derivative Filter: Roll' */
  _rtXdot->DerivativeFilterRoll_CSTATE[0] = q_hover_P.DerivativeFilterRoll_A[0] *
    q_hover_X.DerivativeFilterRoll_CSTATE[0];
  _rtXdot->DerivativeFilterRoll_CSTATE[0] += q_hover_P.DerivativeFilterRoll_A[1]
    * q_hover_X.DerivativeFilterRoll_CSTATE[1];
  _rtXdot->DerivativeFilterRoll_CSTATE[1] =
    q_hover_X.DerivativeFilterRoll_CSTATE[0];
  _rtXdot->DerivativeFilterRoll_CSTATE[0] += q_hover_B.roll;

  /* Derivatives for TransferFcn: '<S1>/Derivative Filter: Yaw' */
  _rtXdot->DerivativeFilterYaw_CSTATE[0] = q_hover_P.DerivativeFilterYaw_A[0] *
    q_hover_X.DerivativeFilterYaw_CSTATE[0];
  _rtXdot->DerivativeFilterYaw_CSTATE[0] += q_hover_P.DerivativeFilterYaw_A[1] *
    q_hover_X.DerivativeFilterYaw_CSTATE[1];
  _rtXdot->DerivativeFilterYaw_CSTATE[1] = q_hover_X.DerivativeFilterYaw_CSTATE
    [0];
  _rtXdot->DerivativeFilterYaw_CSTATE[0] += q_hover_B.yaw;

  /* Derivatives for Integrator: '<S3>/Des Position:  Roll (deg)1' */
  lsat = (q_hover_X.DesPositionRolldeg1_CSTATE <=
          q_hover_P.INT_JOYSTICK_SAT_LOWER);
  usat = (q_hover_X.DesPositionRolldeg1_CSTATE >=
          q_hover_P.INT_JOYSTICK_SAT_UPPER);
  if (((!lsat) && (!usat)) || (lsat && (q_hover_B.RateTransition2 > 0.0)) ||
      (usat && (q_hover_B.RateTransition2 < 0.0))) {
    _rtXdot->DesPositionRolldeg1_CSTATE = q_hover_B.RateTransition2;
  } else {
    /* in saturation */
    _rtXdot->DesPositionRolldeg1_CSTATE = 0.0;
  }

  /* End of Derivatives for Integrator: '<S3>/Des Position:  Roll (deg)1' */

  /* Derivatives for Integrator: '<S3>/Des Position:  Pitch (deg)' */
  lsat = (q_hover_X.DesPositionPitchdeg_CSTATE <=
          q_hover_P.INT_JOYSTICK_SAT_LOWER);
  usat = (q_hover_X.DesPositionPitchdeg_CSTATE >=
          q_hover_P.INT_JOYSTICK_SAT_UPPER);
  if (((!lsat) && (!usat)) || (lsat && (q_hover_B.RateTransition1 > 0.0)) ||
      (usat && (q_hover_B.RateTransition1 < 0.0))) {
    _rtXdot->DesPositionPitchdeg_CSTATE = q_hover_B.RateTransition1;
  } else {
    /* in saturation */
    _rtXdot->DesPositionPitchdeg_CSTATE = 0.0;
  }

  /* End of Derivatives for Integrator: '<S3>/Des Position:  Pitch (deg)' */

  /* Derivatives for Integrator: '<S3>/Des Position:  Roll (deg)' */
  lsat = (q_hover_X.DesPositionRolldeg_CSTATE <=
          q_hover_P.INT_JOYSTICK_SAT_LOWER);
  usat = (q_hover_X.DesPositionRolldeg_CSTATE >=
          q_hover_P.INT_JOYSTICK_SAT_UPPER);
  if (((!lsat) && (!usat)) || (lsat && (q_hover_B.RateTransition > 0.0)) ||
      (usat && (q_hover_B.RateTransition < 0.0))) {
    _rtXdot->DesPositionRolldeg_CSTATE = q_hover_B.RateTransition;
  } else {
    /* in saturation */
    _rtXdot->DesPositionRolldeg_CSTATE = 0.0;
  }

  /* End of Derivatives for Integrator: '<S3>/Des Position:  Roll (deg)' */
}

/* Model output function for TID2 */
void q_hover_output2(void)             /* Sample time: [0.01s, 0.0s] */
{
  real_T rtb_GameController_o3[2];
  real_T rtb_DeadZoneXV;
  real_T rtb_DeadZoneYV;
  real_T rtb_Divide;
  real_T rtb_GameController_o9;

  /* S-Function (game_controller_block): '<S3>/Game Controller' */

  /* S-Function Block: q_hover/Desired Position from Joystick/Game Controller (game_controller_block) */
  {
    if (q_hover_P.GameController_Enabled) {
      t_game_controller_states state;
      t_boolean new_data;
      t_error result;
      result = game_controller_poll(q_hover_DW.GameController_Controller, &state,
        &new_data);
      if (result < 0) {
        new_data = false;
      }

      rtb_GameController_o3[0] = state.sliders[0];
      rtb_GameController_o3[1] = state.sliders[1];
      rtb_DeadZoneXV = state.x;
      rtb_DeadZoneYV = state.y;
      rtb_Divide = state.z;
      q_hover_B.GameController_o7 = state.rx;
      q_hover_B.GameController_o8 = state.ry;
      rtb_GameController_o9 = state.rz;
    } else {
      rtb_GameController_o3[0] = 0;
      rtb_GameController_o3[1] = 0;
      rtb_DeadZoneXV = 0;
      rtb_DeadZoneYV = 0;
      rtb_Divide = 0;
      q_hover_B.GameController_o7 = 0;
      q_hover_B.GameController_o8 = 0;
      rtb_GameController_o9 = 0;
    }
  }

  /* Product: '<S9>/Divide' incorporates:
   *  Bias: '<S9>/Bias'
   *  Constant: '<S9>/Constant'
   *  Gain: '<S9>/Inverse'
   *  Sum: '<S3>/Sum'
   */
  rtb_Divide = ((rtb_GameController_o3[0] + rtb_Divide) * q_hover_P.Inverse_Gain
                + q_hover_P.Bias_Bias) / q_hover_P.Constant_Value;

  /* DeadZone: '<S3>/Dead Zone: X (V)' */
  if (rtb_DeadZoneXV > q_hover_P.JOYSTICK_X_DZ) {
    rtb_DeadZoneXV -= q_hover_P.JOYSTICK_X_DZ;
  } else if (rtb_DeadZoneXV >= -q_hover_P.JOYSTICK_X_DZ) {
    rtb_DeadZoneXV = 0.0;
  } else {
    rtb_DeadZoneXV -= -q_hover_P.JOYSTICK_X_DZ;
  }

  /* RateTransition: '<S3>/Rate Transition' incorporates:
   *  DeadZone: '<S3>/Dead Zone: X (V)'
   *  Gain: '<S3>/Calibration: X  (deg//s//V)'
   *  Product: '<S3>/Yaw Speed Adj.'
   */
  q_hover_DW.RateTransition_Buffer0 = rtb_DeadZoneXV * rtb_Divide *
    q_hover_P.K_JOYSTICK_X;

  /* DeadZone: '<S3>/Dead Zone: Y (V)' */
  if (rtb_DeadZoneYV > q_hover_P.JOYSTICK_Y_DZ) {
    rtb_DeadZoneXV = rtb_DeadZoneYV - q_hover_P.JOYSTICK_Y_DZ;
  } else if (rtb_DeadZoneYV >= -q_hover_P.JOYSTICK_Y_DZ) {
    rtb_DeadZoneXV = 0.0;
  } else {
    rtb_DeadZoneXV = rtb_DeadZoneYV - (-q_hover_P.JOYSTICK_Y_DZ);
  }

  /* RateTransition: '<S3>/Rate Transition1' incorporates:
   *  DeadZone: '<S3>/Dead Zone: Y (V)'
   *  Gain: '<S3>/Calibration: Y  (deg//s//V)'
   *  Product: '<S3>/Pitch Speed Adj'
   */
  q_hover_DW.RateTransition1_Buffer0 = rtb_DeadZoneXV * rtb_Divide *
    q_hover_P.K_JOYSTICK_Y;

  /* RateTransition: '<S3>/Rate Transition2' incorporates:
   *  Gain: '<S3>/Calibration: X  (deg//s//V)1'
   */
  q_hover_DW.RateTransition2_Buffer0 = q_hover_P.CalibrationXdegsV1_Gain *
    rtb_GameController_o9;
}

/* Model update function for TID2 */
void q_hover_update2(void)             /* Sample time: [0.01s, 0.0s] */
{
  /* Update absolute time */
  /* The "clockTick2" counts the number of times the code of this task has
   * been executed. The absolute time is the multiplication of "clockTick2"
   * and "Timing.stepSize2". Size of "clockTick2" ensures timer will not
   * overflow during the application lifespan selected.
   * Timer of this task consists of two 32 bit unsigned integers.
   * The two integers represent the low bits Timing.clockTick2 and the high bits
   * Timing.clockTickH2. When the low bit overflows to 0, the high bits increment.
   */
  if (!(++q_hover_M->Timing.clockTick2)) {
    ++q_hover_M->Timing.clockTickH2;
  }

  q_hover_M->Timing.t[2] = q_hover_M->Timing.clockTick2 *
    q_hover_M->Timing.stepSize2 + q_hover_M->Timing.clockTickH2 *
    q_hover_M->Timing.stepSize2 * 4294967296.0;
}

/* Use this function only if you need to maintain compatibility with an existing static main program. */
void q_hover_output(int_T tid)
{
  switch (tid) {
   case 0 :
    q_hover_output0();
    break;

   case 2 :
    q_hover_output2();
    break;

   default :
    /* do nothing */
    break;
  }
}

/* Use this function only if you need to maintain compatibility with an existing static main program. */
void q_hover_update(int_T tid)
{
  switch (tid) {
   case 0 :
    q_hover_update0();
    break;

   case 2 :
    q_hover_update2();
    break;

   default :
    /* do nothing */
    break;
  }
}

/* Model initialize function */
void q_hover_initialize(void)
{
  /* Start for S-Function (hil_initialize_block): '<S1>/HIL Initialize' */

  /* S-Function Block: q_hover/3-DOF Hover/HIL Initialize (hil_initialize_block) */
  {
    t_int result;
    t_boolean is_switching;
    result = hil_open("q8_usb", "0", &q_hover_DW.HILInitialize_Card);
    if (result < 0) {
      msg_get_error_messageA(NULL, result, _rt_error_message, sizeof
        (_rt_error_message));
      rtmSetErrorStatus(q_hover_M, _rt_error_message);
      return;
    }

    is_switching = false;
    result = hil_set_card_specific_options(q_hover_DW.HILInitialize_Card,
      "update_rate=normal", 19);
    if (result < 0) {
      msg_get_error_messageA(NULL, result, _rt_error_message, sizeof
        (_rt_error_message));
      rtmSetErrorStatus(q_hover_M, _rt_error_message);
      return;
    }

    result = hil_watchdog_clear(q_hover_DW.HILInitialize_Card);
    if (result < 0 && result != -QERR_HIL_WATCHDOG_CLEAR) {
      msg_get_error_messageA(NULL, result, _rt_error_message, sizeof
        (_rt_error_message));
      rtmSetErrorStatus(q_hover_M, _rt_error_message);
      return;
    }

    if ((q_hover_P.HILInitialize_AIPStart && !is_switching) ||
        (q_hover_P.HILInitialize_AIPEnter && is_switching)) {
      {
        int_T i1;
        real_T *dw_AIMinimums = &q_hover_DW.HILInitialize_AIMinimums[0];
        for (i1=0; i1 < 8; i1++) {
          dw_AIMinimums[i1] = (q_hover_P.HILInitialize_AILow);
        }
      }

      {
        int_T i1;
        real_T *dw_AIMaximums = &q_hover_DW.HILInitialize_AIMaximums[0];
        for (i1=0; i1 < 8; i1++) {
          dw_AIMaximums[i1] = q_hover_P.HILInitialize_AIHigh;
        }
      }

      result = hil_set_analog_input_ranges(q_hover_DW.HILInitialize_Card,
        q_hover_P.HILInitialize_AIChannels, 8U,
        &q_hover_DW.HILInitialize_AIMinimums[0],
        &q_hover_DW.HILInitialize_AIMaximums[0]);
      if (result < 0) {
        msg_get_error_messageA(NULL, result, _rt_error_message, sizeof
          (_rt_error_message));
        rtmSetErrorStatus(q_hover_M, _rt_error_message);
        return;
      }
    }

    if ((q_hover_P.HILInitialize_AOPStart && !is_switching) ||
        (q_hover_P.HILInitialize_AOPEnter && is_switching)) {
      {
        int_T i1;
        real_T *dw_AOMinimums = &q_hover_DW.HILInitialize_AOMinimums[0];
        for (i1=0; i1 < 8; i1++) {
          dw_AOMinimums[i1] = (q_hover_P.HILInitialize_AOLow);
        }
      }

      {
        int_T i1;
        real_T *dw_AOMaximums = &q_hover_DW.HILInitialize_AOMaximums[0];
        for (i1=0; i1 < 8; i1++) {
          dw_AOMaximums[i1] = q_hover_P.HILInitialize_AOHigh;
        }
      }

      result = hil_set_analog_output_ranges(q_hover_DW.HILInitialize_Card,
        q_hover_P.HILInitialize_AOChannels, 8U,
        &q_hover_DW.HILInitialize_AOMinimums[0],
        &q_hover_DW.HILInitialize_AOMaximums[0]);
      if (result < 0) {
        msg_get_error_messageA(NULL, result, _rt_error_message, sizeof
          (_rt_error_message));
        rtmSetErrorStatus(q_hover_M, _rt_error_message);
        return;
      }
    }

    if ((q_hover_P.HILInitialize_AOStart && !is_switching) ||
        (q_hover_P.HILInitialize_AOEnter && is_switching)) {
      {
        int_T i1;
        real_T *dw_AOVoltages = &q_hover_DW.HILInitialize_AOVoltages[0];
        for (i1=0; i1 < 8; i1++) {
          dw_AOVoltages[i1] = q_hover_P.HILInitialize_AOInitial;
        }
      }

      result = hil_write_analog(q_hover_DW.HILInitialize_Card,
        q_hover_P.HILInitialize_AOChannels, 8U,
        &q_hover_DW.HILInitialize_AOVoltages[0]);
      if (result < 0) {
        msg_get_error_messageA(NULL, result, _rt_error_message, sizeof
          (_rt_error_message));
        rtmSetErrorStatus(q_hover_M, _rt_error_message);
        return;
      }
    }

    if (q_hover_P.HILInitialize_AOReset) {
      {
        int_T i1;
        real_T *dw_AOVoltages = &q_hover_DW.HILInitialize_AOVoltages[0];
        for (i1=0; i1 < 8; i1++) {
          dw_AOVoltages[i1] = q_hover_P.HILInitialize_AOWatchdog;
        }
      }

      result = hil_watchdog_set_analog_expiration_state
        (q_hover_DW.HILInitialize_Card, q_hover_P.HILInitialize_AOChannels, 8U,
         &q_hover_DW.HILInitialize_AOVoltages[0]);
      if (result < 0) {
        msg_get_error_messageA(NULL, result, _rt_error_message, sizeof
          (_rt_error_message));
        rtmSetErrorStatus(q_hover_M, _rt_error_message);
        return;
      }
    }

    result = hil_set_digital_directions(q_hover_DW.HILInitialize_Card, NULL, 0U,
      q_hover_P.HILInitialize_DOChannels, 4U);
    if (result < 0) {
      msg_get_error_messageA(NULL, result, _rt_error_message, sizeof
        (_rt_error_message));
      rtmSetErrorStatus(q_hover_M, _rt_error_message);
      return;
    }

    if ((q_hover_P.HILInitialize_DOStart && !is_switching) ||
        (q_hover_P.HILInitialize_DOEnter && is_switching)) {
      q_hover_DW.HILInitialize_DOBits[0] = q_hover_P.HILInitialize_DOInitial;
      q_hover_DW.HILInitialize_DOBits[1] = q_hover_P.HILInitialize_DOInitial;
      q_hover_DW.HILInitialize_DOBits[2] = q_hover_P.HILInitialize_DOInitial;
      q_hover_DW.HILInitialize_DOBits[3] = q_hover_P.HILInitialize_DOInitial;
      result = hil_write_digital(q_hover_DW.HILInitialize_Card,
        q_hover_P.HILInitialize_DOChannels, 4U, (t_boolean *)
        &q_hover_DW.HILInitialize_DOBits[0]);
      if (result < 0) {
        msg_get_error_messageA(NULL, result, _rt_error_message, sizeof
          (_rt_error_message));
        rtmSetErrorStatus(q_hover_M, _rt_error_message);
        return;
      }
    }

    if (q_hover_P.HILInitialize_DOReset) {
      q_hover_DW.HILInitialize_DOStates[0] = q_hover_P.HILInitialize_DOWatchdog;
      q_hover_DW.HILInitialize_DOStates[1] = q_hover_P.HILInitialize_DOWatchdog;
      q_hover_DW.HILInitialize_DOStates[2] = q_hover_P.HILInitialize_DOWatchdog;
      q_hover_DW.HILInitialize_DOStates[3] = q_hover_P.HILInitialize_DOWatchdog;
      result = hil_watchdog_set_digital_expiration_state
        (q_hover_DW.HILInitialize_Card, q_hover_P.HILInitialize_DOChannels, 4U,
         (const t_digital_state *) &q_hover_DW.HILInitialize_DOStates[0]);
      if (result < 0) {
        msg_get_error_messageA(NULL, result, _rt_error_message, sizeof
          (_rt_error_message));
        rtmSetErrorStatus(q_hover_M, _rt_error_message);
        return;
      }
    }

    if ((q_hover_P.HILInitialize_EIPStart && !is_switching) ||
        (q_hover_P.HILInitialize_EIPEnter && is_switching)) {
      {
        int_T i1;
        int32_T *dw_QuadratureModes = &q_hover_DW.HILInitialize_QuadratureModes
          [0];
        for (i1=0; i1 < 8; i1++) {
          dw_QuadratureModes[i1] = q_hover_P.HILInitialize_EIQuadrature;
        }
      }

      result = hil_set_encoder_quadrature_mode(q_hover_DW.HILInitialize_Card,
        q_hover_P.HILInitialize_EIChannels, 8U, (t_encoder_quadrature_mode *)
        &q_hover_DW.HILInitialize_QuadratureModes[0]);
      if (result < 0) {
        msg_get_error_messageA(NULL, result, _rt_error_message, sizeof
          (_rt_error_message));
        rtmSetErrorStatus(q_hover_M, _rt_error_message);
        return;
      }
    }

    if ((q_hover_P.HILInitialize_EIStart && !is_switching) ||
        (q_hover_P.HILInitialize_EIEnter && is_switching)) {
      {
        int_T i1;
        int32_T *dw_InitialEICounts = &q_hover_DW.HILInitialize_InitialEICounts
          [0];
        for (i1=0; i1 < 8; i1++) {
          dw_InitialEICounts[i1] = q_hover_P.HILInitialize_EIInitial;
        }
      }

      result = hil_set_encoder_counts(q_hover_DW.HILInitialize_Card,
        q_hover_P.HILInitialize_EIChannels, 8U,
        &q_hover_DW.HILInitialize_InitialEICounts[0]);
      if (result < 0) {
        msg_get_error_messageA(NULL, result, _rt_error_message, sizeof
          (_rt_error_message));
        rtmSetErrorStatus(q_hover_M, _rt_error_message);
        return;
      }
    }

    if ((q_hover_P.HILInitialize_POPStart && !is_switching) ||
        (q_hover_P.HILInitialize_POPEnter && is_switching)) {
      uint32_T num_duty_cycle_modes = 0;
      uint32_T num_frequency_modes = 0;

      {
        int_T i1;
        int32_T *dw_POModeValues = &q_hover_DW.HILInitialize_POModeValues[0];
        for (i1=0; i1 < 8; i1++) {
          dw_POModeValues[i1] = q_hover_P.HILInitialize_POModes;
        }
      }

      result = hil_set_pwm_mode(q_hover_DW.HILInitialize_Card,
        q_hover_P.HILInitialize_POChannels, 8U, (t_pwm_mode *)
        &q_hover_DW.HILInitialize_POModeValues[0]);
      if (result < 0) {
        msg_get_error_messageA(NULL, result, _rt_error_message, sizeof
          (_rt_error_message));
        rtmSetErrorStatus(q_hover_M, _rt_error_message);
        return;
      }

      {
        int_T i1;
        const uint32_T *p_HILInitialize_POChannels =
          q_hover_P.HILInitialize_POChannels;
        int32_T *dw_POModeValues = &q_hover_DW.HILInitialize_POModeValues[0];
        for (i1=0; i1 < 8; i1++) {
          if (dw_POModeValues[i1] == PWM_DUTY_CYCLE_MODE || dw_POModeValues[i1] ==
              PWM_ONE_SHOT_MODE || dw_POModeValues[i1] == PWM_TIME_MODE ||
              dw_POModeValues[i1] == PWM_RAW_MODE) {
            q_hover_DW.HILInitialize_POSortedChans[num_duty_cycle_modes] =
              (p_HILInitialize_POChannels[i1]);
            q_hover_DW.HILInitialize_POSortedFreqs[num_duty_cycle_modes] =
              q_hover_P.HILInitialize_POFrequency;
            num_duty_cycle_modes++;
          } else {
            q_hover_DW.HILInitialize_POSortedChans[7U - num_frequency_modes] =
              (p_HILInitialize_POChannels[i1]);
            q_hover_DW.HILInitialize_POSortedFreqs[7U - num_frequency_modes] =
              q_hover_P.HILInitialize_POFrequency;
            num_frequency_modes++;
          }
        }
      }

      if (num_duty_cycle_modes > 0) {
        result = hil_set_pwm_frequency(q_hover_DW.HILInitialize_Card,
          &q_hover_DW.HILInitialize_POSortedChans[0], num_duty_cycle_modes,
          &q_hover_DW.HILInitialize_POSortedFreqs[0]);
        if (result < 0) {
          msg_get_error_messageA(NULL, result, _rt_error_message, sizeof
            (_rt_error_message));
          rtmSetErrorStatus(q_hover_M, _rt_error_message);
          return;
        }
      }

      if (num_frequency_modes > 0) {
        result = hil_set_pwm_duty_cycle(q_hover_DW.HILInitialize_Card,
          &q_hover_DW.HILInitialize_POSortedChans[num_duty_cycle_modes],
          num_frequency_modes,
          &q_hover_DW.HILInitialize_POSortedFreqs[num_duty_cycle_modes]);
        if (result < 0) {
          msg_get_error_messageA(NULL, result, _rt_error_message, sizeof
            (_rt_error_message));
          rtmSetErrorStatus(q_hover_M, _rt_error_message);
          return;
        }
      }

      {
        int_T i1;
        int32_T *dw_POModeValues = &q_hover_DW.HILInitialize_POModeValues[0];
        for (i1=0; i1 < 8; i1++) {
          dw_POModeValues[i1] = q_hover_P.HILInitialize_POConfiguration;
        }
      }

      {
        int_T i1;
        int32_T *dw_POAlignValues = &q_hover_DW.HILInitialize_POAlignValues[0];
        for (i1=0; i1 < 8; i1++) {
          dw_POAlignValues[i1] = q_hover_P.HILInitialize_POAlignment;
        }
      }

      {
        int_T i1;
        int32_T *dw_POPolarityVals = &q_hover_DW.HILInitialize_POPolarityVals[0];
        for (i1=0; i1 < 8; i1++) {
          dw_POPolarityVals[i1] = q_hover_P.HILInitialize_POPolarity;
        }
      }

      result = hil_set_pwm_configuration(q_hover_DW.HILInitialize_Card,
        q_hover_P.HILInitialize_POChannels, 8U,
        (t_pwm_configuration *) &q_hover_DW.HILInitialize_POModeValues[0],
        (t_pwm_alignment *) &q_hover_DW.HILInitialize_POAlignValues[0],
        (t_pwm_polarity *) &q_hover_DW.HILInitialize_POPolarityVals[0]);
      if (result < 0) {
        msg_get_error_messageA(NULL, result, _rt_error_message, sizeof
          (_rt_error_message));
        rtmSetErrorStatus(q_hover_M, _rt_error_message);
        return;
      }

      {
        int_T i1;
        real_T *dw_POSortedFreqs = &q_hover_DW.HILInitialize_POSortedFreqs[0];
        for (i1=0; i1 < 8; i1++) {
          dw_POSortedFreqs[i1] = q_hover_P.HILInitialize_POLeading;
        }
      }

      {
        int_T i1;
        real_T *dw_POValues = &q_hover_DW.HILInitialize_POValues[0];
        for (i1=0; i1 < 8; i1++) {
          dw_POValues[i1] = q_hover_P.HILInitialize_POTrailing;
        }
      }

      result = hil_set_pwm_deadband(q_hover_DW.HILInitialize_Card,
        q_hover_P.HILInitialize_POChannels, 8U,
        &q_hover_DW.HILInitialize_POSortedFreqs[0],
        &q_hover_DW.HILInitialize_POValues[0]);
      if (result < 0) {
        msg_get_error_messageA(NULL, result, _rt_error_message, sizeof
          (_rt_error_message));
        rtmSetErrorStatus(q_hover_M, _rt_error_message);
        return;
      }
    }

    if ((q_hover_P.HILInitialize_POStart && !is_switching) ||
        (q_hover_P.HILInitialize_POEnter && is_switching)) {
      {
        int_T i1;
        real_T *dw_POValues = &q_hover_DW.HILInitialize_POValues[0];
        for (i1=0; i1 < 8; i1++) {
          dw_POValues[i1] = q_hover_P.HILInitialize_POInitial;
        }
      }

      result = hil_write_pwm(q_hover_DW.HILInitialize_Card,
        q_hover_P.HILInitialize_POChannels, 8U,
        &q_hover_DW.HILInitialize_POValues[0]);
      if (result < 0) {
        msg_get_error_messageA(NULL, result, _rt_error_message, sizeof
          (_rt_error_message));
        rtmSetErrorStatus(q_hover_M, _rt_error_message);
        return;
      }
    }

    if (q_hover_P.HILInitialize_POReset) {
      {
        int_T i1;
        real_T *dw_POValues = &q_hover_DW.HILInitialize_POValues[0];
        for (i1=0; i1 < 8; i1++) {
          dw_POValues[i1] = q_hover_P.HILInitialize_POWatchdog;
        }
      }

      result = hil_watchdog_set_pwm_expiration_state
        (q_hover_DW.HILInitialize_Card, q_hover_P.HILInitialize_POChannels, 8U,
         &q_hover_DW.HILInitialize_POValues[0]);
      if (result < 0) {
        msg_get_error_messageA(NULL, result, _rt_error_message, sizeof
          (_rt_error_message));
        rtmSetErrorStatus(q_hover_M, _rt_error_message);
        return;
      }
    }
  }

  /* Start for S-Function (hil_read_encoder_timebase_block): '<S1>/HIL Read Encoder Timebase' */

  /* S-Function Block: q_hover/3-DOF Hover/HIL Read Encoder Timebase (hil_read_encoder_timebase_block) */
  {
    t_error result;
    result = hil_task_create_encoder_reader(q_hover_DW.HILInitialize_Card,
      q_hover_P.HILReadEncoderTimebase_SamplesI,
      q_hover_P.HILReadEncoderTimebase_Channels, 3,
      &q_hover_DW.HILReadEncoderTimebase_Task);
    if (result >= 0) {
      result = hil_task_set_buffer_overflow_mode
        (q_hover_DW.HILReadEncoderTimebase_Task, (t_buffer_overflow_mode)
         (q_hover_P.HILReadEncoderTimebase_Overflow - 1));
    }

    if (result < 0) {
      msg_get_error_messageA(NULL, result, _rt_error_message, sizeof
        (_rt_error_message));
      rtmSetErrorStatus(q_hover_M, _rt_error_message);
    }
  }

  /* Start for RateTransition: '<S3>/Rate Transition' */
  q_hover_B.RateTransition = q_hover_P.RateTransition_InitialCondition;

  /* Start for RateTransition: '<S3>/Rate Transition1' */
  q_hover_B.RateTransition1 = q_hover_P.RateTransition1_InitialConditio;

  /* Start for RateTransition: '<S3>/Rate Transition2' */
  q_hover_B.RateTransition2 = q_hover_P.RateTransition2_InitialConditio;

  /* Start for S-Function (game_controller_block): '<S3>/Game Controller' */

  /* S-Function Block: q_hover/Desired Position from Joystick/Game Controller (game_controller_block) */
  {
    if (q_hover_P.GameController_Enabled) {
      t_double deadzone[6];
      t_double saturation[6];
      t_int index;
      t_error result;
      for (index = 0; index < 6; index++) {
        deadzone[index] = -1;
      }

      for (index = 0; index < 6; index++) {
        saturation[index] = -1;
      }

      result = game_controller_open(q_hover_P.GameController_ControllerNumber,
        q_hover_P.GameController_BufferSize, deadzone, saturation,
        q_hover_P.GameController_AutoCenter, 0, 1.0,
        &q_hover_DW.GameController_Controller);
      if (result < 0) {
        msg_get_error_messageA(NULL, result, _rt_error_message, sizeof
          (_rt_error_message));
        rtmSetErrorStatus(q_hover_M, _rt_error_message);
      }
    }
  }

  /* InitializeConditions for TransferFcn: '<S1>/Derivative Filter: Pitch' */
  q_hover_X.DerivativeFilterPitch_CSTATE[0] = 0.0;

  /* InitializeConditions for TransferFcn: '<S1>/Derivative Filter: Roll' */
  q_hover_X.DerivativeFilterRoll_CSTATE[0] = 0.0;

  /* InitializeConditions for TransferFcn: '<S1>/Derivative Filter: Yaw' */
  q_hover_X.DerivativeFilterYaw_CSTATE[0] = 0.0;

  /* InitializeConditions for TransferFcn: '<S1>/Derivative Filter: Pitch' */
  q_hover_X.DerivativeFilterPitch_CSTATE[1] = 0.0;

  /* InitializeConditions for TransferFcn: '<S1>/Derivative Filter: Roll' */
  q_hover_X.DerivativeFilterRoll_CSTATE[1] = 0.0;

  /* InitializeConditions for TransferFcn: '<S1>/Derivative Filter: Yaw' */
  q_hover_X.DerivativeFilterYaw_CSTATE[1] = 0.0;

  /* InitializeConditions for RateLimiter: '<S2>/Limit Rate of Desired Angle' */
  q_hover_DW.LastMajorTime = (rtInf);

  /* InitializeConditions for Integrator: '<S3>/Des Position:  Roll (deg)1' */
  q_hover_X.DesPositionRolldeg1_CSTATE = q_hover_P.DesPositionRolldeg1_IC;

  /* InitializeConditions for Integrator: '<S3>/Des Position:  Pitch (deg)' */
  q_hover_X.DesPositionPitchdeg_CSTATE = q_hover_P.DesPositionPitchdeg_IC;

  /* InitializeConditions for Integrator: '<S3>/Des Position:  Roll (deg)' */
  q_hover_X.DesPositionRolldeg_CSTATE = q_hover_P.DesPositionRolldeg_IC;

  /* InitializeConditions for RateLimiter: '<S3>/Limit Rate of Desired Angle' */
  q_hover_DW.LastMajorTime_k = (rtInf);

  /* InitializeConditions for RateTransition: '<S3>/Rate Transition' */
  q_hover_DW.RateTransition_Buffer0 = q_hover_P.RateTransition_InitialCondition;

  /* InitializeConditions for RateTransition: '<S3>/Rate Transition1' */
  q_hover_DW.RateTransition1_Buffer0 = q_hover_P.RateTransition1_InitialConditio;

  /* InitializeConditions for RateTransition: '<S3>/Rate Transition2' */
  q_hover_DW.RateTransition2_Buffer0 = q_hover_P.RateTransition2_InitialConditio;
}

/* Model terminate function */
void q_hover_terminate(void)
{
  /* Terminate for S-Function (hil_initialize_block): '<S1>/HIL Initialize' */

  /* S-Function Block: q_hover/3-DOF Hover/HIL Initialize (hil_initialize_block) */
  {
    t_boolean is_switching;
    t_int result;
    t_uint32 num_final_analog_outputs = 0;
    t_uint32 num_final_digital_outputs = 0;
    t_uint32 num_final_pwm_outputs = 0;
    hil_task_stop_all(q_hover_DW.HILInitialize_Card);
    hil_monitor_stop_all(q_hover_DW.HILInitialize_Card);
    is_switching = false;
    if ((q_hover_P.HILInitialize_AOTerminate && !is_switching) ||
        (q_hover_P.HILInitialize_AOExit && is_switching)) {
      {
        int_T i1;
        real_T *dw_AOVoltages = &q_hover_DW.HILInitialize_AOVoltages[0];
        for (i1=0; i1 < 8; i1++) {
          dw_AOVoltages[i1] = q_hover_P.HILInitialize_AOFinal;
        }
      }

      num_final_analog_outputs = 8U;
    } else {
      num_final_analog_outputs = 0;
    }

    if ((q_hover_P.HILInitialize_DOTerminate && !is_switching) ||
        (q_hover_P.HILInitialize_DOExit && is_switching)) {
      q_hover_DW.HILInitialize_DOBits[0] = q_hover_P.HILInitialize_DOFinal;
      q_hover_DW.HILInitialize_DOBits[1] = q_hover_P.HILInitialize_DOFinal;
      q_hover_DW.HILInitialize_DOBits[2] = q_hover_P.HILInitialize_DOFinal;
      q_hover_DW.HILInitialize_DOBits[3] = q_hover_P.HILInitialize_DOFinal;
      num_final_digital_outputs = 4U;
    } else {
      num_final_digital_outputs = 0;
    }

    if ((q_hover_P.HILInitialize_POTerminate && !is_switching) ||
        (q_hover_P.HILInitialize_POExit && is_switching)) {
      {
        int_T i1;
        real_T *dw_POValues = &q_hover_DW.HILInitialize_POValues[0];
        for (i1=0; i1 < 8; i1++) {
          dw_POValues[i1] = q_hover_P.HILInitialize_POFinal;
        }
      }

      num_final_pwm_outputs = 8U;
    } else {
      num_final_pwm_outputs = 0;
    }

    if (0
        || num_final_analog_outputs > 0
        || num_final_pwm_outputs > 0
        || num_final_digital_outputs > 0
        ) {
      /* Attempt to write the final outputs atomically (due to firmware issue in old Q2-USB). Otherwise write channels individually */
      result = hil_write(q_hover_DW.HILInitialize_Card
                         , q_hover_P.HILInitialize_AOChannels,
                         num_final_analog_outputs
                         , q_hover_P.HILInitialize_POChannels,
                         num_final_pwm_outputs
                         , q_hover_P.HILInitialize_DOChannels,
                         num_final_digital_outputs
                         , NULL, 0
                         , &q_hover_DW.HILInitialize_AOVoltages[0]
                         , &q_hover_DW.HILInitialize_POValues[0]
                         , (t_boolean *) &q_hover_DW.HILInitialize_DOBits[0]
                         , NULL
                         );
      if (result == -QERR_HIL_WRITE_NOT_SUPPORTED) {
        t_error local_result;
        result = 0;

        /* The hil_write operation is not supported by this card. Write final outputs for each channel type */
        if (num_final_analog_outputs > 0) {
          local_result = hil_write_analog(q_hover_DW.HILInitialize_Card,
            q_hover_P.HILInitialize_AOChannels, num_final_analog_outputs,
            &q_hover_DW.HILInitialize_AOVoltages[0]);
          if (local_result < 0) {
            result = local_result;
          }
        }

        if (num_final_pwm_outputs > 0) {
          local_result = hil_write_pwm(q_hover_DW.HILInitialize_Card,
            q_hover_P.HILInitialize_POChannels, num_final_pwm_outputs,
            &q_hover_DW.HILInitialize_POValues[0]);
          if (local_result < 0) {
            result = local_result;
          }
        }

        if (num_final_digital_outputs > 0) {
          local_result = hil_write_digital(q_hover_DW.HILInitialize_Card,
            q_hover_P.HILInitialize_DOChannels, num_final_digital_outputs,
            (t_boolean *) &q_hover_DW.HILInitialize_DOBits[0]);
          if (local_result < 0) {
            result = local_result;
          }
        }

        if (result < 0) {
          msg_get_error_messageA(NULL, result, _rt_error_message, sizeof
            (_rt_error_message));
          rtmSetErrorStatus(q_hover_M, _rt_error_message);
        }
      }
    }

    hil_task_delete_all(q_hover_DW.HILInitialize_Card);
    hil_monitor_delete_all(q_hover_DW.HILInitialize_Card);
    hil_close(q_hover_DW.HILInitialize_Card);
    q_hover_DW.HILInitialize_Card = NULL;
  }

  /* Terminate for S-Function (game_controller_block): '<S3>/Game Controller' */

  /* S-Function Block: q_hover/Desired Position from Joystick/Game Controller (game_controller_block) */
  {
    if (q_hover_P.GameController_Enabled) {
      game_controller_close(q_hover_DW.GameController_Controller);
      q_hover_DW.GameController_Controller = NULL;
    }
  }
}

/*========================================================================*
 * Start of Classic call interface                                        *
 *========================================================================*/

/* Solver interface called by GRT_Main */
#ifndef USE_GENERATED_SOLVER

void rt_ODECreateIntegrationData(RTWSolverInfo *si)
{
  UNUSED_PARAMETER(si);
  return;
}                                      /* do nothing */

void rt_ODEDestroyIntegrationData(RTWSolverInfo *si)
{
  UNUSED_PARAMETER(si);
  return;
}                                      /* do nothing */

void rt_ODEUpdateContinuousStates(RTWSolverInfo *si)
{
  UNUSED_PARAMETER(si);
  return;
}                                      /* do nothing */

#endif

void MdlOutputs(int_T tid)
{
  if (tid == 1)
    tid = 0;
  q_hover_output(tid);
}

void MdlUpdate(int_T tid)
{
  if (tid == 1)
    tid = 0;
  q_hover_update(tid);
}

void MdlInitializeSizes(void)
{
}

void MdlInitializeSampleTimes(void)
{
}

void MdlInitialize(void)
{
}

void MdlStart(void)
{
  q_hover_initialize();
}

void MdlTerminate(void)
{
  q_hover_terminate();
}

/* Registration function */
RT_MODEL_q_hover_T *q_hover(void)
{
  /* Registration code */

  /* initialize non-finites */
  rt_InitInfAndNaN(sizeof(real_T));

  /* initialize real-time model */
  (void) memset((void *)q_hover_M, 0,
                sizeof(RT_MODEL_q_hover_T));

  {
    /* Setup solver object */
    rtsiSetSimTimeStepPtr(&q_hover_M->solverInfo, &q_hover_M->Timing.simTimeStep);
    rtsiSetTPtr(&q_hover_M->solverInfo, &rtmGetTPtr(q_hover_M));
    rtsiSetStepSizePtr(&q_hover_M->solverInfo, &q_hover_M->Timing.stepSize0);
    rtsiSetdXPtr(&q_hover_M->solverInfo, &q_hover_M->derivs);
    rtsiSetContStatesPtr(&q_hover_M->solverInfo, (real_T **)
                         &q_hover_M->contStates);
    rtsiSetNumContStatesPtr(&q_hover_M->solverInfo,
      &q_hover_M->Sizes.numContStates);
    rtsiSetNumPeriodicContStatesPtr(&q_hover_M->solverInfo,
      &q_hover_M->Sizes.numPeriodicContStates);
    rtsiSetPeriodicContStateIndicesPtr(&q_hover_M->solverInfo,
      &q_hover_M->periodicContStateIndices);
    rtsiSetPeriodicContStateRangesPtr(&q_hover_M->solverInfo,
      &q_hover_M->periodicContStateRanges);
    rtsiSetContStateDisabledPtr(&q_hover_M->solverInfo, (boolean_T**)
      &q_hover_M->contStateDisabled);
    rtsiSetErrorStatusPtr(&q_hover_M->solverInfo, (&rtmGetErrorStatus(q_hover_M)));
    rtsiSetRTModelPtr(&q_hover_M->solverInfo, q_hover_M);
  }

  rtsiSetSimTimeStep(&q_hover_M->solverInfo, MAJOR_TIME_STEP);
  rtsiSetIsMinorTimeStepWithModeChange(&q_hover_M->solverInfo, false);
  rtsiSetIsContModeFrozen(&q_hover_M->solverInfo, false);
  q_hover_M->intgData.f[0] = q_hover_M->odeF[0];
  q_hover_M->contStates = ((real_T *) &q_hover_X);
  q_hover_M->contStateDisabled = ((boolean_T *) &q_hover_XDis);
  q_hover_M->Timing.tStart = (0.0);
  rtsiSetSolverData(&q_hover_M->solverInfo, (void *)&q_hover_M->intgData);
  rtsiSetSolverName(&q_hover_M->solverInfo,"ode1");

  /* Initialize timing info */
  {
    int_T *mdlTsMap = q_hover_M->Timing.sampleTimeTaskIDArray;
    mdlTsMap[0] = 0;
    mdlTsMap[1] = 1;
    mdlTsMap[2] = 2;

    /* polyspace +2 MISRA2012:D4.1 [Justified:Low] "q_hover_M points to
       static memory which is guaranteed to be non-NULL" */
    q_hover_M->Timing.sampleTimeTaskIDPtr = (&mdlTsMap[0]);
    q_hover_M->Timing.sampleTimes = (&q_hover_M->Timing.sampleTimesArray[0]);
    q_hover_M->Timing.offsetTimes = (&q_hover_M->Timing.offsetTimesArray[0]);

    /* task periods */
    q_hover_M->Timing.sampleTimes[0] = (0.0);
    q_hover_M->Timing.sampleTimes[1] = (0.002);
    q_hover_M->Timing.sampleTimes[2] = (0.01);

    /* task offsets */
    q_hover_M->Timing.offsetTimes[0] = (0.0);
    q_hover_M->Timing.offsetTimes[1] = (0.0);
    q_hover_M->Timing.offsetTimes[2] = (0.0);
  }

  rtmSetTPtr(q_hover_M, &q_hover_M->Timing.tArray[0]);

  {
    int_T *mdlSampleHits = q_hover_M->Timing.sampleHitArray;
    int_T *mdlPerTaskSampleHits = q_hover_M->Timing.perTaskSampleHitsArray;
    q_hover_M->Timing.perTaskSampleHits = (&mdlPerTaskSampleHits[0]);
    mdlSampleHits[0] = 1;
    q_hover_M->Timing.sampleHits = (&mdlSampleHits[0]);
  }

  rtmSetTFinal(q_hover_M, -1);
  q_hover_M->Timing.stepSize0 = 0.002;
  q_hover_M->Timing.stepSize1 = 0.002;
  q_hover_M->Timing.stepSize2 = 0.01;

  /* External mode info */
  q_hover_M->Sizes.checksums[0] = (1808776896U);
  q_hover_M->Sizes.checksums[1] = (4252722U);
  q_hover_M->Sizes.checksums[2] = (49714659U);
  q_hover_M->Sizes.checksums[3] = (1820460352U);

  {
    static const sysRanDType rtAlwaysEnabled = SUBSYS_RAN_BC_ENABLE;
    static RTWExtModeInfo rt_ExtModeInfo;
    static const sysRanDType *systemRan[3];
    q_hover_M->extModeInfo = (&rt_ExtModeInfo);
    rteiSetSubSystemActiveVectorAddresses(&rt_ExtModeInfo, systemRan);
    systemRan[0] = &rtAlwaysEnabled;
    systemRan[1] = &rtAlwaysEnabled;
    systemRan[2] = &rtAlwaysEnabled;
    rteiSetModelMappingInfoPtr(q_hover_M->extModeInfo,
      &q_hover_M->SpecialInfo.mappingInfo);
    rteiSetChecksumsPtr(q_hover_M->extModeInfo, q_hover_M->Sizes.checksums);
    rteiSetTPtr(q_hover_M->extModeInfo, rtmGetTPtr(q_hover_M));
  }

  q_hover_M->solverInfoPtr = (&q_hover_M->solverInfo);
  q_hover_M->Timing.stepSize = (0.002);
  rtsiSetFixedStepSize(&q_hover_M->solverInfo, 0.002);
  rtsiSetSolverMode(&q_hover_M->solverInfo, SOLVER_MODE_MULTITASKING);

  /* block I/O */
  q_hover_M->blockIO = ((void *) &q_hover_B);

  {
    int32_T i;
    for (i = 0; i < 6; i++) {
      q_hover_B.Gain[i] = 0.0;
    }

    for (i = 0; i < 6; i++) {
      q_hover_B.Gain_p[i] = 0.0;
    }

    q_hover_B.pitch = 0.0;
    q_hover_B.roll = 0.0;
    q_hover_B.yaw = 0.0;
    q_hover_B.ConverttoVector[0] = 0.0;
    q_hover_B.ConverttoVector[1] = 0.0;
    q_hover_B.ConverttoVector[2] = 0.0;
    q_hover_B.ConverttoVector[3] = 0.0;
    q_hover_B.LimitRateofDesiredAngle[0] = 0.0;
    q_hover_B.LimitRateofDesiredAngle[1] = 0.0;
    q_hover_B.LimitRateofDesiredAngle[2] = 0.0;
    q_hover_B.LimitRateofDesiredAngle_f[0] = 0.0;
    q_hover_B.LimitRateofDesiredAngle_f[1] = 0.0;
    q_hover_B.LimitRateofDesiredAngle_f[2] = 0.0;
    q_hover_B.CableGainPreCompensation[0] = 0.0;
    q_hover_B.CableGainPreCompensation[1] = 0.0;
    q_hover_B.CableGainPreCompensation[2] = 0.0;
    q_hover_B.CableGainPreCompensation[3] = 0.0;
    q_hover_B.CableGain[0] = 0.0;
    q_hover_B.CableGain[1] = 0.0;
    q_hover_B.CableGain[2] = 0.0;
    q_hover_B.CableGain[3] = 0.0;
    q_hover_B.RateTransition = 0.0;
    q_hover_B.RateTransition1 = 0.0;
    q_hover_B.RateTransition2 = 0.0;
    q_hover_B.GameController_o7 = 0.0;
    q_hover_B.GameController_o8 = 0.0;
  }

  /* parameters */
  q_hover_M->defaultParam = ((real_T *)&q_hover_P);

  /* states (continuous) */
  {
    real_T *x = (real_T *) &q_hover_X;
    q_hover_M->contStates = (x);
    (void) memset((void *)&q_hover_X, 0,
                  sizeof(X_q_hover_T));
  }

  /* disabled states */
  {
    boolean_T *xdis = (boolean_T *) &q_hover_XDis;
    q_hover_M->contStateDisabled = (xdis);
    (void) memset((void *)&q_hover_XDis, 0,
                  sizeof(XDis_q_hover_T));
  }

  /* states (dwork) */
  q_hover_M->dwork = ((void *) &q_hover_DW);
  (void) memset((void *)&q_hover_DW, 0,
                sizeof(DW_q_hover_T));

  {
    int32_T i;
    for (i = 0; i < 8; i++) {
      q_hover_DW.HILInitialize_AIMinimums[i] = 0.0;
    }
  }

  {
    int32_T i;
    for (i = 0; i < 8; i++) {
      q_hover_DW.HILInitialize_AIMaximums[i] = 0.0;
    }
  }

  {
    int32_T i;
    for (i = 0; i < 8; i++) {
      q_hover_DW.HILInitialize_AOMinimums[i] = 0.0;
    }
  }

  {
    int32_T i;
    for (i = 0; i < 8; i++) {
      q_hover_DW.HILInitialize_AOMaximums[i] = 0.0;
    }
  }

  {
    int32_T i;
    for (i = 0; i < 8; i++) {
      q_hover_DW.HILInitialize_AOVoltages[i] = 0.0;
    }
  }

  {
    int32_T i;
    for (i = 0; i < 8; i++) {
      q_hover_DW.HILInitialize_FilterFrequency[i] = 0.0;
    }
  }

  {
    int32_T i;
    for (i = 0; i < 8; i++) {
      q_hover_DW.HILInitialize_POSortedFreqs[i] = 0.0;
    }
  }

  {
    int32_T i;
    for (i = 0; i < 8; i++) {
      q_hover_DW.HILInitialize_POValues[i] = 0.0;
    }
  }

  q_hover_DW.PrevY[0] = 0.0;
  q_hover_DW.PrevY[1] = 0.0;
  q_hover_DW.PrevY[2] = 0.0;
  q_hover_DW.LastMajorTime = 0.0;
  q_hover_DW.PrevY_k[0] = 0.0;
  q_hover_DW.PrevY_k[1] = 0.0;
  q_hover_DW.PrevY_k[2] = 0.0;
  q_hover_DW.LastMajorTime_k = 0.0;
  q_hover_DW.RateTransition_Buffer0 = 0.0;
  q_hover_DW.RateTransition1_Buffer0 = 0.0;
  q_hover_DW.RateTransition2_Buffer0 = 0.0;

  /* data type transition information */
  {
    static DataTypeTransInfo dtInfo;
    (void) memset((char_T *) &dtInfo, 0,
                  sizeof(dtInfo));
    q_hover_M->SpecialInfo.mappingInfo = (&dtInfo);
    dtInfo.numDataTypes = 22;
    dtInfo.dataTypeSizes = &rtDataTypeSizes[0];
    dtInfo.dataTypeNames = &rtDataTypeNames[0];

    /* Block I/O transition table */
    dtInfo.BTransTable = &rtBTransTable;

    /* Parameters transition table */
    dtInfo.PTransTable = &rtPTransTable;
  }

  /* Initialize Sizes */
  q_hover_M->Sizes.numContStates = (9);/* Number of continuous states */
  q_hover_M->Sizes.numPeriodicContStates = (0);
                                      /* Number of periodic continuous states */
  q_hover_M->Sizes.numY = (0);         /* Number of model outputs */
  q_hover_M->Sizes.numU = (0);         /* Number of model inputs */
  q_hover_M->Sizes.sysDirFeedThru = (0);/* The model is not direct feedthrough */
  q_hover_M->Sizes.numSampTimes = (3); /* Number of sample times */
  q_hover_M->Sizes.numBlocks = (69);   /* Number of blocks */
  q_hover_M->Sizes.numBlockIO = (19);  /* Number of block outputs */
  q_hover_M->Sizes.numBlockPrms = (233);/* Sum of parameter "widths" */
  return q_hover_M;
}

/*========================================================================*
 * End of Classic call interface                                          *
 *========================================================================*/
