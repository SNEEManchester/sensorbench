
load 'init.gnuplot'

set terminal pdf enhanced color
set out 'exp6a-lifetime.pdf'

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

#MHOSC
plot 'exp6a-INSNEE-results.csv' using XVAL_COL:(stringcolumn(TASK_COL) eq 'raw'? column(LIFETIME_COL):1/0) title 'SNEE raw', \
     'exp6a-INSNEE-results.csv' using XVAL_COL:(stringcolumn(TASK_COL) eq 'aggr'? column(LIFETIME_COL):1/0) title 'SNEE aggr'
#, \
#     'exp6a-INSNEE-results.csv' using XVAL_COL:(stringcolumn(TASK_COL) eq 'OD'? column(LIFETIME_COL):1/0) title 'SNEE OD'
