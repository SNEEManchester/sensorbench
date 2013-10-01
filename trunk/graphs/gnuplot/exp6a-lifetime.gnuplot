load 'gnuplot/init.gnuplot'

set terminal pdf enhanced color
set out PDF_DIR.'exp6a-lifetime.pdf'

set auto x
set auto y
set style data linespoints
set pointsize 1.5
set xlabel "Radio Packet Loss Rate (%)"
set ylabel "Lifetime (days)"
set key center right
set style histogram cluster gap 1
set style fill pattern border -1
set boxwidth 0.9 absolute
set yrange [0:]
set xtics
set datafile missing '?'
set datafile separator ","

plot CSV_DIR.'exp6a-INSNEE-results-avg.csv' using XVAL_COL:(stringcolumn(TASK_COL) eq 'raw'? column(LIFETIME_COL):1/0) title 'SNEE raw', \
     CSV_DIR.'exp6a-INSNEE-results-avg.csv' using XVAL_COL:(stringcolumn(TASK_COL) eq 'aggr'? column(LIFETIME_COL):1/0) title 'SNEE aggr', \
     CSV_DIR.'exp6a-MHOSC-results-avg.csv' using XVAL_COL:LIFETIME_COL title 'MHOSC'
#, \
#     CSV_DIR.'exp6a-INSNEE-results-avg.csv' using XVAL_COL:(stringcolumn(TASK_COL) eq 'OD'? column(LIFETIME_COL):1/0) title 'SNEE OD'

