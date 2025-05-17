import re
from math import cos, sin, pi, sqrt, radians, degrees
from utils import distance

fname='hi.txt'

lines=[]
for line in open(fname):
    lines.append(line.rstrip('\n'))

mylist=[]

for line in lines:
    p = re.search(r'(\d+) (\d+) (.*?) (.*?) (.*?) (.*?) (-?\d+)', line)
    if p:
        x = float(p.group(3))
        y = float(p.group(4))
        z = float(p.group(5))
        mylist.append([x, y, z])


dist_sum=[]

for i in range(len(mylist)-1):
    current = mylist[i + 1]
    next = mylist[i]
    di = distance(next[0], current[0], next[1], current[1], next[2], current[2])
    dist_sum.append(di)
    print(current, next, sum(dist_sum))


sum_dist = sum(dist_sum)

print(sum_dist)
