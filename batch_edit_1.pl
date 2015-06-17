$t1=time();

open(F, "files_to_be_edited_1.txt");
while($line=<F>)
{
	chomp $line;
	#system("python multiple_files.py /Users/bozelosp/Dropbox/remod/hippocampal_ca3_pyramidal/ $line");
	system("python second_run.py /Users/bozelosp/Dropbox/remod/hippocampal_ca3_pyramidal/ $line who_random_apical 30 none remove none none none none");
}

$t2=time();

$dt=$t2-$t1;

print "Elapsed time: $dt seconds\n";