load 'gnuplot/init.gnuplot'

set terminal pdf enhanced color
set out PDF_DIR.'exp2a-freshness.pdf'

set style data histogram
set style histogram cluster gap 1
set style fill pattern border -1
set boxwidth 0.9

set xlabel "Network Layout"
set ylabel "Data Freshness (s)"
set key center left

set yrange [0:]
set datafile missing '?'
set datafile separator ","

plot CSV_DIR.'exp2a-INSNEE-raw-results-avg.csv' using FRESHNESS_COL:xtic(XVAL_COL) title 'SNEE raw' linetype LT_INSNEE_RAW, \
     CSV_DIR.'exp2a-INSNEE-aggr-results-avg.csv' using FRESHNESS_COL:xtic(XVAL_COL) title 'SNEE aggr' linetype LT_INSNEE_AGGR, \
     CSV_DIR.'exp2a-MHOSC-results-avg.csv' using FRESHNESS_COL:xtic(XVAL_COL) title 'MHOSC' linetype LT_MHOSC


