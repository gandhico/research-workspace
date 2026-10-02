    function targMap = targDataMap(),

    ;%***********************
    ;% Create Parameter Map *
    ;%***********************
    
        nTotData      = 0; %add to this count as we go
        nTotSects     = 8;
        sectIdxOffset = 0;

        ;%
        ;% Define dummy sections & preallocate arrays
        ;%
        dumSection.nData = -1;
        dumSection.data  = [];

        dumData.logicalSrcIdx = -1;
        dumData.dtTransOffset = -1;

        ;%
        ;% Init/prealloc paramMap
        ;%
        paramMap.nSections           = nTotSects;
        paramMap.sectIdxOffset       = sectIdxOffset;
            paramMap.sections(nTotSects) = dumSection; %prealloc
        paramMap.nTotData            = -1;

        ;%
        ;% Auto data (q_hover_P)
        ;%
            section.nData     = 14;
            section.data(14)  = dumData; %prealloc

                    ;% q_hover_P.CMD_RATE_LIMIT
                    section.data(1).logicalSrcIdx = 0;
                    section.data(1).dtTransOffset = 0;

                    ;% q_hover_P.INT_JOYSTICK_SAT_LOWER
                    section.data(2).logicalSrcIdx = 1;
                    section.data(2).dtTransOffset = 1;

                    ;% q_hover_P.INT_JOYSTICK_SAT_UPPER
                    section.data(3).logicalSrcIdx = 2;
                    section.data(3).dtTransOffset = 2;

                    ;% q_hover_P.JOYSTICK_X_DZ
                    section.data(4).logicalSrcIdx = 3;
                    section.data(4).dtTransOffset = 3;

                    ;% q_hover_P.JOYSTICK_Y_DZ
                    section.data(5).logicalSrcIdx = 4;
                    section.data(5).dtTransOffset = 4;

                    ;% q_hover_P.K
                    section.data(6).logicalSrcIdx = 5;
                    section.data(6).dtTransOffset = 5;

                    ;% q_hover_P.K_AMP
                    section.data(7).logicalSrcIdx = 6;
                    section.data(7).dtTransOffset = 29;

                    ;% q_hover_P.K_EC_P
                    section.data(8).logicalSrcIdx = 7;
                    section.data(8).dtTransOffset = 30;

                    ;% q_hover_P.K_EC_R
                    section.data(9).logicalSrcIdx = 8;
                    section.data(9).dtTransOffset = 31;

                    ;% q_hover_P.K_EC_Y
                    section.data(10).logicalSrcIdx = 9;
                    section.data(10).dtTransOffset = 32;

                    ;% q_hover_P.K_JOYSTICK_X
                    section.data(11).logicalSrcIdx = 10;
                    section.data(11).dtTransOffset = 33;

                    ;% q_hover_P.K_JOYSTICK_Y
                    section.data(12).logicalSrcIdx = 11;
                    section.data(12).dtTransOffset = 34;

                    ;% q_hover_P.VMAX_AMP
                    section.data(13).logicalSrcIdx = 12;
                    section.data(13).dtTransOffset = 35;

                    ;% q_hover_P.V_bias
                    section.data(14).logicalSrcIdx = 13;
                    section.data(14).dtTransOffset = 36;

            nTotData = nTotData + section.nData;
            paramMap.sections(1) = section;
            clear section

            section.nData     = 1;
            section.data(1)  = dumData; %prealloc

                    ;% q_hover_P.HILWriteAnalog_channels
                    section.data(1).logicalSrcIdx = 14;
                    section.data(1).dtTransOffset = 0;

            nTotData = nTotData + section.nData;
            paramMap.sections(2) = section;
            clear section

            section.nData     = 55;
            section.data(55)  = dumData; %prealloc

                    ;% q_hover_P.ConverttoStatewith6Elements_Gai
                    section.data(1).logicalSrcIdx = 15;
                    section.data(1).dtTransOffset = 0;

                    ;% q_hover_P.ConverttoStatewith6Elements_G_i
                    section.data(2).logicalSrcIdx = 16;
                    section.data(2).dtTransOffset = 18;

                    ;% q_hover_P.HILInitialize_OOTerminate
                    section.data(3).logicalSrcIdx = 17;
                    section.data(3).dtTransOffset = 36;

                    ;% q_hover_P.HILInitialize_OOExit
                    section.data(4).logicalSrcIdx = 18;
                    section.data(4).dtTransOffset = 37;

                    ;% q_hover_P.HILInitialize_OOStart
                    section.data(5).logicalSrcIdx = 19;
                    section.data(5).dtTransOffset = 38;

                    ;% q_hover_P.HILInitialize_OOEnter
                    section.data(6).logicalSrcIdx = 20;
                    section.data(6).dtTransOffset = 39;

                    ;% q_hover_P.HILInitialize_AOFinal
                    section.data(7).logicalSrcIdx = 21;
                    section.data(7).dtTransOffset = 40;

                    ;% q_hover_P.HILInitialize_POFinal
                    section.data(8).logicalSrcIdx = 22;
                    section.data(8).dtTransOffset = 41;

                    ;% q_hover_P.HILInitialize_AIHigh
                    section.data(9).logicalSrcIdx = 23;
                    section.data(9).dtTransOffset = 42;

                    ;% q_hover_P.HILInitialize_AILow
                    section.data(10).logicalSrcIdx = 24;
                    section.data(10).dtTransOffset = 43;

                    ;% q_hover_P.HILInitialize_AOHigh
                    section.data(11).logicalSrcIdx = 25;
                    section.data(11).dtTransOffset = 44;

                    ;% q_hover_P.HILInitialize_AOLow
                    section.data(12).logicalSrcIdx = 26;
                    section.data(12).dtTransOffset = 45;

                    ;% q_hover_P.HILInitialize_AOInitial
                    section.data(13).logicalSrcIdx = 27;
                    section.data(13).dtTransOffset = 46;

                    ;% q_hover_P.HILInitialize_AOWatchdog
                    section.data(14).logicalSrcIdx = 28;
                    section.data(14).dtTransOffset = 47;

                    ;% q_hover_P.HILInitialize_POFrequency
                    section.data(15).logicalSrcIdx = 29;
                    section.data(15).dtTransOffset = 48;

                    ;% q_hover_P.HILInitialize_POLeading
                    section.data(16).logicalSrcIdx = 30;
                    section.data(16).dtTransOffset = 49;

                    ;% q_hover_P.HILInitialize_POTrailing
                    section.data(17).logicalSrcIdx = 31;
                    section.data(17).dtTransOffset = 50;

                    ;% q_hover_P.HILInitialize_POInitial
                    section.data(18).logicalSrcIdx = 32;
                    section.data(18).dtTransOffset = 51;

                    ;% q_hover_P.HILInitialize_POWatchdog
                    section.data(19).logicalSrcIdx = 33;
                    section.data(19).dtTransOffset = 52;

                    ;% q_hover_P.DerivativeFilterPitch_A
                    section.data(20).logicalSrcIdx = 34;
                    section.data(20).dtTransOffset = 53;

                    ;% q_hover_P.DerivativeFilterPitch_C
                    section.data(21).logicalSrcIdx = 35;
                    section.data(21).dtTransOffset = 55;

                    ;% q_hover_P.DerivativeFilterRoll_A
                    section.data(22).logicalSrcIdx = 36;
                    section.data(22).dtTransOffset = 57;

                    ;% q_hover_P.DerivativeFilterRoll_C
                    section.data(23).logicalSrcIdx = 37;
                    section.data(23).dtTransOffset = 59;

                    ;% q_hover_P.DerivativeFilterYaw_A
                    section.data(24).logicalSrcIdx = 38;
                    section.data(24).dtTransOffset = 61;

                    ;% q_hover_P.DerivativeFilterYaw_C
                    section.data(25).logicalSrcIdx = 39;
                    section.data(25).dtTransOffset = 63;

                    ;% q_hover_P.ConverttoVector_Gain
                    section.data(26).logicalSrcIdx = 40;
                    section.data(26).dtTransOffset = 65;

                    ;% q_hover_P.SignalGeneratorYaw_Amplitude
                    section.data(27).logicalSrcIdx = 41;
                    section.data(27).dtTransOffset = 69;

                    ;% q_hover_P.SignalGeneratorYaw_Frequency
                    section.data(28).logicalSrcIdx = 42;
                    section.data(28).dtTransOffset = 70;

                    ;% q_hover_P.AmplitudeYawdeg_Gain
                    section.data(29).logicalSrcIdx = 43;
                    section.data(29).dtTransOffset = 71;

                    ;% q_hover_P.ConstantYawdeg_Value
                    section.data(30).logicalSrcIdx = 44;
                    section.data(30).dtTransOffset = 72;

                    ;% q_hover_P.Gain1_Gain
                    section.data(31).logicalSrcIdx = 45;
                    section.data(31).dtTransOffset = 73;

                    ;% q_hover_P.SignalGeneratorPitch_Amplitude
                    section.data(32).logicalSrcIdx = 46;
                    section.data(32).dtTransOffset = 74;

                    ;% q_hover_P.SignalGeneratorPitch_Frequency
                    section.data(33).logicalSrcIdx = 47;
                    section.data(33).dtTransOffset = 75;

                    ;% q_hover_P.AmplitudePitchdeg_Gain
                    section.data(34).logicalSrcIdx = 48;
                    section.data(34).dtTransOffset = 76;

                    ;% q_hover_P.ConstantPitchdeg_Value
                    section.data(35).logicalSrcIdx = 49;
                    section.data(35).dtTransOffset = 77;

                    ;% q_hover_P.Gain1_Gain_c
                    section.data(36).logicalSrcIdx = 50;
                    section.data(36).dtTransOffset = 78;

                    ;% q_hover_P.SignalGeneratorRoll_Amplitude
                    section.data(37).logicalSrcIdx = 51;
                    section.data(37).dtTransOffset = 79;

                    ;% q_hover_P.SignalGeneratorRoll_Frequency
                    section.data(38).logicalSrcIdx = 52;
                    section.data(38).dtTransOffset = 80;

                    ;% q_hover_P.AmplitudeRolldeg_Gain
                    section.data(39).logicalSrcIdx = 53;
                    section.data(39).dtTransOffset = 81;

                    ;% q_hover_P.ConstantRolldeg_Value
                    section.data(40).logicalSrcIdx = 54;
                    section.data(40).dtTransOffset = 82;

                    ;% q_hover_P.Gain1_Gain_d
                    section.data(41).logicalSrcIdx = 55;
                    section.data(41).dtTransOffset = 83;

                    ;% q_hover_P.DesPositionRolldeg1_IC
                    section.data(42).logicalSrcIdx = 56;
                    section.data(42).dtTransOffset = 84;

                    ;% q_hover_P.DesPositionPitchdeg_IC
                    section.data(43).logicalSrcIdx = 57;
                    section.data(43).dtTransOffset = 85;

                    ;% q_hover_P.DesPositionRolldeg_IC
                    section.data(44).logicalSrcIdx = 58;
                    section.data(44).dtTransOffset = 86;

                    ;% q_hover_P.Gain1_Gain_m
                    section.data(45).logicalSrcIdx = 59;
                    section.data(45).dtTransOffset = 87;

                    ;% q_hover_P.UPMVoltageLimit0toVMAX_AMP_Lowe
                    section.data(46).logicalSrcIdx = 60;
                    section.data(46).dtTransOffset = 88;

                    ;% q_hover_P.Gain_Gain
                    section.data(47).logicalSrcIdx = 61;
                    section.data(47).dtTransOffset = 89;

                    ;% q_hover_P.Gain_Gain_g
                    section.data(48).logicalSrcIdx = 62;
                    section.data(48).dtTransOffset = 90;

                    ;% q_hover_P.RateTransition_InitialCondition
                    section.data(49).logicalSrcIdx = 63;
                    section.data(49).dtTransOffset = 91;

                    ;% q_hover_P.RateTransition1_InitialConditio
                    section.data(50).logicalSrcIdx = 64;
                    section.data(50).dtTransOffset = 92;

                    ;% q_hover_P.RateTransition2_InitialConditio
                    section.data(51).logicalSrcIdx = 65;
                    section.data(51).dtTransOffset = 93;

                    ;% q_hover_P.Inverse_Gain
                    section.data(52).logicalSrcIdx = 66;
                    section.data(52).dtTransOffset = 94;

                    ;% q_hover_P.Bias_Bias
                    section.data(53).logicalSrcIdx = 67;
                    section.data(53).dtTransOffset = 95;

                    ;% q_hover_P.Constant_Value
                    section.data(54).logicalSrcIdx = 68;
                    section.data(54).dtTransOffset = 96;

                    ;% q_hover_P.CalibrationXdegsV1_Gain
                    section.data(55).logicalSrcIdx = 69;
                    section.data(55).dtTransOffset = 97;

            nTotData = nTotData + section.nData;
            paramMap.sections(3) = section;
            clear section

            section.nData     = 8;
            section.data(8)  = dumData; %prealloc

                    ;% q_hover_P.HILInitialize_CKChannels
                    section.data(1).logicalSrcIdx = 70;
                    section.data(1).dtTransOffset = 0;

                    ;% q_hover_P.HILInitialize_DOWatchdog
                    section.data(2).logicalSrcIdx = 71;
                    section.data(2).dtTransOffset = 3;

                    ;% q_hover_P.HILInitialize_EIInitial
                    section.data(3).logicalSrcIdx = 72;
                    section.data(3).dtTransOffset = 4;

                    ;% q_hover_P.HILInitialize_POModes
                    section.data(4).logicalSrcIdx = 73;
                    section.data(4).dtTransOffset = 5;

                    ;% q_hover_P.HILInitialize_POConfiguration
                    section.data(5).logicalSrcIdx = 74;
                    section.data(5).dtTransOffset = 6;

                    ;% q_hover_P.HILInitialize_POAlignment
                    section.data(6).logicalSrcIdx = 75;
                    section.data(6).dtTransOffset = 7;

                    ;% q_hover_P.HILInitialize_POPolarity
                    section.data(7).logicalSrcIdx = 76;
                    section.data(7).dtTransOffset = 8;

                    ;% q_hover_P.HILReadEncoderTimebase_Clock
                    section.data(8).logicalSrcIdx = 77;
                    section.data(8).dtTransOffset = 9;

            nTotData = nTotData + section.nData;
            paramMap.sections(4) = section;
            clear section

            section.nData     = 8;
            section.data(8)  = dumData; %prealloc

                    ;% q_hover_P.HILInitialize_AIChannels
                    section.data(1).logicalSrcIdx = 78;
                    section.data(1).dtTransOffset = 0;

                    ;% q_hover_P.HILInitialize_AOChannels
                    section.data(2).logicalSrcIdx = 79;
                    section.data(2).dtTransOffset = 8;

                    ;% q_hover_P.HILInitialize_DOChannels
                    section.data(3).logicalSrcIdx = 80;
                    section.data(3).dtTransOffset = 16;

                    ;% q_hover_P.HILInitialize_EIChannels
                    section.data(4).logicalSrcIdx = 81;
                    section.data(4).dtTransOffset = 20;

                    ;% q_hover_P.HILInitialize_EIQuadrature
                    section.data(5).logicalSrcIdx = 82;
                    section.data(5).dtTransOffset = 28;

                    ;% q_hover_P.HILInitialize_POChannels
                    section.data(6).logicalSrcIdx = 83;
                    section.data(6).dtTransOffset = 29;

                    ;% q_hover_P.HILReadEncoderTimebase_Channels
                    section.data(7).logicalSrcIdx = 84;
                    section.data(7).dtTransOffset = 37;

                    ;% q_hover_P.HILReadEncoderTimebase_SamplesI
                    section.data(8).logicalSrcIdx = 85;
                    section.data(8).dtTransOffset = 40;

            nTotData = nTotData + section.nData;
            paramMap.sections(5) = section;
            clear section

            section.nData     = 1;
            section.data(1)  = dumData; %prealloc

                    ;% q_hover_P.GameController_BufferSize
                    section.data(1).logicalSrcIdx = 86;
                    section.data(1).dtTransOffset = 0;

            nTotData = nTotData + section.nData;
            paramMap.sections(6) = section;
            clear section

            section.nData     = 39;
            section.data(39)  = dumData; %prealloc

                    ;% q_hover_P.HILInitialize_Active
                    section.data(1).logicalSrcIdx = 87;
                    section.data(1).dtTransOffset = 0;

                    ;% q_hover_P.HILInitialize_AOTerminate
                    section.data(2).logicalSrcIdx = 88;
                    section.data(2).dtTransOffset = 1;

                    ;% q_hover_P.HILInitialize_AOExit
                    section.data(3).logicalSrcIdx = 89;
                    section.data(3).dtTransOffset = 2;

                    ;% q_hover_P.HILInitialize_DOTerminate
                    section.data(4).logicalSrcIdx = 90;
                    section.data(4).dtTransOffset = 3;

                    ;% q_hover_P.HILInitialize_DOExit
                    section.data(5).logicalSrcIdx = 91;
                    section.data(5).dtTransOffset = 4;

                    ;% q_hover_P.HILInitialize_POTerminate
                    section.data(6).logicalSrcIdx = 92;
                    section.data(6).dtTransOffset = 5;

                    ;% q_hover_P.HILInitialize_POExit
                    section.data(7).logicalSrcIdx = 93;
                    section.data(7).dtTransOffset = 6;

                    ;% q_hover_P.HILInitialize_CKPStart
                    section.data(8).logicalSrcIdx = 94;
                    section.data(8).dtTransOffset = 7;

                    ;% q_hover_P.HILInitialize_CKPEnter
                    section.data(9).logicalSrcIdx = 95;
                    section.data(9).dtTransOffset = 8;

                    ;% q_hover_P.HILInitialize_CKStart
                    section.data(10).logicalSrcIdx = 96;
                    section.data(10).dtTransOffset = 9;

                    ;% q_hover_P.HILInitialize_CKEnter
                    section.data(11).logicalSrcIdx = 97;
                    section.data(11).dtTransOffset = 10;

                    ;% q_hover_P.HILInitialize_AIPStart
                    section.data(12).logicalSrcIdx = 98;
                    section.data(12).dtTransOffset = 11;

                    ;% q_hover_P.HILInitialize_AIPEnter
                    section.data(13).logicalSrcIdx = 99;
                    section.data(13).dtTransOffset = 12;

                    ;% q_hover_P.HILInitialize_AOPStart
                    section.data(14).logicalSrcIdx = 100;
                    section.data(14).dtTransOffset = 13;

                    ;% q_hover_P.HILInitialize_AOPEnter
                    section.data(15).logicalSrcIdx = 101;
                    section.data(15).dtTransOffset = 14;

                    ;% q_hover_P.HILInitialize_AOStart
                    section.data(16).logicalSrcIdx = 102;
                    section.data(16).dtTransOffset = 15;

                    ;% q_hover_P.HILInitialize_AOEnter
                    section.data(17).logicalSrcIdx = 103;
                    section.data(17).dtTransOffset = 16;

                    ;% q_hover_P.HILInitialize_AOReset
                    section.data(18).logicalSrcIdx = 104;
                    section.data(18).dtTransOffset = 17;

                    ;% q_hover_P.HILInitialize_DOPStart
                    section.data(19).logicalSrcIdx = 105;
                    section.data(19).dtTransOffset = 18;

                    ;% q_hover_P.HILInitialize_DOPEnter
                    section.data(20).logicalSrcIdx = 106;
                    section.data(20).dtTransOffset = 19;

                    ;% q_hover_P.HILInitialize_DOStart
                    section.data(21).logicalSrcIdx = 107;
                    section.data(21).dtTransOffset = 20;

                    ;% q_hover_P.HILInitialize_DOEnter
                    section.data(22).logicalSrcIdx = 108;
                    section.data(22).dtTransOffset = 21;

                    ;% q_hover_P.HILInitialize_DOReset
                    section.data(23).logicalSrcIdx = 109;
                    section.data(23).dtTransOffset = 22;

                    ;% q_hover_P.HILInitialize_EIPStart
                    section.data(24).logicalSrcIdx = 110;
                    section.data(24).dtTransOffset = 23;

                    ;% q_hover_P.HILInitialize_EIPEnter
                    section.data(25).logicalSrcIdx = 111;
                    section.data(25).dtTransOffset = 24;

                    ;% q_hover_P.HILInitialize_EIStart
                    section.data(26).logicalSrcIdx = 112;
                    section.data(26).dtTransOffset = 25;

                    ;% q_hover_P.HILInitialize_EIEnter
                    section.data(27).logicalSrcIdx = 113;
                    section.data(27).dtTransOffset = 26;

                    ;% q_hover_P.HILInitialize_POPStart
                    section.data(28).logicalSrcIdx = 114;
                    section.data(28).dtTransOffset = 27;

                    ;% q_hover_P.HILInitialize_POPEnter
                    section.data(29).logicalSrcIdx = 115;
                    section.data(29).dtTransOffset = 28;

                    ;% q_hover_P.HILInitialize_POStart
                    section.data(30).logicalSrcIdx = 116;
                    section.data(30).dtTransOffset = 29;

                    ;% q_hover_P.HILInitialize_POEnter
                    section.data(31).logicalSrcIdx = 117;
                    section.data(31).dtTransOffset = 30;

                    ;% q_hover_P.HILInitialize_POReset
                    section.data(32).logicalSrcIdx = 118;
                    section.data(32).dtTransOffset = 31;

                    ;% q_hover_P.HILInitialize_OOReset
                    section.data(33).logicalSrcIdx = 119;
                    section.data(33).dtTransOffset = 32;

                    ;% q_hover_P.HILInitialize_DOFinal
                    section.data(34).logicalSrcIdx = 120;
                    section.data(34).dtTransOffset = 33;

                    ;% q_hover_P.HILInitialize_DOInitial
                    section.data(35).logicalSrcIdx = 121;
                    section.data(35).dtTransOffset = 34;

                    ;% q_hover_P.HILReadEncoderTimebase_Active
                    section.data(36).logicalSrcIdx = 122;
                    section.data(36).dtTransOffset = 35;

                    ;% q_hover_P.HILWriteAnalog_Active
                    section.data(37).logicalSrcIdx = 123;
                    section.data(37).dtTransOffset = 36;

                    ;% q_hover_P.GameController_AutoCenter
                    section.data(38).logicalSrcIdx = 124;
                    section.data(38).dtTransOffset = 37;

                    ;% q_hover_P.GameController_Enabled
                    section.data(39).logicalSrcIdx = 125;
                    section.data(39).dtTransOffset = 38;

            nTotData = nTotData + section.nData;
            paramMap.sections(7) = section;
            clear section

            section.nData     = 3;
            section.data(3)  = dumData; %prealloc

                    ;% q_hover_P.HILReadEncoderTimebase_Overflow
                    section.data(1).logicalSrcIdx = 126;
                    section.data(1).dtTransOffset = 0;

                    ;% q_hover_P.ManualSwitch_CurrentSetting
                    section.data(2).logicalSrcIdx = 127;
                    section.data(2).dtTransOffset = 1;

                    ;% q_hover_P.GameController_ControllerNumber
                    section.data(3).logicalSrcIdx = 128;
                    section.data(3).dtTransOffset = 2;

            nTotData = nTotData + section.nData;
            paramMap.sections(8) = section;
            clear section


            ;%
            ;% Non-auto Data (parameter)
            ;%


        ;%
        ;% Add final counts to struct.
        ;%
        paramMap.nTotData = nTotData;



    ;%**************************
    ;% Create Block Output Map *
    ;%**************************
    
        nTotData      = 0; %add to this count as we go
        nTotSects     = 1;
        sectIdxOffset = 0;

        ;%
        ;% Define dummy sections & preallocate arrays
        ;%
        dumSection.nData = -1;
        dumSection.data  = [];

        dumData.logicalSrcIdx = -1;
        dumData.dtTransOffset = -1;

        ;%
        ;% Init/prealloc sigMap
        ;%
        sigMap.nSections           = nTotSects;
        sigMap.sectIdxOffset       = sectIdxOffset;
            sigMap.sections(nTotSects) = dumSection; %prealloc
        sigMap.nTotData            = -1;

        ;%
        ;% Auto data (q_hover_B)
        ;%
            section.nData     = 15;
            section.data(15)  = dumData; %prealloc

                    ;% q_hover_B.pitch
                    section.data(1).logicalSrcIdx = 0;
                    section.data(1).dtTransOffset = 0;

                    ;% q_hover_B.roll
                    section.data(2).logicalSrcIdx = 1;
                    section.data(2).dtTransOffset = 1;

                    ;% q_hover_B.yaw
                    section.data(3).logicalSrcIdx = 2;
                    section.data(3).dtTransOffset = 2;

                    ;% q_hover_B.ConverttoVector
                    section.data(4).logicalSrcIdx = 3;
                    section.data(4).dtTransOffset = 3;

                    ;% q_hover_B.LimitRateofDesiredAngle
                    section.data(5).logicalSrcIdx = 7;
                    section.data(5).dtTransOffset = 7;

                    ;% q_hover_B.LimitRateofDesiredAngle_f
                    section.data(6).logicalSrcIdx = 9;
                    section.data(6).dtTransOffset = 10;

                    ;% q_hover_B.CableGainPreCompensation
                    section.data(7).logicalSrcIdx = 10;
                    section.data(7).dtTransOffset = 13;

                    ;% q_hover_B.CableGain
                    section.data(8).logicalSrcIdx = 11;
                    section.data(8).dtTransOffset = 17;

                    ;% q_hover_B.Gain
                    section.data(9).logicalSrcIdx = 12;
                    section.data(9).dtTransOffset = 21;

                    ;% q_hover_B.Gain_p
                    section.data(10).logicalSrcIdx = 13;
                    section.data(10).dtTransOffset = 27;

                    ;% q_hover_B.RateTransition
                    section.data(11).logicalSrcIdx = 14;
                    section.data(11).dtTransOffset = 33;

                    ;% q_hover_B.RateTransition1
                    section.data(12).logicalSrcIdx = 15;
                    section.data(12).dtTransOffset = 34;

                    ;% q_hover_B.RateTransition2
                    section.data(13).logicalSrcIdx = 16;
                    section.data(13).dtTransOffset = 35;

                    ;% q_hover_B.GameController_o7
                    section.data(14).logicalSrcIdx = 17;
                    section.data(14).dtTransOffset = 36;

                    ;% q_hover_B.GameController_o8
                    section.data(15).logicalSrcIdx = 18;
                    section.data(15).dtTransOffset = 37;

            nTotData = nTotData + section.nData;
            sigMap.sections(1) = section;
            clear section


            ;%
            ;% Non-auto Data (signal)
            ;%


        ;%
        ;% Add final counts to struct.
        ;%
        sigMap.nTotData = nTotData;



    ;%*******************
    ;% Create DWork Map *
    ;%*******************
    
        nTotData      = 0; %add to this count as we go
        nTotSects     = 8;
        sectIdxOffset = 1;

        ;%
        ;% Define dummy sections & preallocate arrays
        ;%
        dumSection.nData = -1;
        dumSection.data  = [];

        dumData.logicalSrcIdx = -1;
        dumData.dtTransOffset = -1;

        ;%
        ;% Init/prealloc dworkMap
        ;%
        dworkMap.nSections           = nTotSects;
        dworkMap.sectIdxOffset       = sectIdxOffset;
            dworkMap.sections(nTotSects) = dumSection; %prealloc
        dworkMap.nTotData            = -1;

        ;%
        ;% Auto data (q_hover_DW)
        ;%
            section.nData     = 15;
            section.data(15)  = dumData; %prealloc

                    ;% q_hover_DW.HILInitialize_AIMinimums
                    section.data(1).logicalSrcIdx = 0;
                    section.data(1).dtTransOffset = 0;

                    ;% q_hover_DW.HILInitialize_AIMaximums
                    section.data(2).logicalSrcIdx = 1;
                    section.data(2).dtTransOffset = 8;

                    ;% q_hover_DW.HILInitialize_AOMinimums
                    section.data(3).logicalSrcIdx = 2;
                    section.data(3).dtTransOffset = 16;

                    ;% q_hover_DW.HILInitialize_AOMaximums
                    section.data(4).logicalSrcIdx = 3;
                    section.data(4).dtTransOffset = 24;

                    ;% q_hover_DW.HILInitialize_AOVoltages
                    section.data(5).logicalSrcIdx = 4;
                    section.data(5).dtTransOffset = 32;

                    ;% q_hover_DW.HILInitialize_FilterFrequency
                    section.data(6).logicalSrcIdx = 5;
                    section.data(6).dtTransOffset = 40;

                    ;% q_hover_DW.HILInitialize_POSortedFreqs
                    section.data(7).logicalSrcIdx = 6;
                    section.data(7).dtTransOffset = 48;

                    ;% q_hover_DW.HILInitialize_POValues
                    section.data(8).logicalSrcIdx = 7;
                    section.data(8).dtTransOffset = 56;

                    ;% q_hover_DW.PrevY
                    section.data(9).logicalSrcIdx = 8;
                    section.data(9).dtTransOffset = 64;

                    ;% q_hover_DW.LastMajorTime
                    section.data(10).logicalSrcIdx = 9;
                    section.data(10).dtTransOffset = 67;

                    ;% q_hover_DW.PrevY_k
                    section.data(11).logicalSrcIdx = 10;
                    section.data(11).dtTransOffset = 68;

                    ;% q_hover_DW.LastMajorTime_k
                    section.data(12).logicalSrcIdx = 11;
                    section.data(12).dtTransOffset = 71;

                    ;% q_hover_DW.RateTransition_Buffer0
                    section.data(13).logicalSrcIdx = 12;
                    section.data(13).dtTransOffset = 72;

                    ;% q_hover_DW.RateTransition1_Buffer0
                    section.data(14).logicalSrcIdx = 13;
                    section.data(14).dtTransOffset = 73;

                    ;% q_hover_DW.RateTransition2_Buffer0
                    section.data(15).logicalSrcIdx = 14;
                    section.data(15).dtTransOffset = 74;

            nTotData = nTotData + section.nData;
            dworkMap.sections(1) = section;
            clear section

            section.nData     = 1;
            section.data(1)  = dumData; %prealloc

                    ;% q_hover_DW.GameController_Controller
                    section.data(1).logicalSrcIdx = 15;
                    section.data(1).dtTransOffset = 0;

            nTotData = nTotData + section.nData;
            dworkMap.sections(2) = section;
            clear section

            section.nData     = 1;
            section.data(1)  = dumData; %prealloc

                    ;% q_hover_DW.HILInitialize_Card
                    section.data(1).logicalSrcIdx = 16;
                    section.data(1).dtTransOffset = 0;

            nTotData = nTotData + section.nData;
            dworkMap.sections(3) = section;
            clear section

            section.nData     = 1;
            section.data(1)  = dumData; %prealloc

                    ;% q_hover_DW.HILReadEncoderTimebase_Task
                    section.data(1).logicalSrcIdx = 17;
                    section.data(1).dtTransOffset = 0;

            nTotData = nTotData + section.nData;
            dworkMap.sections(4) = section;
            clear section

            section.nData     = 9;
            section.data(9)  = dumData; %prealloc

                    ;% q_hover_DW.HILWriteAnalog_PWORK
                    section.data(1).logicalSrcIdx = 18;
                    section.data(1).dtTransOffset = 0;

                    ;% q_hover_DW.PitchAngledeg_PWORK.LoggedData
                    section.data(2).logicalSrcIdx = 19;
                    section.data(2).dtTransOffset = 1;

                    ;% q_hover_DW.RollAngledeg_PWORK.LoggedData
                    section.data(3).logicalSrcIdx = 20;
                    section.data(3).dtTransOffset = 2;

                    ;% q_hover_DW.YawAngledeg_PWORK.LoggedData
                    section.data(4).logicalSrcIdx = 21;
                    section.data(4).dtTransOffset = 3;

                    ;% q_hover_DW.BackMotorV_PWORK.LoggedData
                    section.data(5).logicalSrcIdx = 22;
                    section.data(5).dtTransOffset = 4;

                    ;% q_hover_DW.FrontMotorV_PWORK.LoggedData
                    section.data(6).logicalSrcIdx = 23;
                    section.data(6).dtTransOffset = 5;

                    ;% q_hover_DW.LeftMotorV_PWORK.LoggedData
                    section.data(7).logicalSrcIdx = 24;
                    section.data(7).dtTransOffset = 6;

                    ;% q_hover_DW.RightMotorV_PWORK.LoggedData
                    section.data(8).logicalSrcIdx = 25;
                    section.data(8).dtTransOffset = 7;

                    ;% q_hover_DW.Scope_PWORK.LoggedData
                    section.data(9).logicalSrcIdx = 26;
                    section.data(9).dtTransOffset = 8;

            nTotData = nTotData + section.nData;
            dworkMap.sections(5) = section;
            clear section

            section.nData     = 8;
            section.data(8)  = dumData; %prealloc

                    ;% q_hover_DW.HILInitialize_ClockModes
                    section.data(1).logicalSrcIdx = 27;
                    section.data(1).dtTransOffset = 0;

                    ;% q_hover_DW.HILInitialize_DOStates
                    section.data(2).logicalSrcIdx = 28;
                    section.data(2).dtTransOffset = 3;

                    ;% q_hover_DW.HILInitialize_QuadratureModes
                    section.data(3).logicalSrcIdx = 29;
                    section.data(3).dtTransOffset = 7;

                    ;% q_hover_DW.HILInitialize_InitialEICounts
                    section.data(4).logicalSrcIdx = 30;
                    section.data(4).dtTransOffset = 15;

                    ;% q_hover_DW.HILInitialize_POModeValues
                    section.data(5).logicalSrcIdx = 31;
                    section.data(5).dtTransOffset = 23;

                    ;% q_hover_DW.HILInitialize_POAlignValues
                    section.data(6).logicalSrcIdx = 32;
                    section.data(6).dtTransOffset = 31;

                    ;% q_hover_DW.HILInitialize_POPolarityVals
                    section.data(7).logicalSrcIdx = 33;
                    section.data(7).dtTransOffset = 39;

                    ;% q_hover_DW.HILReadEncoderTimebase_Buffer
                    section.data(8).logicalSrcIdx = 34;
                    section.data(8).dtTransOffset = 47;

            nTotData = nTotData + section.nData;
            dworkMap.sections(6) = section;
            clear section

            section.nData     = 1;
            section.data(1)  = dumData; %prealloc

                    ;% q_hover_DW.HILInitialize_POSortedChans
                    section.data(1).logicalSrcIdx = 35;
                    section.data(1).dtTransOffset = 0;

            nTotData = nTotData + section.nData;
            dworkMap.sections(7) = section;
            clear section

            section.nData     = 3;
            section.data(3)  = dumData; %prealloc

                    ;% q_hover_DW.HILInitialize_DOBits
                    section.data(1).logicalSrcIdx = 36;
                    section.data(1).dtTransOffset = 0;

                    ;% q_hover_DW.PrevLimited
                    section.data(2).logicalSrcIdx = 37;
                    section.data(2).dtTransOffset = 4;

                    ;% q_hover_DW.PrevLimited_l
                    section.data(3).logicalSrcIdx = 38;
                    section.data(3).dtTransOffset = 7;

            nTotData = nTotData + section.nData;
            dworkMap.sections(8) = section;
            clear section


            ;%
            ;% Non-auto Data (dwork)
            ;%


        ;%
        ;% Add final counts to struct.
        ;%
        dworkMap.nTotData = nTotData;



    ;%
    ;% Add individual maps to base struct.
    ;%

    targMap.paramMap  = paramMap;
    targMap.signalMap = sigMap;
    targMap.dworkMap  = dworkMap;

    ;%
    ;% Add checksums to base struct.
    ;%


    targMap.checksum0 = 1808776896;
    targMap.checksum1 = 4252722;
    targMap.checksum2 = 49714659;
    targMap.checksum3 = 1820460352;

