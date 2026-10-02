/*
 * q_hover_dt.h
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

#include "ext_types.h"

/* data type size table */
static uint_T rtDataTypeSizes[] = {
  sizeof(real_T),
  sizeof(real32_T),
  sizeof(int8_T),
  sizeof(uint8_T),
  sizeof(int16_T),
  sizeof(uint16_T),
  sizeof(int32_T),
  sizeof(uint32_T),
  sizeof(boolean_T),
  sizeof(fcn_call_T),
  sizeof(int_T),
  sizeof(pointer_T),
  sizeof(action_T),
  2*sizeof(uint32_T),
  sizeof(int32_T),
  sizeof(t_game_controller),
  sizeof(t_card),
  sizeof(t_task),
  sizeof(uint_T),
  sizeof(char_T),
  sizeof(uchar_T),
  sizeof(time_T)
};

/* data type name table */
static const char_T * rtDataTypeNames[] = {
  "real_T",
  "real32_T",
  "int8_T",
  "uint8_T",
  "int16_T",
  "uint16_T",
  "int32_T",
  "uint32_T",
  "boolean_T",
  "fcn_call_T",
  "int_T",
  "pointer_T",
  "action_T",
  "timer_uint32_pair_T",
  "physical_connection",
  "t_game_controller",
  "t_card",
  "t_task",
  "uint_T",
  "char_T",
  "uchar_T",
  "time_T"
};

/* data type transitions for block I/O structure */
static DataTypeTransition rtBTransitions[] = {
  { (char_T *)(&q_hover_B.pitch), 0, 0, 38 }
  ,

  { (char_T *)(&q_hover_DW.HILInitialize_AIMinimums[0]), 0, 0, 75 },

  { (char_T *)(&q_hover_DW.GameController_Controller), 15, 0, 1 },

  { (char_T *)(&q_hover_DW.HILInitialize_Card), 16, 0, 1 },

  { (char_T *)(&q_hover_DW.HILReadEncoderTimebase_Task), 17, 0, 1 },

  { (char_T *)(&q_hover_DW.HILWriteAnalog_PWORK), 11, 0, 11 },

  { (char_T *)(&q_hover_DW.HILInitialize_ClockModes[0]), 6, 0, 50 },

  { (char_T *)(&q_hover_DW.HILInitialize_POSortedChans[0]), 7, 0, 8 },

  { (char_T *)(&q_hover_DW.HILInitialize_DOBits[0]), 8, 0, 10 }
};

/* data type transition table for block I/O structure */
static DataTypeTransitionTable rtBTransTable = {
  9U,
  rtBTransitions
};

/* data type transitions for Parameters structure */
static DataTypeTransition rtPTransitions[] = {
  { (char_T *)(&q_hover_P.CMD_RATE_LIMIT), 0, 0, 37 },

  { (char_T *)(&q_hover_P.HILWriteAnalog_channels[0]), 7, 0, 4 },

  { (char_T *)(&q_hover_P.ConverttoStatewith6Elements_Gai[0]), 0, 0, 98 },

  { (char_T *)(&q_hover_P.HILInitialize_CKChannels[0]), 6, 0, 10 },

  { (char_T *)(&q_hover_P.HILInitialize_AIChannels[0]), 7, 0, 41 },

  { (char_T *)(&q_hover_P.GameController_BufferSize), 5, 0, 1 },

  { (char_T *)(&q_hover_P.HILInitialize_Active), 8, 0, 39 },

  { (char_T *)(&q_hover_P.HILReadEncoderTimebase_Overflow), 3, 0, 3 }
};

/* data type transition table for Parameters structure */
static DataTypeTransitionTable rtPTransTable = {
  8U,
  rtPTransitions
};

/* [EOF] q_hover_dt.h */
