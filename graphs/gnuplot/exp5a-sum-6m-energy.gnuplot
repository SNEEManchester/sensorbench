load 'gnuplot/init.gnuplot'

set terminal pdf enhanced color dashed
set out PDF_DIR.'exp5a-sum-6m-energy.pdf'

set auto x
set auto y
set style data linespoints
set pointsize 1.5
set xlabel "Proportion of Source Nodes in Network (%)"
set ylabel "Total Network Energy over 6 Months (J)"
set key top left
set style histogram cluster gap 1
set style fill pattern border -1
set boxwidth 0.9 absolute
set yrange [0:]
set xrange [20:105]
set xtics
set datafile missing '?'
set datafile separator ","

plot CSV_DIR.'exp5a-INSNEE-results-avg.csv' using XVAL_COL:(stringcolumn(TASK_COL) eq 'raw'? column(SUM_6M_ENERGY_COL):1/0) title 'SNEE Select' linestyle LS_INSNEE_RAW, \
     CSV_DIR.'exp5a-MHOSC-results-avg.csv' using XVAL_COL:SUM_6M_ENERGY_COL title 'MHOSC' linestyle LS_MHOSC, \
     CSV_DIR.'exp5a-OD2-results-avg.csv' using XVAL_COL:SUM_6M_ENERGY_COL title 'OD' linestyle LS_OD, \
     CSV_DIR.'exp5a-LR-results-avg.csv' using XVAL_COL:SUM_6M_ENERGY_COL title 'LR' linestyle LS_LR

