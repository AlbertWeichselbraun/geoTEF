set datafile separator ","
set xlabel "w_contains"
set ylabel "w_partOf"
set zlabel "utility"
set terminal postscript
set output '3dutility.ps'

splot '../results/geotagger_results_C5000.csv_3d.dat' title ""

