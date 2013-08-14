
set terminal pdf enhanced color
set out 'exp0-output-rate.pdf'

set auto x
set auto y
set style data linespoints
set pointsize 1.5
set xlabel "Acquisition Interval (s)"
set ylabel "Output Rate (tuples/s)"
set key center right
set style histogram cluster gap 1
set style fill pattern border -1
set boxwidth 0.9 absolute
set yrange [0:]
set xtics
set datafile missing '?'
set datafile separator ","

plot 'exp0a-MHOSC-results.csv' using 12:22 title 'MHOSC', 'exp0b-INSNEE-results.csv' using 12:22 title 'SNEE', 'exp0a-INSNEE-results.csv' using 12:22 title 'SNEE*'

#set term png
#set out 'exp0-output-rate.png'
#plot 'exp0a-MHOSC-results.csv' using 12:22 title 'MHOSC', 'exp0b-INSNEE-results.csv' using 12:22 title 'SNEE', 'exp0a-INSNEE-results.csv' using 12:22 title 'SNEE*'

