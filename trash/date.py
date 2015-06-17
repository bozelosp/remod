import datetime

now = datetime.datetime.now()

print "This file was modified on" + str(now.strftime("%Y-%m-%d %H:%M"))
