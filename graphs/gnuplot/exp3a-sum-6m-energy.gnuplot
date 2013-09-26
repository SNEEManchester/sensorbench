load 'gnuplot/init.gnuplot'

set terminal pdf enhanced color
set out PDF_DIR.'exp3a-sum-6m-energy.pdf'

set auto x
set auto y
set style data linespoints
set pointsize 1.5
set xlabel "Network Density"
set ylabel "Total Network Energy over 6 Months (J)"
set key center right
set style histogram cluster gap 1
set style fill pattern border -1
set boxwidth 0.9 absolute
set yrange [0:]
set xtics
set datafile missing '?'
set datafile separator ","

#MHOSC
plot CSV_DIR.'exp3a-INSNEE-results.csv' using XVAL_COL:(stringcolumn(TASK_COL) eq 'raw'? column(SUM_6M_ENERGY_COL):1/0) title 'SNEE raw', \
     CSV_DIR.'exp3a-INSNEE-results.csv' using XVAL_COL:(stringcolumn(TASK_COL) eq 'corr1'? column(SUM_6M_ENERGY_COL):1/0) title 'SNEE corr1', \
     CSV_DIR.'exp3a-MHOSC-results.csv' using XVAL_COL:SUM_6M_ENERGY_COL title 'MHOSC'
