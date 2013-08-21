load 'gnuplot/init.gnuplot'

set terminal pdf enhanced color
set out PDF_DIR.'exp5a-delivery-rate.pdf'

set auto x
set auto y
set style data linespoints
set pointsize 1.5
set xlabel "Proportion of Source Nodes in Network (%)"
set ylabel "Tuple Delivery Rate (delivered/acquired)"
set key center right
set style histogram cluster gap 1
set style fill pattern border -1
set boxwidth 0.9 absolute
set yrange [0:1]
set xtics
set datafile missing '?'
set datafile separator ","

plot CSV_DIR.'exp5a-INSNEE-results.csv' using XVAL_COL:(stringcolumn(TASK_COL) eq 'raw'? column(DELIVERY_RATE_COL):1/0) title 'SNEE raw', \
     CSV_DIR.'exp5a-MHOSC-results.csv' using XVAL_COL:DELIVERY_RATE_COL title 'MHOSC'

