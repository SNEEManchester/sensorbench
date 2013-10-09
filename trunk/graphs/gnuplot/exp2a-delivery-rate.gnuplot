reset
load 'gnuplot/init.gnuplot'

set terminal pdf enhanced color
set out PDF_DIR.'exp2a-delivery-rate.pdf'

set style fill pattern border -1
dx=5.


set auto x
set auto y
set xlabel "Network Layout"
set ylabel "Tuple Delivery Rate (delivered/acquired)"
set key top right

n=3
dx=3
total_box_width_relative=0.75
d_width=(total_box_width_relative)/n
d_width2= d_width + d_width
d_width3= d_width2 + d_width 
gap_width_relative=0.3
set boxwidth total_box_width_relative/n 


set yrange [0:1]
set xrange [0.5:5]
set xtics ("linear" 1, "grid" 2, "random" 3)

plot CSV_DIR."exp2a-Delivery.data" using 1:2 with boxes title 'SNEE raw', CSV_DIR."exp2a-Delivery.data" using ($1+d_width):3 with boxes title 'SNEE aggr', CSV_DIR."exp2a-Delivery.data" using ($1+d_width2):4 title 'MHOSC' with boxes

