set datafile separator ","
set xlabel "w_partOf"
set ylabel "utility"
set terminal postscript
set output '2dutility.ps'

plot '../results/geotagger_results_C10000.csv_2d.dat' title "Population > 10,000" with lines,  '../results/geotagger_results_C5000.csv_2d.dat' title "Population > 5,000" with lines



