#!/usr/bin/env python

""" watches the computations and deletes all hanging processes """

from commands import getoutput
from sys import argv, exit
from time import ctime


def check_running_proc():
    dead  = 0
    alive = 0
    runs  = False
    out = getoutput("ps xauww")
    for line  in out.split("\n"):
        if '[python] <defunct>' in line:
            dead +=1
        if 'python ./ipm-evaluation-worker.py' in line:
            alive +=1
    return (dead, alive)


dead, alive = check_running_proc()
if dead>3 or dead>alive or len(argv)==2 and argv[1]=="test":
    f=open("/tmp/ursula.log", "a")
    f.write("%s Killing and restarting simulation (%d dead and %d alive).\n" % (ctime(), dead, alive))
    f.close()
    exit(0)
else:
    exit(1)

