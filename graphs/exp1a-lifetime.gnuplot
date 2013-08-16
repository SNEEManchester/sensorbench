
load 'init.gnuplot'

set terminal pdf enhanced color
set out 'exp1a-lifetime.pdf'

set auto x
set auto y
set style data linespoints
set pointsize 1.5
set xlabel "Network Size"
set ylabel "Lifetime (days)"
set key bottom right
set style histogram cluster gap 1
set style fill pattern border -1
set boxwidth 0.9 absolute
set yrange [0:]
set xtics
set datafile missing '?'
set datafile separator ","

#MHOSC
plot 'exp1a-INSNEE-results.csv' using XVAL_COL:(stringcolumn(TASK_COL) eq 'raw'? column(LIFETIME_COL):1/0) title 'SNEE raw', \
     'exp1a-INSNEE-results.csv' using XVAL_COL:(stringcolumn(TASK_COL) eq 'aggr'? column(LIFETIME_COL):1/0) title 'SNEE aggr', \
     'exp1a-MHOSC-results.csv' using XVAL_COL:LIFETIME_COL title 'MHOSC'

