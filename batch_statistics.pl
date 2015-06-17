$t1=time();

open(F, "files_to_extract_statistics.txt");
while($line=<F>)
{
	chomp $line;
	system("python first_run.py /Users/bozelosp/Dropbox/remod/spyros/danzer/ $line");
	print "Hi!\n";
}

$t2=time();

$dt=$t2-$t1;

print "Elapsed time: $dt seconds\n";
