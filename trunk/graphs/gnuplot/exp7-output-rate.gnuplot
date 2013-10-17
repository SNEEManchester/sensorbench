load 'gnuplot/init.gnuplot'

set terminal pdf enhanced color
set out PDF_DIR.'exp7-output-rate.pdf'

set auto x
set auto y
set style data linespoints
set pointsize 1.5
set xlabel "Acquisition interval (s)"
set ylabel "Tuple Output Rate (tuples/s)"
set key center right
set style histogram cluster gap 1
set style fill pattern border -1
set boxwidth 0.9 absolute
set yrange [0:1]
set xtics
set datafile missing '?'
set datafile separator ","

plot CSV_DIR.'exp7-INSNEE-results-avg.csv' using XVAL_COL:(stringcolumn(TASK_COL) eq 'raw'? column(OUTPUT_RATE_COL):1/0) title 'SNEE Select' linetype LT_INSNEE_RAW, \
     CSV_DIR.'exp7-INSNEE-results-avg.csv' using XVAL_COL:(stringcolumn(TASK_COL) eq 'aggr'? column(OUTPUT_RATE_COL):1/0) title 'SNEE Aggr' linetype LT_INSNEE_AGGR, \
     CSV_DIR.'exp7-INSNEE-results-avg.csv' using XVAL_COL:(stringcolumn(TASK_COL) eq 'corr1'? column(OUTPUT_RATE_COL):1/0) title 'SNEE Join' linetype LT_INSNEE_CORR1, \
     CSV_DIR.'exp7-INSNEE-results-avg.csv' using XVAL_COL:(stringcolumn(TASK_COL) eq 'corr2'? column(OUTPUT_RATE_COL):1/0) title 'SNEE Join2' linetype LT_INSNEE_CORR2, \
     CSV_DIR.'exp7-MHOSC-results-avg.csv' using XVAL_COL:OUTPUT_RATE_COL title 'MHOSC' linetype LT_MHOSC, \
     CSV_DIR.'exp7-OD2-results-avg.csv' using XVAL_COL:OUTPUT_RATE_COL title 'OD2' linetype LT_OD2, \
     CSV_DIR.'exp7-LR-results-avg.csv' using XVAL_COL:OUTPUT_RATE_COL title 'LR' linetype LT_LR


