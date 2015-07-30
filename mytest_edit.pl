$t1=time();

open(F, "myfiles");
while($line=<F>)
{
	chomp $line;
	#system("python multiple_files.py /Users/bozelosp/Dropbox/remod/hippocampal_ca3_pyramidal/ $line");
	system("python second_run.py /Users/bozelosp/Downloads/CA3_cells/ $line who_random_basal 30 none extend percent 80 none none");
}

$t2=time();

$dt=$t2-$t1;

print "Elapsed time: $dt seconds\n";