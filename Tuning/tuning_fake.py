#!/usr/bin/python
# -*- coding: utf-8 -*-

from subprocess import Popen, PIPE
import sys
import platform
import random
import math
import pyswarms as ps
from pyswarms.utils.plotters import plot_cost_history
from random import randrange
import matplotlib.pyplot as plt


# parameters to optimize
params = [
  ["staticNullMoveMaxDepth0", 0, 15, 6],
  ["staticNullMoveMaxDepth1", 0, 15, 6],
  ["staticNullMoveDepthCoeff0", 0, 300, 80],
  ["staticNullMoveDepthCoeff1", 0, 300, 80],
  ["staticNullMoveDepthInit0", 0, 300, 0],
  ["staticNullMoveDepthInit1", 0, 300, 0],
]

def obj_func_one_fake(x):
    return sum([ (x[i]-params[i][2]/2)*(x[i]-params[i][2]/2) + randrange(-100,1000)*params[i][2]/100 for i in range(len(x))])

def obj_func_many(x):
    res = [None]*len(x)
    for k in range(len(x)):
       res[k] = obj_func_one_fake(x[k])
    return res

def PSO():
    # Set-up hyperparameters
    options = {'c1': 0.5, 'c2': 0.3, 'w':0.9}
    # Call instance of PSO
    optimizer = ps.single.GlobalBestPSO(n_particles=15, dimensions=len(params), options=options, bounds=([params[i][1] for i in range(len(params))], [params[i][2] for i in range(len(params))]))
    # Perform optimization
    best_cost, best_pos = optimizer.optimize(obj_func_many, iters=1500)

    plot_cost_history(optimizer.cost_history)
    plt.show()

def main(argv = None):
    if argv is None:
       argv = sys.argv[1:]
        
    PSO()

if __name__ == "__main__":
    sys.exit(main())
