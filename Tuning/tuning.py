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
from noisyopt import minimizeCompass, minimizeSPSA
from termcolor import colored

# for all methods
threads = 7
ngames = 50

# for naive method
nloops = 100
factor = 0.2

if platform.system() == 'Windows':
   cutechess_cli_path = "\"C:\Program Files (x86)\cutechess\cutechess-cli.exe\""
else:
   cutechess_cli_path = "/ssd/cutechess/projects/cli/cutechess-cli"

# The engine whose parameters will be optimized
engine = 'conf=minic_dev_uci'

# Format for the commands that are sent to the engine
engine_param_cmd = ' option.{name}={value}'

# A pool of opponents for the engine. 
opponents = [ 'conf=minic_dev_uci' ]

# Additional cutechess-cli options, eg. time control and opening book
options = '-each tc=0.5+0.02 -openings file=/ssd/Minic/Book_and_Test/OpeningBook/Hert500.pgn format=pgn order=random plies=24 -draw movenumber=80 movecount=5 score=5 -resign movecount=5 score=600 -pgnout out.pgn'

# parameters to optimize
params = [
  #["staticNullMoveMaxDepth0", 0, 15, 6],
  #["staticNullMoveMaxDepth1", 0, 15, 6],
  #["staticNullMoveDepthCoeff0", 0, 300, 80],
  #["staticNullMoveDepthCoeff1", 0, 300, 80],
  #["staticNullMoveDepthInit0", 0, 300, 0],
  #["staticNullMoveDepthInit1", 0, 300, 0],
  
  #["PawnValueMG"  , 0 , 2000, 500 ],
  #["PawnValueEG"  , 0 , 2000, 500 ],
  #["KnightValueMG", 0 , 2000, 500 ],
  #["KnightValueEG", 0 , 2000, 500 ],
  #["BishopValueMG", 0 , 2000, 500 ],
  #["BishopValueEG", 0 , 2000, 500 ],
  #["RookValueMG"  , 0 , 2000, 500 ],
  #["RookValueEG"  , 0 , 2000, 500 ],
  #["QueenValueMG" , 0 , 2000, 500 ],
  #["QueenValueEG" , 0 , 2000, 500 ],
  
  #["razoringMarginDepthCoeff0", 0, 500, 0],
  #["razoringMarginDepthCoeff1", 0, 500, 0],
  #["razoringMarginDepthInit0", 0, 800, 200],
  #["razoringMarginDepthInit1", 0, 800, 200],
  #["razoringMaxDepth0", 0, 15, 3],
  #["razoringMaxDepth1", 0, 15, 3],

  ["historyPruningMaxDepth", 1, 15, 3],
  ["historyPruningThresholdInit", -500, 500, 0],
  ["historyPruningThresholdDepth", -500, 500, 0],
  ["CMHMaxDepth", 0, 15, 4],

  #["failHighReductionThresholdInit0", 0, 300, 117],
  #["failHighReductionThresholdInit1", 0, 300, 93],
  #["failHighReductionThresholdDepth0", 0, 500, 217],
  #["failHighReductionThresholdDepth1", 0, 500, 145]
]

def run_one(i,fcp,scp,ngames):

   # Choose the engine's playing side (color) based on i
   if i % 2 != 0:
       fcp, scp = scp, fcp

   cutechess_args = '-engine %s -engine %s %s' % (fcp, scp, options)
   command = '%s %s' % (cutechess_cli_path, cutechess_args)

   print("Running game {}/{}   \r".format(i+1,ngames), end='')
         
   # Run cutechess-cli and wait for it to finish
   process = Popen(command, shell = True, stdout = PIPE, stderr = PIPE)
   output, err = process.communicate()
   if process.returncode != 0:
       sys.stderr.write('failed to execute command: %s\n' % command)
       return None

   # track down time forfeit
   if "time" in str(output):
       print(colored(output,'red'))

   # Convert Cutechess-cli's result into +1 0 -1
   # Note that only one game is played
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
    #print("All result {}".format(results))

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

def noisy_opt():
    bounds = [ [params[i][1] , params[i][2]] for i in range(len(params))]
    x0 = np.array([params[i][3] for i in range(len(params))])
                   
    res = minimizeCompass(obj_func_one, bounds=bounds, x0=x0, deltatol=0.1, paired=False)
    print(res)

    #res = minimizeSPSA(obj_func_one, bounds=bounds, x0=x0, niter=100, paired=False)
    #print(res)
   
def naive():
    
    for k in range(1,nloops):

       delta = [random.randint(-100,100) for i in range(len(params))]  # random
       print("Loop {}/{}, current params {}, delta (% of 1/10th of range) {}".format(k,nloops,params,delta))
        
       # configure engine
       fcp = engine
       scp = opponents[random.getrandbits(16) % len(opponents)]

       # force params to be evaluated
       for i in range(len(params)):
          delta[i] = (params[i][2] - params[i][1])*delta[i]/1000 # delta in [-100 ; 100], so here 1/10th of the allowed interval
          if int(delta[i]) == 0: # always move ...
              delta[i] = 1 if delta[i]>0 else -1
          delta[i] = int(delta[i])
          value = min(params[i][2],max(params[i][1],params[i][3]+delta[i]))
          print(params[i][0] + " delta : " + str(delta[i]) + " value : " + str(value))
          initstr = engine_param_cmd.format(name = params[i][0], value = value)
          fcp += ' initstr="%s"' % initstr
  
       print("Starting games ({})...".format(ngames))
       result,los,elo = run(ngames,threads,fcp,scp)
       
       print("Global result {}".format(result))
       
       # update values    
       if result > 0:
           print("Good !")
           for i in range(len(params)):
              d = int(delta[i]*factor*(1.-los))
              if d == 0:
                 d = 1 if delta[i]>0 else -1
              params[i][3] = min(params[i][2],max(params[i][1],params[i][3]+d))
       elif result < 0:
           print("Bad ...")
       else:
           pass    

def main(argv = None):
    if argv is None:
        argv = sys.argv[1:]

    #naive()
    #noisy_opt()
    PSO()

if __name__ == "__main__":
    sys.exit(main())
