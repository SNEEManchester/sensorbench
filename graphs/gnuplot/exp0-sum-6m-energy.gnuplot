
set terminal pdf enhanced color
set out 'exp0-sum-6m-energy.pdf'

set auto x
set auto y
set style data linespoints
set pointsize 1.5
set xlabel "Acquisition Interval (s)"
set ylabel "Total Network Energy over 6 Months (J)"
set key center right
set style histogram cluster gap 1
set style fill pattern border -1
set boxwidth 0.9 absolute
set yrange [0:]
set xtics
set datafile missing '?'
set datafile separator ","

plot 'exp0a-MHOSC-results.csv' using 12:25 title 'MHOSC', 'exp0b-INSNEE-results.csv' using 12:25 title 'SNEE', 'exp0a-INSNEE-results.csv' using 12:25 title 'SNEE*'

#set term png
#set out 'exp0-sum-6m-energy.png'
#plot 'exp0a-MHOSC-results.csv' using 12:25 title 'MHOSC', 'exp0b-INSNEE-results.csv' using 12:25 title 'SNEE', 'exp0a-INSNEE-results.csv' using 12:25 title 'SNEE*'

