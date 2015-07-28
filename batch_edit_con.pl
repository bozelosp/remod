$t1=time();

open(F, "files_to_be_edited_1.txt");
while($line=<F>)
{
	chomp $line;
	system("python second_run.py /Users/bozelosp/Dropbox/remod/swc/ m-2.CNG.swc who_apical_terminal 0 none none none none percent 50");
}

$t2=time();

$dt=$t2-$t1;

print "Elapsed time: $dt seconds\n";