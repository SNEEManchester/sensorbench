
load 'init.gnuplot'

set terminal pdf enhanced color
set out 'exp2a-lifetime.pdf'

set style fill pattern border -1
set boxwidth 2

set auto x
set auto y
set xlabel "Network Layout"
set ylabel "Lifetime (days)"
set key top right

set yrange [0:]
set xtics ("linear" 12, "grid" 22, "random" 32)
set datafile missing '?'
set datafile separator ","

plot 'exp2a-INSNEE-results.csv' using XVAL_COL:(stringcolumn(TASK_COL) eq 'raw'? column(LIFETIME_COL):1/0) title 'SNEE raw' with boxes, \
     'exp2a-INSNEE-results.csv' using XVAL_COL:(stringcolumn(TASK_COL) eq 'aggr'? column(LIFETIME_COL):1/0) title 'SNEE aggr' with boxes, \
     'exp2a-MHOSC-results.csv' using XVAL_COL:LIFETIME_COL title 'MHOSC' with boxes

