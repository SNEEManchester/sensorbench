load 'gnuplot/init.gnuplot'

set terminal pdf enhanced color dashed
set out PDF_DIR.'exp4a-output-rate.pdf'

set auto x
set auto y
set style data linespoints
set pointsize 1.5
set xlabel "Acquisition interval (s)"
set ylabel "Output Rate (tuples/s)"
set key center right
set style histogram cluster gap 1
set style fill pattern border -1
set boxwidth 0.9 absolute
set yrange [0:]
set xtics
set datafile missing '?'
set datafile separator ","

plot CSV_DIR.'exp4a-INSNEE-results-avg.csv' using XVAL_COL:(stringcolumn(TASK_COL) eq 'raw'? column(OUTPUT_RATE_COL):1/0) title 'SNEE Select' linestyle LS_INSNEE_RAW, \
     CSV_DIR.'exp4a-MHOSC-results-avg.csv' using XVAL_COL:OUTPUT_RATE_COL title 'MHOSC' linestyle LS_MHOSC, \
     CSV_DIR.'exp4a-OD2-results-avg.csv' using XVAL_COL:OUTPUT_RATE_COL title 'OD2' linestyle LS_OD2, \
     CSV_DIR.'exp4a-LR-results-avg.csv' using XVAL_COL:OUTPUT_RATE_COL title 'LR' linestyle LS_LR


