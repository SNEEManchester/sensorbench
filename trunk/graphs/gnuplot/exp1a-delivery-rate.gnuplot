load 'gnuplot/init.gnuplot'

set terminal pdf enhanced color dashed
set out PDF_DIR.'exp1a-delivery-rate.pdf'

set auto x
set auto y
set style data linespoints
set pointsize 1.5
set xlabel "Network Size"
set ylabel "Delivery Fraction (%)"
set key center right
set style histogram cluster gap 1
set style fill pattern border -1
set boxwidth 0.9 absolute
set yrange [0:110]
set xtics
set datafile missing '?'
set datafile separator ","

plot CSV_DIR.'exp1a-INSNEE-results-avg.csv' using XVAL_COL:(stringcolumn(TASK_COL) eq 'raw'? column(DELIVERY_RATE_COL):1/0) title 'SNEE Select' linestyle LS_INSNEE_RAW, \
     CSV_DIR.'exp1a-INSNEE-results-avg.csv' using XVAL_COL:(stringcolumn(TASK_COL) eq 'aggr'? column(DELIVERY_RATE_COL):1/0) title 'SNEE Aggr' linestyle LS_INSNEE_AGGR, \
     CSV_DIR.'exp1a-MHOSC-results-avg.csv' using XVAL_COL:DELIVERY_RATE_COL title 'MHOSC' linestyle LS_MHOSC, \
     CSV_DIR.'exp1a-OD2-results-avg.csv' using XVAL_COL:DELIVERY_RATE_COL title 'OD2' linestyle LS_OD2, \
     CSV_DIR.'exp1a-LR-results-avg.csv' using XVAL_COL:DELIVERY_RATE_COL title 'LR' linestyle LS_LR



