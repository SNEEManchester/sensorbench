
load 'init.gnuplot'

set terminal pdf enhanced color
set out 'exp5a-output-rate.pdf'

set auto x
set auto y
set style data linespoints
set pointsize 1.5
set xlabel "Proportion of Source Nodes in Network (%)"
set ylabel "Output Rate (tuples/s)"
set key center right
set style histogram cluster gap 1
set style fill pattern border -1
set boxwidth 0.9 absolute
set yrange [0:]
set xtics
set datafile missing '?'
set datafile separator ","

plot 'exp5a-INSNEE-results.csv' using XVAL_COL:(stringcolumn(TASK_COL) eq 'raw'? column(OUTPUT_RATE_COL):1/0) title 'SNEE raw', \
     'exp5a-MHOSC-results.csv' using XVAL_COL:OUTPUT_RATE_COL title 'MHOSC'
