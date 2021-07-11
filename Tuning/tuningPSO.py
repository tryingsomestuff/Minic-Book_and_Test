#!/usr/bin/python
# -*- coding: utf-8 -*-

from subprocess import Popen, PIPE
import sys
import platform
import random
import math
import multiprocessing
from joblib import Parallel, delayed
import pyswarms as ps
from random import randrange
from pyswarms.utils.plotters import plot_cost_history
from random import randrange
import matplotlib.pyplot as plt
import numpy as np
from termcolor import colored

threads = 8
ngames = 100

if platform.system() == 'Windows':
   cutechess_cli_path = "\"C:\Program Files (x86)\cutechess\cutechess-cli.exe\""
else:
   cutechess_cli_path = "/ssd/cutechess/projects/cli/cutechess-cli"

engine = 'conf=minic_dev_uci'

engine_param_cmd = ' option.{name}={value}'

opponents = [ 'conf=minic_dev_uci' ]

options = '-each tc=1+0.01 -openings file=/ssd/Minic/Book_and_Test/OpeningBook/Hert500.pgn format=pgn order=random plies=24 -draw movenumber=80 movecount=5 score=5 -resign movecount=5 score=600 -pgnout out.pgn'

params = [
 
  ["PawnValueMG"  , 0 , 2000, 500 ],
  ["PawnValueEG"  , 0 , 2000, 500 ],
  ["KnightValueMG", 0 , 2000, 500 ],
  ["KnightValueEG", 0 , 2000, 500 ],
  ["BishopValueMG", 0 , 2000, 500 ],
  ["BishopValueEG", 0 , 2000, 500 ],
  ["RookValueMG"  , 0 , 2000, 500 ],
  ["RookValueEG"  , 0 , 2000, 500 ],
  ["QueenValueMG" , 0 , 2000, 500 ],
  ["QueenValueEG" , 0 , 2000, 500 ],
  
]

def run_one(i,fcp,scp,ngames):

   if i % 2 != 0:
       fcp, scp = scp, fcp

   cutechess_args = '-engine %s -engine %s %s' % (fcp, scp, options)
   command = '%s %s' % (cutechess_cli_path, cutechess_args)

   print("Running game {}/{}   \r".format(i+1,ngames), end='')
         
   process = Popen(command, shell = True, stdout = PIPE)
   output = process.communicate()[0]
   if process.returncode != 0:
       sys.stderr.write('failed to execute command: %s\n' % command)
       return None

   result = -1
   for line in output.decode("utf-8").splitlines():
       if line.startswith('Finished game'):
           if line.find(": 1-0") != -1:
               result = i % 2
           elif line.find(": 0-1") != -1:
               result = (i % 2) ^ 1
           elif line.find(": 1/2-1/2") != -1:
               result = 2
           else:
               sys.stderr.write('the game did not terminate properly\n')
               return None
           break

   if result == 0:
       return 1
   elif result == 1:
       return -1
   elif result == 2:
       return 0    

def run(ngames,threads,fcp,scp):

    results = Parallel(n_jobs=threads)(delayed(run_one)(i,fcp,scp,ngames) for i in range(ngames))

    l = list(results) 
    draws = l.count(0)
    wins = l.count(1)
    losses = l.count(-1)
    mu = max(0.00001,wins + draws/2)/ngames # avoid div by zero
    elo = -math.log(1.0/mu-1.0)*400.0/math.log(10.0);
    los = .5 + .5 * math.erf((wins-losses)/math.sqrt(2.0*(wins+losses)));

    print("\nwins   {}".format(wins))
    print("draws  {}".format(draws))
    print("losses {}".format(losses))
    print(colored("elo    {}".format(elo), 'red' if elo<0 else 'green' if elo > 15 else 'yellow'))
    print("LOS    {}".format(los))

    return sum(results),los,elo

def obj_func_one(x):
   
    print("\nCurrent params {}".format([int(xx) for xx in x]))
   
    # configure engine
    fcp = engine
    scp = opponents[random.getrandbits(16) % len(opponents)]    
    
    for i in range(len(params)):
       option = engine_param_cmd.format(name = params[i][0], value = int(x[i]))
       fcp += option    
    
    return ngames - run(ngames,threads,fcp,scp)[0]

def obj_func_many(x):
    res = [None]*len(x)
    for k in range(len(x)):
       res[k] = obj_func_one(x[k])
    return res

def PSO():
    # Set-up hyperparameters
    options = {'c1': 0.5, 'c2': 0.3, 'w':0.9}
    # Call instance of PSO
    optimizer = ps.single.GlobalBestPSO(n_particles=15, dimensions=len(params), options=options, bounds=([params[i][1] for i in range(len(params))], [params[i][2] for i in range(len(params))]))
    # Perform optimization
    best_cost, best_pos = optimizer.optimize(obj_func_many, iters=1000)
    plot_cost_history(optimizer.cost_history)
    plt.show()    

def main(argv = None):
    if argv is None:
        argv = sys.argv[1:]
    PSO()

if __name__ == "__main__":
    sys.exit(main())
