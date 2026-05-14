"""GRSIMWrite .grsp file exporter.

Uses the full 11.grsp template (all ~670 controls) and substitutes
only the SIM-specific values. GRSIMWrite requires ALL controls present.
"""
from __future__ import annotations
import os
import re
from typing import Any


# ── Full template based on 11.grsp structure ──────────────────────────────
# All 670 controls from a real LY14 LTE+GSM card, with placeholder markers.
_TEMPLATE = """\
GRSIMWrite Data file
V 1.0

Control0
Name=Image1

Control1
Name=GrpComm
State=-1

Control2
Name=Label8
State=-1

Control3
Name=Label10
State=-1

Control4
Name=Label14
State=-1

Control5
Name=Label16
State=-1

Control6
Name=Label17
State=-1

Control7
Name=Label18
State=-1

Control8
Name=Label20
State=-1

Control9
Name=LabADM
State=-1

Control10
Name=LabADM0
State=-1

Control11
Name=LabATR
State=-1

Control12
Name=Label42
State=-1

Control13
Name=LabLang
State=-1

Control14
Name=EditICCID
State=-1
Value={ICCID}

Control15
Name=EditPIN1
State=-1
Value={PIN1}

Control16
Name=EditPUK1
State=-1
Value={PUK1}

Control17
Name=EditPIN2
State=-1
Value={PIN1}

Control18
Name=EditPUK2
State=-1
Value={PUK1}

Control19
Name=EditADM
State=-1
Value={ADM}

Control20
Name=EditATR
State=-1
Value={ATR}

Control21
Name=ChkICCID_Inc
State=-1
Value=0

Control22
Name=EditType
State=-1
Value=LTE(LY14):LTE+GSM

Control23
Name=EditLang
State=-1
Value=English

Control24
Name=ButLang
State=-1

Control25
Name=EditApp
State=-1
Value=11100

Control26
Name=ButADN
State=-1

Control27
Name=GrpReader
State=-1

Control28
Name=Label1
State=-1

Control29
Name=CombReader
State=-1
Value=0

Control30
Name=ButReaderRefresh
State=-1

Control31
Name=ButReadCard
State=-1

Control32
Name=ButWriteCard
State=-1

Control33
Name=ButExit
State=-1

Control34
Name=ButSaveData
State=-1

Control35
Name=ButLoadData
State=-1

Control36
Name=ButHelp
State=-1

Control37
Name=GrpBatch
State=-1

Control38
Name=Label50
State=-1

Control39
Name=Label40
State=-1

Control40
Name=ButGo
State=0

Control41
Name=EditDataFile
State=-1
Value=

Control42
Name=ButSelectFile
State=-1

Control43
Name=ButFirst
State=0

Control44
Name=ButPrev
State=0

Control45
Name=ButNext
State=0

Control46
Name=ButLast
State=0

Control47
Name=EditDataRec
State=-1
Value=

Control48
Name=EditDataCount
State=-1
Value=

Control49
Name=ButFind
State=0

Control50
Name=ButContinue
State=-1

Control51
Name=ButTemplate
State=-1

Control52
Name=PageControlMain

Control53
Name=TabGSM

Control54
Name=GrpGSM
State=-1

Control55
Name=Label7
State=-1

Control56
Name=Label52
State=-1

Control57
Name=Label4
State=-1

Control58
Name=Label6
State=-1

Control59
Name=LabGSM_SMSP
State=-1

Control60
Name=Label59
State=-1

Control61
Name=LabGSM_SPN
State=-1

Control62
Name=Label62
State=-1

Control63
Name=Label9
State=-1

Control64
Name=Label11
State=-1

Control65
Name=Label69
State=-1

Control66
Name=LabGSM_GID1
State=-1

Control67
Name=Label53
State=-1

Control68
Name=LabGSM_GID2
State=-1

Control69
Name=LabGSM_MSISDN
State=-1

Control70
Name=Label91
State=-1

Control71
Name=Label3
State=-1

Control72
Name=LabGSM_ECC
State=-1

Control73
Name=LabGSM_EHPLMN
State=-1

Control74
Name=Label5
State=-1

Control75
Name=Image2

Control76
Name=LabImage2
State=-1

Control77
Name=PanGSM_IMSI

Control78
Name=RadGSM_IMSI18
State=-1
Value=0

Control79
Name=RadGSM_IMSI15
State=-1
Value=-1

Control80
Name=EditGSM_IMSI18
State=-1
Value={IMSI18}

Control81
Name=EditGSM_IMSI15
State=-1
Value={IMSI15}

Control82
Name=EditGSM_KI
State=-1
Value={KI}

Control83
Name=EditGSM_ACC
State=-1
Value=FFFF

Control84
Name=ChkGSM_ACC_Input
State=-1
Value=0

Control85
Name=ChkGSM_IMSI_Inc
State=-1
Value=0

Control86
Name=ChkGSM_KI_Inc
State=-1
Value=0

Control87
Name=EditGSM_SMSP
State=-1
Value=+

Control88
Name=EditGSM_FPLMN
State=-1
Value=

Control89
Name=EditGSM_SPN
State=-1
Value={SPN}

Control90
Name=EditGSM_PLMN
State=-1
Value={PLMN}

Control91
Name=EditGSM_HPLMN
State=-1
Value=01

Control92
Name=EditGSM_GID1
State=-1
Value=

Control93
Name=EditGSM_GID2
State=-1
Value=

Control94
Name=EditGSM_MSISDN
State=-1
Value={MSISDN}

Control95
Name=ChkGSM_MSISDN_Inc
State=-1
Value=0

Control96
Name=ButGSM_LTE
State=-1

Control97
Name=PanGSM_Alg

Control98
Name=RadGSM_Comp128_1
State=0
Value=-1

Control99
Name=RadGSM_Comp128_2
State=0
Value=0

Control100
Name=RadGSM_Comp128_3
State=0
Value=0

Control101
Name=RadGSM_MLG
State=-1
Value=0

Control102
Name=EditGSM_ECC
State=-1
Value=112; 911

Control103
Name=ButGSM_ECC
State=-1

Control104
Name=ButGSM_PLMN
State=-1

Control105
Name=ButGSM_FPLMN
State=-1

Control106
Name=EditGSM_EHPLMN
State=-1
Value={PLMN}

Control107
Name=ButGSM_EHPLMN
State=-1

Control108
Name=EditGSM_AD
State=-1
Value=00000003

Control109
Name=ButGSM_AD
State=-1

Control110
Name=ButGSM_PLMNAuto
State=-1

Control111
Name=ButGSM_Other
State=-1

Control112
Name=EditGSM_Other
State=-1
Value=

Control113
Name=ButAPDU
State=-1

Control114
Name=GrpLTE
State=-1

Control115
Name=Label73
State=-1

Control116
Name=Label74
State=-1

Control117
Name=Label75
State=-1

Control118
Name=Label76
State=-1

Control119
Name=Label77
State=-1

Control120
Name=Label78
State=-1

Control121
Name=LabLTE_SPN
State=-1

Control122
Name=Label81
State=-1

Control123
Name=LabLTE_PLMN
State=-1

Control124
Name=Label83
State=-1

Control125
Name=Label84
State=-1

Control126
Name=LabLTE_GID1
State=-1

Control127
Name=Label87
State=-1

Control128
Name=LabLTE_GID2
State=-1

Control129
Name=Label12
State=-1

Control130
Name=Label44
State=-1

Control131
Name=LabLTE_OPLMN
State=-1

Control132
Name=LabLTE_HPLMN
State=-1

Control133
Name=Label97
State=-1

Control134
Name=Label98
State=-1

Control135
Name=Label99
State=-1

Control136
Name=Label2
State=-1

Control137
Name=LabLTE_ECC
State=-1

Control138
Name=LabLTE_EHPLMN
State=-1

Control139
Name=Label13
State=-1

Control140
Name=PanLTE_OPC

Control141
Name=RadLTE_OPC
State=-1
Value=-1

Control142
Name=RadLTE_OP
State=-1
Value=0

Control143
Name=PanLTE_IMSI

Control144
Name=RadLTE_IMSI18
State=-1
Value=0

Control145
Name=RadLTE_IMSI15
State=-1
Value=-1

Control146
Name=EditLTE_IMSI18
State=-1
Value={IMSI18}

Control147
Name=EditLTE_IMSI15
State=-1
Value={IMSI15}

Control148
Name=EditLTE_KI
State=-1
Value={KI}

Control149
Name=EditLTE_ACC
State=-1
Value=FFFF

Control150
Name=ChkLTE_ACC_Input
State=-1
Value=0

Control151
Name=ChkLTE_IMSI_Inc
State=-1
Value=0

Control152
Name=ChkLTE_KI_Inc
State=-1
Value=0

Control153
Name=EditLTE_SMSP
State=-1
Value=+

Control154
Name=EditLTE_FPLMN
State=-1
Value=

Control155
Name=EditLTE_SPN
State=-1
Value={SPN}

Control156
Name=EditLTE_PLMN
State=-1
Value={PLMN}:4000

Control157
Name=EditLTE_HPPLMN
State=-1
Value=01

Control158
Name=EditLTE_GID1
State=-1
Value=

Control159
Name=EditLTE_GID2
State=-1
Value=

Control160
Name=EditLTE_OPC
State=-1
Value={OPC}

Control161
Name=EditLTE_OP
State=0
Value=

Control162
Name=EditLTE_OPLMN
State=-1
Value={OPLMN}

Control163
Name=EditLTE_HPLMN
State=-1
Value={OPLMN}

Control164
Name=EditLTE_MSISDN
State=-1
Value={MSISDN}

Control165
Name=ChkLTE_MSISDN_Inc
State=-1
Value=0

Control166
Name=PanLTE_Alg

Control167
Name=RadLTE_MLG
State=-1
Value=-1

Control168
Name=RadLTE_XOR
State=0
Value=0

Control169
Name=ButLTE_GSM
State=-1

Control170
Name=ButLTE_ECC
State=-1

Control171
Name=EditLTE_ECC
State=-1
Value=112:112:00; 911:911:00

Control172
Name=ButLTE_RC
State=-1

Control173
Name=ButLTE_PLMN
State=-1

Control174
Name=ButLTE_OPLMN
State=-1

Control175
Name=ButLTE_HPLMN
State=-1

Control176
Name=ButLTE_FPLMN
State=-1

Control177
Name=EditLTE_EHPLMN
State=-1
Value={PLMN}

Control178
Name=ButLTE_EHPLMN
State=-1

Control179
Name=EditLTE_R
State=-1
Value=

Control180
Name=EditLTE_C
State=-1
Value=

Control181
Name=EditLTE_AD
State=-1
Value=00000003

Control182
Name=ButLTE_AD
State=-1

Control183
Name=ButLTE_PLMNAuto
State=-1

Control184
Name=ButLTE_Other
State=-1

Control185
Name=EditLTE_Other
State=-1
Value=

Control186
Name=TabCDMA

Control187
Name=GrpCDMA
State=0

Control188
Name=Label22
State=0

Control189
Name=Label23
State=0

Control190
Name=Label24
State=0

Control191
Name=Label27
State=0

Control192
Name=Label28
State=0

Control193
Name=Label29
State=0

Control194
Name=Label30
State=0

Control195
Name=Label31
State=0

Control196
Name=Label32
State=0

Control197
Name=Label33
State=0

Control198
Name=LabNAIName
State=0

Control199
Name=Label35
State=0

Control200
Name=LabNAIPass
State=0

Control201
Name=Label37
State=0

Control202
Name=LabSIPName
State=0

Control203
Name=LabMIPName
State=0

Control204
Name=Label34
State=0

Control205
Name=Label36
State=0

Control206
Name=Label25
State=0

Control207
Name=Label38
State=0

Control208
Name=LabCDMA_IMSI_T
State=0

Control209
Name=Label54
State=0

Control210
Name=LabCDMA_ECC
State=0

Control211
Name=EditCDMA_IMSI
State=0
Value=

Control212
Name=EditCDMA_SID
State=0
Value=1

Control213
Name=EditCDMA_NID
State=0
Value=65535

Control214
Name=RadCDMA_UIMID
State=0
Value=-1

Control215
Name=EditCDMA_UIMID
State=0
Value=

Control216
Name=RadCDMA_ME_ESN
State=0
Value=0

Control217
Name=EditCDMA_ME_ESN
State=0
Value=

Control218
Name=RadCDMA_MEID
State=0
Value=0

Control219
Name=EditCDMA_MEID
State=0
Value=

Control220
Name=EditCDMA_AKEY
State=0
Value=

Control221
Name=EditNAI_Name
State=0
Value=

Control222
Name=EditNAI_Pass
State=0
Value=

Control223
Name=EditSIP_Name
State=0
Value=

Control224
Name=EditSIP_Pass
State=0
Value=

Control225
Name=EditMIP_Name
State=0
Value=

Control226
Name=EditMIP_Pass
State=0
Value=

Control227
Name=GrpSPN
State=0

Control228
Name=Label46
State=0

Control229
Name=Label47
State=0

Control230
Name=Label48
State=0

Control231
Name=Label49
State=0

Control232
Name=EditSPN_Name
State=0
Value=

Control233
Name=EditSPN_Disp
State=0
Value=

Control234
Name=CombSPN_Lang
State=0
Value=-1

Control235
Name=CombSPN_Code
State=0
Value=-1

Control236
Name=GrpPRL
State=0

Control237
Name=MemoPRL
State=0
Value=

Control238
Name=ButLoadPRL
State=0

Control239
Name=ButLoadEPRL
State=0

Control240
Name=MemoEPRL
State=0
Value=

Control241
Name=EditCDMA_ACC
State=0
Value=

Control242
Name=ChkCDMA_ACC_Input
State=0
Value=0

Control243
Name=EditCDMA_MDN
State=0
Value=

Control244
Name=ChkCDMA_IMSI_Inc
State=0
Value=0

Control245
Name=ChkCDMA_AKEY_Inc
State=0
Value=0

Control246
Name=ChkCDMA_MDN_Inc
State=0
Value=0

Control247
Name=ChkNAI_Name_Inc
State=0
Value=0

Control248
Name=ChkCDMA_ESN_Inc
State=0
Value=0

Control249
Name=EditCDMA_IMSI_T
State=0
Value=

Control250
Name=ChkCDMA_IMSI_T_Inc
State=0
Value=0

Control251
Name=ButSIP_Name
State=0

Control252
Name=ButMIP_Name
State=0

Control253
Name=EditCDMA_ECC
State=0
Value=

Control254
Name=ButCDMA_ECC
State=0

Control255
Name=ButCDMA_Other
State=0

Control256
Name=EditCDMA_Other
State=0
Value=

Control257
Name=TabISIM

Control258
Name=GrpISIM
State=0

Control259
Name=Label15
State=0

Control260
Name=Label19
State=0

Control261
Name=Label21
State=0

Control262
Name=Label26
State=0

Control263
Name=Label39
State=0

Control264
Name=EditISIM_DOMAIN
State=0
Value=

Control265
Name=EditISIM_IMPI
State=0
Value=

Control266
Name=EditISIM_IMPU
State=0
Value=

Control267
Name=EditISIM_PCSCF
State=0
Value=

Control268
Name=EditISIM_AD
State=0
Value=

Control269
Name=ButISIM_DOMAINAuto
State=0

Control270
Name=ButISIM_IMPIAuto
State=0

Control271
Name=ButISIM_IMPUAuto1
State=0

Control272
Name=ButISIM_PCSCFAuto
State=0

Control273
Name=ButISIM_IMPUAuto2
State=0

Control274
Name=TabJAVA

Control275
Name=GrpJava
State=0

Control276
Name=PageControlJava

Control277
Name=TabSheet1

Control278
Name=GrpJAVA_GP_ENC
State=-1

Control279
Name=LabJAVA_GP_ENC00
State=0

Control280
Name=LabJAVA_GP_ENC01
State=0

Control281
Name=LabJAVA_GP_ENC02
State=0

Control282
Name=LabJAVA_GP_ENC03
State=0

Control283
Name=LabJAVA_GP_ENC04
State=0

Control284
Name=LabJAVA_GP_ENC05
State=0

Control285
Name=LabJAVA_GP_ENC06
State=0

Control286
Name=LabJAVA_GP_ENC07
State=0

Control287
Name=LabJAVA_GP_ENC0F
State=0

Control288
Name=LabJAVA_GP_ENC0E
State=0

Control289
Name=LabJAVA_GP_ENC08
State=0

Control290
Name=LabJAVA_GP_ENC09
State=0

Control291
Name=LabJAVA_GP_ENC0A
State=0

Control292
Name=LabJAVA_GP_ENC0B
State=0

Control293
Name=LabJAVA_GP_ENC0C
State=0

Control294
Name=LabJAVA_GP_ENC0D
State=0

Control295
Name=Label43
State=-1

Control296
Name=EditJAVA_GP_ENC00
State=0
Value=

Control297
Name=EditJAVA_GP_ENC01
State=0
Value=

Control298
Name=EditJAVA_GP_ENC02
State=0
Value=

Control299
Name=EditJAVA_GP_ENC03
State=0
Value=

Control300
Name=EditJAVA_GP_ENC04
State=0
Value=

Control301
Name=EditJAVA_GP_ENC05
State=0
Value=

Control302
Name=EditJAVA_GP_ENC06
State=0
Value=

Control303
Name=EditJAVA_GP_ENC07
State=0
Value=

Control304
Name=EditJAVA_GP_ENC0F
State=0
Value=

Control305
Name=EditJAVA_GP_ENC0E
State=0
Value=

Control306
Name=EditJAVA_GP_ENC0D
State=0
Value=

Control307
Name=EditJAVA_GP_ENC0C
State=0
Value=

Control308
Name=EditJAVA_GP_ENC0B
State=0
Value=

Control309
Name=EditJAVA_GP_ENC0A
State=0
Value=

Control310
Name=EditJAVA_GP_ENC09
State=0
Value=

Control311
Name=EditJAVA_GP_ENC08
State=0
Value=

Control312
Name=ButJava_GP_ENC_SAME
State=-1

Control313
Name=CombJAVA_GP_Num
State=-1
Value=-1

Control314
Name=GrpJAVA_GP_MAC
State=-1

Control315
Name=LabJAVA_GP_MAC00
State=0

Control316
Name=LabJAVA_GP_MAC01
State=0

Control317
Name=LabJAVA_GP_MAC02
State=0

Control318
Name=LabJAVA_GP_MAC03
State=0

Control319
Name=LabJAVA_GP_MAC04
State=0

Control320
Name=LabJAVA_GP_MAC05
State=0

Control321
Name=LabJAVA_GP_MAC06
State=0

Control322
Name=LabJAVA_GP_MAC07
State=0

Control323
Name=LabJAVA_GP_MAC0F
State=0

Control324
Name=LabJAVA_GP_MAC0E
State=0

Control325
Name=LabJAVA_GP_MAC08
State=0

Control326
Name=LabJAVA_GP_MAC09
State=0

Control327
Name=LabJAVA_GP_MAC0A
State=0

Control328
Name=LabJAVA_GP_MAC0B
State=0

Control329
Name=LabJAVA_GP_MAC0C
State=0

Control330
Name=LabJAVA_GP_MAC0D
State=0

Control331
Name=EditJAVA_GP_MAC00
State=0
Value=

Control332
Name=EditJAVA_GP_MAC01
State=0
Value=

Control333
Name=EditJAVA_GP_MAC02
State=0
Value=

Control334
Name=EditJAVA_GP_MAC03
State=0
Value=

Control335
Name=EditJAVA_GP_MAC04
State=0
Value=

Control336
Name=EditJAVA_GP_MAC05
State=0
Value=

Control337
Name=EditJAVA_GP_MAC06
State=0
Value=

Control338
Name=EditJAVA_GP_MAC07
State=0
Value=

Control339
Name=EditJAVA_GP_MAC0F
State=0
Value=

Control340
Name=EditJAVA_GP_MAC0E
State=0
Value=

Control341
Name=EditJAVA_GP_MAC0D
State=0
Value=

Control342
Name=EditJAVA_GP_MAC0C
State=0
Value=

Control343
Name=EditJAVA_GP_MAC0B
State=0
Value=

Control344
Name=EditJAVA_GP_MAC0A
State=0
Value=

Control345
Name=EditJAVA_GP_MAC09
State=0
Value=

Control346
Name=EditJAVA_GP_MAC08
State=0
Value=

Control347
Name=ButJava_GP_MAC_SAME
State=-1

Control348
Name=GrpJAVA_GP_DEK
State=-1

Control349
Name=LabJAVA_GP_DEK00
State=0

Control350
Name=LabJAVA_GP_DEK01
State=0

Control351
Name=LabJAVA_GP_DEK02
State=0

Control352
Name=LabJAVA_GP_DEK03
State=0

Control353
Name=LabJAVA_GP_DEK04
State=0

Control354
Name=LabJAVA_GP_DEK05
State=0

Control355
Name=LabJAVA_GP_DEK06
State=0

Control356
Name=LabJAVA_GP_DEK07
State=0

Control357
Name=LabJAVA_GP_DEK0F
State=0

Control358
Name=LabJAVA_GP_DEK0E
State=0

Control359
Name=LabJAVA_GP_DEK08
State=0

Control360
Name=LabJAVA_GP_DEK09
State=0

Control361
Name=LabJAVA_GP_DEK0A
State=0

Control362
Name=LabJAVA_GP_DEK0B
State=0

Control363
Name=LabJAVA_GP_DEK0C
State=0

Control364
Name=LabJAVA_GP_DEK0D
State=0

Control365
Name=EditJAVA_GP_DEK00
State=0
Value=

Control366
Name=EditJAVA_GP_DEK01
State=0
Value=

Control367
Name=EditJAVA_GP_DEK02
State=0
Value=

Control368
Name=EditJAVA_GP_DEK03
State=0
Value=

Control369
Name=EditJAVA_GP_DEK04
State=0
Value=

Control370
Name=EditJAVA_GP_DEK05
State=0
Value=

Control371
Name=EditJAVA_GP_DEK06
State=0
Value=

Control372
Name=EditJAVA_GP_DEK07
State=0
Value=

Control373
Name=EditJAVA_GP_DEK0F
State=0
Value=

Control374
Name=EditJAVA_GP_DEK0E
State=0
Value=

Control375
Name=EditJAVA_GP_DEK0D
State=0
Value=

Control376
Name=EditJAVA_GP_DEK0C
State=0
Value=

Control377
Name=EditJAVA_GP_DEK0B
State=0
Value=

Control378
Name=EditJAVA_GP_DEK0A
State=0
Value=

Control379
Name=EditJAVA_GP_DEK09
State=0
Value=

Control380
Name=EditJAVA_GP_DEK08
State=0
Value=

Control381
Name=ButJava_GP_DEK_SAME
State=-1

Control382
Name=TabSheet2

Control383
Name=GrpJAVA_DES_KIC
State=-1

Control384
Name=LabJAVA_DES_KIC00
State=0

Control385
Name=LabJAVA_DES_KIC01
State=0

Control386
Name=LabJAVA_DES_KIC02
State=0

Control387
Name=LabJAVA_DES_KIC03
State=0

Control388
Name=LabJAVA_DES_KIC04
State=0

Control389
Name=LabJAVA_DES_KIC05
State=0

Control390
Name=LabJAVA_DES_KIC06
State=0

Control391
Name=LabJAVA_DES_KIC07
State=0

Control392
Name=LabJAVA_DES_KIC0F
State=0

Control393
Name=LabJAVA_DES_KIC0E
State=0

Control394
Name=LabJAVA_DES_KIC08
State=0

Control395
Name=LabJAVA_DES_KIC09
State=0

Control396
Name=LabJAVA_DES_KIC0A
State=0

Control397
Name=LabJAVA_DES_KIC0B
State=0

Control398
Name=LabJAVA_DES_KIC0C
State=0

Control399
Name=LabJAVA_DES_KIC0D
State=0

Control400
Name=Label45
State=-1

Control401
Name=EditJAVA_DES_0348_KIC00
State=0
Value=

Control402
Name=EditJAVA_DES_0348_KIC01
State=0
Value=

Control403
Name=EditJAVA_DES_0348_KIC02
State=0
Value=

Control404
Name=EditJAVA_DES_0348_KIC03
State=0
Value=

Control405
Name=EditJAVA_DES_0348_KIC04
State=0
Value=

Control406
Name=EditJAVA_DES_0348_KIC05
State=0
Value=

Control407
Name=EditJAVA_DES_0348_KIC06
State=0
Value=

Control408
Name=EditJAVA_DES_0348_KIC07
State=0
Value=

Control409
Name=EditJAVA_DES_0348_KIC0F
State=0
Value=

Control410
Name=EditJAVA_DES_0348_KIC0E
State=0
Value=

Control411
Name=EditJAVA_DES_0348_KIC0D
State=0
Value=

Control412
Name=EditJAVA_DES_0348_KIC0C
State=0
Value=

Control413
Name=EditJAVA_DES_0348_KIC0B
State=0
Value=

Control414
Name=EditJAVA_DES_0348_KIC0A
State=0
Value=

Control415
Name=EditJAVA_DES_0348_KIC09
State=0
Value=

Control416
Name=EditJAVA_DES_0348_KIC08
State=0
Value=

Control417
Name=ButJava_DES_KIC_SAME
State=-1

Control418
Name=CombJAVA_DES_Num
State=-1
Value=-1

Control419
Name=GrpJAVA_DES_KID
State=-1

Control420
Name=LabJAVA_DES_KID00
State=0

Control421
Name=LabJAVA_DES_KID01
State=0

Control422
Name=LabJAVA_DES_KID02
State=0

Control423
Name=LabJAVA_DES_KID03
State=0

Control424
Name=LabJAVA_DES_KID04
State=0

Control425
Name=LabJAVA_DES_KID05
State=0

Control426
Name=LabJAVA_DES_KID06
State=0

Control427
Name=LabJAVA_DES_KID07
State=0

Control428
Name=LabJAVA_DES_KID0F
State=0

Control429
Name=LabJAVA_DES_KID0E
State=0

Control430
Name=LabJAVA_DES_KID08
State=0

Control431
Name=LabJAVA_DES_KID09
State=0

Control432
Name=LabJAVA_DES_KID0A
State=0

Control433
Name=LabJAVA_DES_KID0B
State=0

Control434
Name=LabJAVA_DES_KID0C
State=0

Control435
Name=LabJAVA_DES_KID0D
State=0

Control436
Name=EditJAVA_DES_0348_KID00
State=0
Value=

Control437
Name=EditJAVA_DES_0348_KID01
State=0
Value=

Control438
Name=EditJAVA_DES_0348_KID02
State=0
Value=

Control439
Name=EditJAVA_DES_0348_KID03
State=0
Value=

Control440
Name=EditJAVA_DES_0348_KID04
State=0
Value=

Control441
Name=EditJAVA_DES_0348_KID05
State=0
Value=

Control442
Name=EditJAVA_DES_0348_KID06
State=0
Value=

Control443
Name=EditJAVA_DES_0348_KID07
State=0
Value=

Control444
Name=EditJAVA_DES_0348_KID0F
State=0
Value=

Control445
Name=EditJAVA_DES_0348_KID0E
State=0
Value=

Control446
Name=EditJAVA_DES_0348_KID0D
State=0
Value=

Control447
Name=EditJAVA_DES_0348_KID0C
State=0
Value=

Control448
Name=EditJAVA_DES_0348_KID0B
State=0
Value=

Control449
Name=EditJAVA_DES_0348_KID0A
State=0
Value=

Control450
Name=EditJAVA_DES_0348_KID09
State=0
Value=

Control451
Name=EditJAVA_DES_0348_KID08
State=0
Value=

Control452
Name=ButJava_DES_KID_SAME
State=-1

Control453
Name=GrpJAVA_DES_KIK
State=-1

Control454
Name=LabJAVA_DES_KIK00
State=0

Control455
Name=LabJAVA_DES_KIK01
State=0

Control456
Name=LabJAVA_DES_KIK02
State=0

Control457
Name=LabJAVA_DES_KIK03
State=0

Control458
Name=LabJAVA_DES_KIK04
State=0

Control459
Name=LabJAVA_DES_KIK05
State=0

Control460
Name=LabJAVA_DES_KIK06
State=0

Control461
Name=LabJAVA_DES_KIK07
State=0

Control462
Name=LabJAVA_DES_KIK0F
State=0

Control463
Name=LabJAVA_DES_KIK0E
State=0

Control464
Name=LabJAVA_DES_KIK08
State=0

Control465
Name=LabJAVA_DES_KIK09
State=0

Control466
Name=LabJAVA_DES_KIK0A
State=0

Control467
Name=LabJAVA_DES_KIK0B
State=0

Control468
Name=LabJAVA_DES_KIK0C
State=0

Control469
Name=LabJAVA_DES_KIK0D
State=0

Control470
Name=EditJAVA_DES_0348_KIK00
State=0
Value=

Control471
Name=EditJAVA_DES_0348_KIK01
State=0
Value=

Control472
Name=EditJAVA_DES_0348_KIK02
State=0
Value=

Control473
Name=EditJAVA_DES_0348_KIK03
State=0
Value=

Control474
Name=EditJAVA_DES_0348_KIK04
State=0
Value=

Control475
Name=EditJAVA_DES_0348_KIK05
State=0
Value=

Control476
Name=EditJAVA_DES_0348_KIK06
State=0
Value=

Control477
Name=EditJAVA_DES_0348_KIK07
State=0
Value=

Control478
Name=EditJAVA_DES_0348_KIK0F
State=0
Value=

Control479
Name=EditJAVA_DES_0348_KIK0E
State=0
Value=

Control480
Name=EditJAVA_DES_0348_KIK0D
State=0
Value=

Control481
Name=EditJAVA_DES_0348_KIK0C
State=0
Value=

Control482
Name=EditJAVA_DES_0348_KIK0B
State=0
Value=

Control483
Name=EditJAVA_DES_0348_KIK0A
State=0
Value=

Control484
Name=EditJAVA_DES_0348_KIK09
State=0
Value=

Control485
Name=EditJAVA_DES_0348_KIK08
State=0
Value=

Control486
Name=ButJava_DES_KIK_SAME
State=-1

Control487
Name=TabSheet3

Control488
Name=GrpJAVA_AES_KIC
State=-1

Control489
Name=LabJAVA_AES_KIC00
State=0

Control490
Name=LabJAVA_AES_KIC01
State=0

Control491
Name=LabJAVA_AES_KIC02
State=0

Control492
Name=LabJAVA_AES_KIC03
State=0

Control493
Name=LabJAVA_AES_KIC04
State=0

Control494
Name=LabJAVA_AES_KIC05
State=0

Control495
Name=LabJAVA_AES_KIC06
State=0

Control496
Name=LabJAVA_AES_KIC07
State=0

Control497
Name=LabJAVA_AES_KIC0F
State=0

Control498
Name=LabJAVA_AES_KIC0E
State=0

Control499
Name=LabJAVA_AES_KIC08
State=0

Control500
Name=LabJAVA_AES_KIC09
State=0

Control501
Name=LabJAVA_AES_KIC0A
State=0

Control502
Name=LabJAVA_AES_KIC0B
State=0

Control503
Name=LabJAVA_AES_KIC0C
State=0

Control504
Name=LabJAVA_AES_KIC0D
State=0

Control505
Name=Label51
State=-1

Control506
Name=EditJAVA_AES_0348_KIC00
State=0
Value=

Control507
Name=EditJAVA_AES_0348_KIC01
State=0
Value=

Control508
Name=EditJAVA_AES_0348_KIC02
State=0
Value=

Control509
Name=EditJAVA_AES_0348_KIC03
State=0
Value=

Control510
Name=EditJAVA_AES_0348_KIC04
State=0
Value=

Control511
Name=EditJAVA_AES_0348_KIC05
State=0
Value=

Control512
Name=EditJAVA_AES_0348_KIC06
State=0
Value=

Control513
Name=EditJAVA_AES_0348_KIC07
State=0
Value=

Control514
Name=EditJAVA_AES_0348_KIC0F
State=0
Value=

Control515
Name=EditJAVA_AES_0348_KIC0E
State=0
Value=

Control516
Name=EditJAVA_AES_0348_KIC0D
State=0
Value=

Control517
Name=EditJAVA_AES_0348_KIC0C
State=0
Value=

Control518
Name=EditJAVA_AES_0348_KIC0B
State=0
Value=

Control519
Name=EditJAVA_AES_0348_KIC0A
State=0
Value=

Control520
Name=EditJAVA_AES_0348_KIC09
State=0
Value=

Control521
Name=EditJAVA_AES_0348_KIC08
State=0
Value=

Control522
Name=ButJava_AES_KIC_SAME
State=-1

Control523
Name=CombJAVA_AES_Num
State=-1
Value=-1

Control524
Name=GrpJAVA_AES_KID
State=-1

Control525
Name=LabJAVA_AES_KID00
State=0

Control526
Name=LabJAVA_AES_KID01
State=0

Control527
Name=LabJAVA_AES_KID02
State=0

Control528
Name=LabJAVA_AES_KID03
State=0

Control529
Name=LabJAVA_AES_KID04
State=0

Control530
Name=LabJAVA_AES_KID05
State=0

Control531
Name=LabJAVA_AES_KID06
State=0

Control532
Name=LabJAVA_AES_KID07
State=0

Control533
Name=LabJAVA_AES_KID0F
State=0

Control534
Name=LabJAVA_AES_KID0E
State=0

Control535
Name=LabJAVA_AES_KID08
State=0

Control536
Name=LabJAVA_AES_KID09
State=0

Control537
Name=LabJAVA_AES_KID0A
State=0

Control538
Name=LabJAVA_AES_KID0B
State=0

Control539
Name=LabJAVA_AES_KID0C
State=0

Control540
Name=LabJAVA_AES_KID0D
State=0

Control541
Name=EditJAVA_AES_0348_KID00
State=0
Value=

Control542
Name=EditJAVA_AES_0348_KID01
State=0
Value=

Control543
Name=EditJAVA_AES_0348_KID02
State=0
Value=

Control544
Name=EditJAVA_AES_0348_KID03
State=0
Value=

Control545
Name=EditJAVA_AES_0348_KID04
State=0
Value=

Control546
Name=EditJAVA_AES_0348_KID05
State=0
Value=

Control547
Name=EditJAVA_AES_0348_KID06
State=0
Value=

Control548
Name=EditJAVA_AES_0348_KID07
State=0
Value=

Control549
Name=EditJAVA_AES_0348_KID0F
State=0
Value=

Control550
Name=EditJAVA_AES_0348_KID0E
State=0
Value=

Control551
Name=EditJAVA_AES_0348_KID0D
State=0
Value=

Control552
Name=EditJAVA_AES_0348_KID0C
State=0
Value=

Control553
Name=EditJAVA_AES_0348_KID0B
State=0
Value=

Control554
Name=EditJAVA_AES_0348_KID0A
State=0
Value=

Control555
Name=EditJAVA_AES_0348_KID09
State=0
Value=

Control556
Name=EditJAVA_AES_0348_KID08
State=0
Value=

Control557
Name=ButJava_AES_KID_SAME
State=-1

Control558
Name=GrpJAVA_AES_KIK
State=-1

Control559
Name=LabJAVA_AES_KIK00
State=0

Control560
Name=LabJAVA_AES_KIK01
State=0

Control561
Name=LabJAVA_AES_KIK02
State=0

Control562
Name=LabJAVA_AES_KIK03
State=0

Control563
Name=LabJAVA_AES_KIK04
State=0

Control564
Name=LabJAVA_AES_KIK05
State=0

Control565
Name=LabJAVA_AES_KIK06
State=0

Control566
Name=LabJAVA_AES_KIK07
State=0

Control567
Name=LabJAVA_AES_KIK0F
State=0

Control568
Name=LabJAVA_AES_KIK0E
State=0

Control569
Name=LabJAVA_AES_KIK08
State=0

Control570
Name=LabJAVA_AES_KIK09
State=0

Control571
Name=LabJAVA_AES_KIK0A
State=0

Control572
Name=LabJAVA_AES_KIK0B
State=0

Control573
Name=LabJAVA_AES_KIK0C
State=0

Control574
Name=LabJAVA_AES_KIK0D
State=0

Control575
Name=EditJAVA_AES_0348_KIK00
State=0
Value=

Control576
Name=EditJAVA_AES_0348_KIK01
State=0
Value=

Control577
Name=EditJAVA_AES_0348_KIK02
State=0
Value=

Control578
Name=EditJAVA_AES_0348_KIK03
State=0
Value=

Control579
Name=EditJAVA_AES_0348_KIK04
State=0
Value=

Control580
Name=EditJAVA_AES_0348_KIK05
State=0
Value=

Control581
Name=EditJAVA_AES_0348_KIK06
State=0
Value=

Control582
Name=EditJAVA_AES_0348_KIK07
State=0
Value=

Control583
Name=EditJAVA_AES_0348_KIK0F
State=0
Value=

Control584
Name=EditJAVA_AES_0348_KIK0E
State=0
Value=

Control585
Name=EditJAVA_AES_0348_KIK0D
State=0
Value=

Control586
Name=EditJAVA_AES_0348_KIK0C
State=0
Value=

Control587
Name=EditJAVA_AES_0348_KIK0B
State=0
Value=

Control588
Name=EditJAVA_AES_0348_KIK0A
State=0
Value=

Control589
Name=EditJAVA_AES_0348_KIK09
State=0
Value=

Control590
Name=EditJAVA_AES_0348_KIK08
State=0
Value=

Control591
Name=ButJava_AES_KIK_SAME
State=-1

Control592
Name=TabSheet4

Control593
Name=Grp_JAVA_Other
State=-1

Control594
Name=Label41
State=-1

Control595
Name=EditJAVA_HTTPS_PS_KEY
State=-1
Value=

Control596
Name=TabSheet5

Control597
Name=GrpPKCS
State=0

Control598
Name=GrpPKCS_AID
State=0

Control599
Name=LabPKCS_AID_00
State=-1

Control600
Name=LabPKCS_AID_01
State=-1

Control601
Name=LabPKCS_AID_02
State=-1

Control602
Name=LabPKCS_AID_03
State=-1

Control603
Name=LabPKCS_AID_04
State=-1

Control604
Name=LabPKCS_AID_05
State=-1

Control605
Name=LabPKCS_AID_06
State=-1

Control606
Name=LabPKCS_AID_07
State=-1

Control607
Name=LabPKCS_AID_0F
State=-1

Control608
Name=LabPKCS_AID_0E
State=-1

Control609
Name=LabPKCS_AID_08
State=-1

Control610
Name=LabPKCS_AID_09
State=-1

Control611
Name=LabPKCS_AID_0A
State=-1

Control612
Name=LabPKCS_AID_0B
State=-1

Control613
Name=LabPKCS_AID_0C
State=-1

Control614
Name=LabPKCS_AID_0D
State=-1

Control615
Name=Label236
State=-1

Control616
Name=EditPKCS_AID_00
State=-1
Value=

Control617
Name=EditPKCS_AID_01
State=-1
Value=

Control618
Name=EditPKCS_AID_02
State=-1
Value=

Control619
Name=EditPKCS_AID_03
State=-1
Value=

Control620
Name=EditPKCS_AID_04
State=-1
Value=

Control621
Name=EditPKCS_AID_05
State=-1
Value=

Control622
Name=EditPKCS_AID_06
State=-1
Value=

Control623
Name=EditPKCS_AID_07
State=-1
Value=

Control624
Name=EditPKCS_AID_0F
State=-1
Value=

Control625
Name=EditPKCS_AID_0E
State=-1
Value=

Control626
Name=EditPKCS_AID_0D
State=-1
Value=

Control627
Name=EditPKCS_AID_0C
State=-1
Value=

Control628
Name=EditPKCS_AID_0B
State=-1
Value=

Control629
Name=EditPKCS_AID_0A
State=-1
Value=

Control630
Name=EditPKCS_AID_09
State=-1
Value=

Control631
Name=EditPKCS_AID_08
State=-1
Value=

Control632
Name=CombPKCS_AID_Num
State=-1
Value=-1

Control633
Name=GrpPKCS_HASH
State=0

Control634
Name=LabPKCS_HASH_00
State=-1

Control635
Name=LabPKCS_HASH_01
State=-1

Control636
Name=LabPKCS_HASH_02
State=-1

Control637
Name=LabPKCS_HASH_03
State=-1

Control638
Name=LabPKCS_HASH_04
State=-1

Control639
Name=LabPKCS_HASH_05
State=-1

Control640
Name=LabPKCS_HASH_06
State=-1

Control641
Name=LabPKCS_HASH_07
State=-1

Control642
Name=LabPKCS_HASH_0F
State=-1

Control643
Name=LabPKCS_HASH_0E
State=-1

Control644
Name=LabPKCS_HASH_08
State=-1

Control645
Name=LabPKCS_HASH_09
State=-1

Control646
Name=LabPKCS_HASH_0A
State=-1

Control647
Name=LabPKCS_HASH_0B
State=-1

Control648
Name=LabPKCS_HASH_0C
State=-1

Control649
Name=LabPKCS_HASH_0D
State=-1

Control650
Name=Label237
State=-1

Control651
Name=EditPKCS_HASH_00
State=-1
Value=

Control652
Name=EditPKCS_HASH_01
State=-1
Value=

Control653
Name=EditPKCS_HASH_02
State=-1
Value=

Control654
Name=EditPKCS_HASH_03
State=-1
Value=

Control655
Name=EditPKCS_HASH_04
State=-1
Value=

Control656
Name=EditPKCS_HASH_05
State=-1
Value=

Control657
Name=EditPKCS_HASH_06
State=-1
Value=

Control658
Name=EditPKCS_HASH_07
State=-1
Value=

Control659
Name=EditPKCS_HASH_0F
State=-1
Value=

Control660
Name=EditPKCS_HASH_0E
State=-1
Value=

Control661
Name=EditPKCS_HASH_0D
State=-1
Value=

Control662
Name=EditPKCS_HASH_0C
State=-1
Value=

Control663
Name=EditPKCS_HASH_0B
State=-1
Value=

Control664
Name=EditPKCS_HASH_0A
State=-1
Value=

Control665
Name=EditPKCS_HASH_09
State=-1
Value=

Control666
Name=EditPKCS_HASH_08
State=-1
Value=

Control667
Name=CombPKCS_HASH_Num
State=-1
Value=-1

Control668
Name=StatusBar

Control669
Name=WebBrowser1

Control670
Name=MemoDownLoad
State=-1
Value=

Control671
Name=STextDownLoad

Control672
Name=OpenDialog1

Control673
Name=SaveDialog1

Control674
Name=TimerDownLoad


CardInfo.Code=LY14
CardInfo.Name=LTE
CardInfo.Func=LTE+GSM
CardInfo.Desc=LTE(LY14):LTE+GSM
CardInfo.ATR={ATR}
CardInfo.AID_USIM=A0000000871002FF86FF0389FFFFFFFF
CardInfo.AID_CSIM=
CardInfo.GSM=-1
CardInfo.WCDMA=-1
CardInfo.LTE=-1
CardInfo.CDMA1X=0
CardInfo.EVDO=0
CardInfo.CSIM=0
CardInfo.Alg_Comp128_1=0
CardInfo.Alg_Comp128_2=0
CardInfo.Alg_Comp128_3=0
CardInfo.Alg_MLG=-1
CardInfo.Alg_XOR=0
CardInfo.ChangeADM=-1
"""


def generate_grsp(sim: dict[str, Any]) -> str:
    """Generate full GRSIMWrite .grsp file (all 675 controls) from SIM profile."""
    imsi15 = sim.get("imsi", "310410000000001")
    imsi18 = "80" + imsi15[0] + imsi15

    mcc  = sim.get("mcc", "310")
    mnc  = sim.get("mnc", "410")
    plmn = mcc + mnc
    oplmn = f"{plmn}:4000; {plmn}:8000; {plmn}:0080"

    return _TEMPLATE.format(
        ICCID  = sim.get("_iccid",  f"8901{mcc}{mnc}000000000"),
        PIN1   = sim.get("_pin1",   "1234"),
        PUK1   = sim.get("_puk1",   "88888888"),
        ADM    = sim.get("_adm",    "3838383838383838"),
        ATR    = sim.get("_atr",    "3B9F95801FC78031A073B6A10067CF3215CA9CD70920"),
        IMSI15 = imsi15,
        IMSI18 = imsi18,
        KI     = sim.get("ki",  "").upper(),
        OPC    = sim.get("opc", "").upper(),
        SPN    = sim.get("carrier", "Custom"),
        PLMN   = plmn,
        OPLMN  = oplmn,
        MSISDN = sim.get("_msisdn", ""),
    )


def export_grsp(sim: dict[str, Any], output_dir: str) -> str:
    """Write .grsp file for GRSIMWrite. Returns path."""
    os.makedirs(output_dir, exist_ok=True)
    safe_name = sim.get("id", "sim").replace("/", "_")
    path = os.path.join(output_dir, f"{safe_name}.grsp")
    with open(path, "w", encoding="utf-8", newline="\r\n") as f:
        f.write(generate_grsp(sim))
    return path
