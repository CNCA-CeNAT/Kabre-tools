import matplotlib
matplotlib.use('Agg')

import time
import numpy as np
import matplotlib.pyplot as plt 
import sys
import modules 

import __main__ # you sure??

def dummy_setup():
    pass

def poli_growth(coefficient, order):
    return lambda c: base * c**order

class Executable:
    def __init__(self, P, setup, name='scaling_test', capture_output=False):
        self.P    = P
        self.name = name
        self.co   = capture_output
        setup()

    def run(self, c, s):
        start = time.time()
        out = modules.run(self.P(c, s), capture_output=True)
        end = time.time()
        if self.co:
            try:
                return float(out)
            except ValueError:
                raise SystemExit('Executable set with capture_output = True, but returned value cannot be parsed to Float')
        else:
            return float(end - start)

def tester(executable, G, cores, repetitions):
    reps = []
    for r in range(repetitions):
        series = []
        for c in cores:
            series.append(executable.run(c, G(c)))
        reps.append(np.array(series))
    return np.array(reps)

def scaling_sigle_test(executable, G, cores, repetitions, print_times=False):
    scaling = tester(executable, G, cores, repetitions)
    if print_times:
        np.savetxt(executable.name.replace(' ', '_') + '_scaling_test.txt', scaling)

    cores = np.array([np.prod(c) for c in cores[1:]])
    cores_label = [str(c) for c in cores]

    scaling = (scaling[:,0] / scaling.T)[1:]
    speedup = np.mean(scaling, axis=1) 
    speedup_std = np.std(scaling, axis=1) 
    efficiency = speedup / cores

    fig, ax1 = plt.subplots()
    ax1.set_xscale('log', basex=2)
    ax1.set_title(executable.name + ' scalablity')
    ax1.set_xlabel('Workers')
    plt.xticks(cores, cores_label)

    ax1.set_ylabel('Speedup')
    ax1.errorbar(cores, speedup, fmt='-', yerr=speedup_std, label='Speedup')

    ax2 = ax1.twinx()
    ax2.set_ylabel('Efficiency')
    ax2.set_ylim([0,1])
    ax2.plot(cores, efficiency, '--', label='Efficiency')

    ax1.legend(loc=2)
    ax2.legend(loc=1)

    fig.savefig(executable.name.replace(' ', '_') + '_scaling.png')

def scaling_full_test(executable, G_strong, G_weak, cores, repetitions, print_times=False):
    strong = tester(executalbe, G_strong, cores, repetitions)
    weak   = tester(executalbe, G_weak, cores, repetitions)
    if print_times:
        np.savetxt(executable.name.replace(' ', '_') + '_strong.png', strong)
        np.savetxt(executable.name.replace(' ', '_') + '_weak.png', weak)

    cores = np.array([np.prod(c) for c in cores[1:]])
    cores_label = [str(c) for c in cores]

    strong_scaling = (strong[:,0] / strong.T)[1:]
    strong_speedup = np.mean(strong_scaling, axis=1)
    strong_speedup_std = np.std(strong_speedup, axis=1)
    strong_efficiency = strong_speedup / cores

    weak_scaling = (weak[:,0] / weak.T)[1:]
    weak_speedup = np.mean(weak_scaling, axis=1)
    weak_speedup_std = np.std(weak_speedup, axis=1)
    weak_efficiency = weak_speedup / cores

    fig, ax1 = plt.subplots()
    ax1.set_xscale('log', basex=2)
    ax1.set_tile(executable.name + 'scalability')
    ax1.set_xlabel('Workers')
    plt.xticks(cores, cores_label)

    ax2 = ax1.twinx()
    ax2.set_ylim([0,1])
    ax1.set_ylabel('Speedup') 
    ax2.set_ylabel('Efficiency')

    ax1.errorbar(cores, strong_speedup, fmt='-', yerr=strong_speedup_std, label='Strong speedup')
    ax1.errorbar(cores, weak_speedup, fmt='--', yerr=weak_speedup_std, label='Weak efficiency')
    ax2.plot(cores, strong_efficiency, '-.', label='Strong efficiency')
    ax2.plot(cores, weak_efficiency, ':', label='Weak efficiency')

    ax1.legend(loc=2)
    ax2.legend(loc=1)
    fig.savefig(fig_name + '.png')
    
def scalability_main():
    if len(sys.argv[1:]) == 0:
        raise SystemExit('No test name given\nUsage:qsub %s -F test_name' % sys.argv[0])

    for test in sys.argv[1:]:
        try:
            exec('__main__.' + test.strip() + '()')
        except NameError:
            raise SystemExit('Wrong test name: %s' % test)

