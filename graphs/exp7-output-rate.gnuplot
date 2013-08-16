
load 'init.gnuplot'

set terminal pdf enhanced color
set out 'exp7-output-rate.pdf'

set auto x
set auto y
set style data linespoints
set pointsize 1.5
set xlabel "Acquisition Rate (s)"
set ylabel "Tuple Output Rate (tuples/s)"
set key center right
set style histogram cluster gap 1
set style fill pattern border -1
set boxwidth 0.9 absolute
set yrange [0:1]
set xtics
set datafile missing '?'
set datafile separator ","

#plot 'exp1a-MHOSC-results.csv' using 13:23 title 'MHOSC', 
plot 'exp7-INSNEE-results.csv' using XVAL_COL:(stringcolumn(TASK_COL) eq 'raw'? column(OUTPUT_RATE_COL):1/0) title 'SNEE raw', \
     'exp7-INSNEE-results.csv' using XVAL_COL:(stringcolumn(TASK_COL) eq 'aggr'? column(OUTPUT_RATE_COL):1/0) title 'SNEE aggr', \
     'exp7-INSNEE-results.csv' using XVAL_COL:(stringcolumn(TASK_COL) eq 'corr1'? column(OUTPUT_RATE_COL):1/0) title 'SNEE corr1', \
     'exp7-INSNEE-results.csv' using XVAL_COL:(stringcolumn(TASK_COL) eq 'corr2'? column(OUTPUT_RATE_COL):1/0) title 'SNEE corr2', \
     'exp4a-MHOSC-results.csv' using XVAL_COL:OUTPUT_RATE_COL title 'MHOSC'
#, \
#     'exp7-INSNEE-results.csv' using XVAL_COL:(stringcolumn(TASK_COL) eq 'LR'? column(OUTPUT_RATE_COL):1/0) title 'SNEE LR', \
#     'exp7-INSNEE-results.csv' using XVAL_COL:(stringcolumn(TASK_COL) eq 'OD'? column(OUTPUT_RATE_COL):1/0) title 'SNEE OD'
