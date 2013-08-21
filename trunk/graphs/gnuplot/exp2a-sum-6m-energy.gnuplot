load 'gnuplot/init.gnuplot'

set terminal pdf enhanced color
set out PDF_DIR.'exp2a-sum-6m-energy.pdf'

set style fill pattern border -1
set boxwidth 2

set auto x
set auto y
set xlabel "Network Layout"
set ylabel "Total Network Energy over 6 Months (J)"
set key top right

set yrange [0:]
set xtics ("linear" 12, "grid" 22, "random" 32)
set datafile missing '?'
set datafile separator ","

plot CSV_DIR.'exp2a-INSNEE-results.csv' using XVAL_COL:(stringcolumn(TASK_COL) eq 'raw'? column(SUM_6M_ENERGY_COL):1/0) title 'SNEE raw' with boxes, \
     CSV_DIR.'exp2a-INSNEE-results.csv' using XVAL_COL:(stringcolumn(TASK_COL) eq 'aggr'? column(SUM_6M_ENERGY_COL):1/0) title 'SNEE aggr' with boxes, \
     CSV_DIR.'exp2a-MHOSC-results.csv' using XVAL_COL:SUM_6M_ENERGY_COL title 'MHOSC' with boxes

