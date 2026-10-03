"""Number format constants for Excel exports per 11_EXCEL_OUTPUT_SPEC.md §3.6."""

# Formats dictionary
XLS_FMT_001 = '₹ #,##,##,##0.00;(₹ #,##,##,##0.00);₹ 0.00'   # MONEY_IN - Indian grouping
XLS_FMT_002 = '₹ #,##0.00;(₹ #,##0.00);₹ 0.00'               # MONEY_INTL - International grouping
XLS_FMT_003 = '#,##0.00;(#,##0.00);0.00'                     # MONEY_SCALED
XLS_FMT_004 = '0.0%;(0.0%);0.0%'                             # PCT_1DP
XLS_FMT_005 = '+0.0" pp";-0.0" pp";0.0" pp"'                 # PP_1DP
XLS_FMT_006 = '0.00;(0.00);0.00'                             # RATIO_2DP
XLS_FMT_007 = '#,##0;(#,##0);0'                              # COUNT_INT
XLS_FMT_008 = 'dd-mm-yyyy'                                   # DATE_DMY
XLS_FMT_009 = 'dd-mm-yyyy hh:mm'                             # TS_DMY
XLS_FMT_010 = '@'                                            # TEXT
XLS_FMT_011 = '@'                                            # CODE
XLS_FMT_012 = '@'                                            # HASH
XLS_FMT_013 = '0" d"'                                        # DAYS
XLS_FMT_014 = '@'                                            # LABEL
XLS_FMT_015 = '+0.0" bp";-0.0" bp";0.0" bp"'                 # BPS_1DP

# Aliases for readability
MONEY_IN = XLS_FMT_001
MONEY_INTL = XLS_FMT_002
MONEY_SCALED = XLS_FMT_003
PCT_1DP = XLS_FMT_004
PP_1DP = XLS_FMT_005
RATIO_2DP = XLS_FMT_006
COUNT_INT = XLS_FMT_007
DATE_DMY = XLS_FMT_008
TS_DMY = XLS_FMT_009
TEXT = XLS_FMT_010
CODE = XLS_FMT_011
HASH = XLS_FMT_012
DAYS = XLS_FMT_013
LABEL = XLS_FMT_014
BPS_1DP = XLS_FMT_015
