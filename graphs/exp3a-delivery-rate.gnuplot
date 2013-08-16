
load 'init.gnuplot'

set terminal pdf enhanced color
set out 'exp3a-delivery-rate.pdf'

set auto x
set auto y
set style data linespoints
set pointsize 1.5
set xlabel "Network Density"
set ylabel "Tuple Delivery Rate (delivered/acquired)"
set key center right
set style histogram cluster gap 1
set style fill pattern border -1
set boxwidth 0.9 absolute
set yrange [0:1]
set xtics
set datafile missing '?'
set datafile separator ","

#plot 'exp1a-MHOSC-results.csv' using 13:23 title 'MHOSC', 
plot 'exp3a-INSNEE-results.csv' using XVAL_COL:(stringcolumn(TASK_COL) eq 'raw'? column(DELIVERY_RATE_COL):1/0) title 'SNEE raw', \
     'exp3a-INSNEE-results.csv' using XVAL_COL:(stringcolumn(TASK_COL) eq 'corr1'? column(DELIVERY_RATE_COL):1/0) title 'SNEE corr1', \
     'exp3a-MHOSC-results.csv' using XVAL_COL:DELIVERY_RATE_COL title 'MHOSC'
