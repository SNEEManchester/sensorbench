
if [ $1 == "2a" ]; then
	python fixExp2.py
fi

gnuplot < gnuplot/exp$1-delivery-rate.gnuplot
gnuplot	< gnuplot/exp$1-output-rate.gnuplot
gnuplot < gnuplot/exp$1-freshness.gnuplot
gnuplot < gnuplot/exp$1-sum-6m-energy.gnuplot
gnuplot < gnuplot/exp$1-lifetime.gnuplot


