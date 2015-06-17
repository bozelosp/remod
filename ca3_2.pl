$t1=time();

open(F, "homo_ca3_2.txt");
while($line=<F>)
{
	chomp $line;
	#system("python multiple_files.py /Users/bozelosp/Dropbox/remod/hippocampal_ca3_pyramidal/ $line");
	system("python second_run.py /Users/bozelosp/Dropbox/remod/homogeneous_ca3/downloads/files/ $line who_random_apical 5 none shrink percent 25 none none");
}

$t2=time();

$dt=$t2-$t1;

print "Elapsed time: $dt seconds\n";
