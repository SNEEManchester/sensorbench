load 'gnuplot/init.gnuplot'

set terminal pdf enhanced color dashed
set out PDF_DIR.'exp7-freshness.pdf'

set auto x
set auto y
set style data linespoints
set pointsize 1.5
set xlabel "Acquisition interval (s)"
set ylabel "Delivery Delay (s)"
set key center right
set style histogram cluster gap 1
set style fill pattern border -1
set boxwidth 0.9 absolute
set yrange [0:]
set xtics
set datafile missing '?'
set datafile separator ","

plot CSV_DIR.'exp7-INSNEE-results-avg.csv' using XVAL_COL:(stringcolumn(TASK_COL) eq 'raw'? column(FRESHNESS_COL):1/0) title 'SNEE Select' linestyle LS_INSNEE_RAW, \
     CSV_DIR.'exp7-INSNEE-results-avg.csv' using XVAL_COL:(stringcolumn(TASK_COL) eq 'aggr'? column(FRESHNESS_COL):1/0) title 'SNEE Aggr' linestyle LS_INSNEE_AGGR, \
     CSV_DIR.'exp7-INSNEE-results-avg.csv' using XVAL_COL:(stringcolumn(TASK_COL) eq 'corr1'? column(FRESHNESS_COL):1/0) title 'SNEE Join' linestyle LS_INSNEE_CORR1, \
     CSV_DIR.'exp7-INSNEE-results-avg.csv' using XVAL_COL:(stringcolumn(TASK_COL) eq 'corr2'? column(FRESHNESS_COL):1/0) title 'SNEE Join2' linestyle LS_INSNEE_CORR2, \
     CSV_DIR.'exp7-MHOSC-results-avg.csv' using XVAL_COL:FRESHNESS_COL title 'MHOSC' linestyle LS_MHOSC, \
     CSV_DIR.'exp7-OD2-results-avg.csv' using XVAL_COL:FRESHNESS_COL title 'OD' linestyle LS_OD, \
     CSV_DIR.'exp7-LR-results-avg.csv' using XVAL_COL:FRESHNESS_COL title 'LR' linestyle LS_LR

