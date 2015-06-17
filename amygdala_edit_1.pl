$t1=time();

open(F, "files_1.txt");
while($line=<F>)
{
	chomp $line;
	#system("python multiple_files.py /Users/bozelosp/Dropbox/remod/hippocampal_ca3_pyramidal/ $line");
	system("python second_run.py /Users/bozelosp/Dropbox/remod/amygdala_pyramidal/ $line who_random_all 11 none branch percent 30 none none");
}

$t2=time();

$dt=$t2-$t1;

print "Elapsed time: $dt seconds\n";