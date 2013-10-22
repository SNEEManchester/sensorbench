load 'gnuplot/init.gnuplot'

set terminal pdf enhanced color dashed
set out PDF_DIR.'exp2a-freshness-OD-LR-only.pdf'

set style data histogram
set style histogram cluster gap 1
set style fill pattern border -1
set boxwidth 0.9

set xlabel "Network Layout"
set ylabel "Delivery Delay (s)"
set key center left

set yrange [0:]
set datafile missing '?'
set datafile separator ","

plot CSV_DIR.'exp2a-OD2-results-avg.csv' using FRESHNESS_COL:xtic(XVAL_COL) title 'OD' linetype 3 linecolor rgb "green" linewidth 3 fill solid, \
     CSV_DIR.'exp2a-LR-results-avg.csv' using FRESHNESS_COL:xtic(XVAL_COL) title 'LR' linetype 7 linecolor rgb "black" linewidth 3 fill pattern 4




