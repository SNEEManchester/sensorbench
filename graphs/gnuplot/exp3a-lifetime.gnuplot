load 'gnuplot/init.gnuplot'

set terminal pdf enhanced color
set out PDF_DIR.'exp3a-lifetime.pdf'

set auto x
set auto y
set style data linespoints
set pointsize 1.5
set xlabel "Network Density"
set ylabel "Lifetime (days)"
set key center right
set style histogram cluster gap 1
set style fill pattern border -1
set boxwidth 0.9 absolute
set yrange [0:]
set xtics
set datafile missing '?'
set datafile separator ","

plot CSV_DIR.'exp3a-INSNEE-results-avg.csv' using XVAL_COL:(stringcolumn(TASK_COL) eq 'raw'? column(LIFETIME_COL):1/0) title 'SNEE Select' linetype LT_INSNEE_RAW, \
     CSV_DIR.'exp3a-INSNEE-results-avg.csv' using XVAL_COL:(stringcolumn(TASK_COL) eq 'corr1'? column(LIFETIME_COL):1/0) title 'SNEE Join' linetype LT_INSNEE_CORR1, \
     CSV_DIR.'exp3a-MHOSC-results-avg.csv' using XVAL_COL:LIFETIME_COL title 'MHOSC' linetype LT_MHOSC, \
     CSV_DIR.'exp3a-OD2-results-avg.csv' using XVAL_COL:LIFETIME_COL title 'OD2' linetype LT_OD2, \
     CSV_DIR.'exp3a-LR-results-avg.csv' using XVAL_COL:LIFETIME_COL title 'LR' linetype LT_LR


