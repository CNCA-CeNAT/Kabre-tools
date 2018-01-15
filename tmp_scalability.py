import modules
import time
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import sys

def dummy_setup():
    pass

def poli_growth(base, order):
    return lambda c: base * c**order


# P(c, s): Takes c cores and s problem size and returns an string to run the program
# G(c):    Takes cores and returns a problem size.
# C:       A list of workers
# rep:     number of repetitions 

class Executable:
    def __init__(self, setup, P, G_strong, G_weak, capture_output=False, name=''):
        self.P        = P
        self.G_strong = G_strong
        self.G_weak   = G_weak
        self.co       = capture_output
        self.name     = name
        setup()

    def run(self, c, G):
        start = time.time()
            
        out = modules.run(self.P(c, self.G(c)), capture_output=True)
        end = time.time()
        if self.co:
            return float(out)
        else:
            return float(end - start)

def scalability_supporter(executable, cores, reps, test_type='strong'):
    if test_type == 'strong':
        C = [cores[-1] for i in cores]
    elif test_type == 'weak':
        C = cores
    else:
        raise ValueError('test_type must be \'strong\' or \'weak\'')

    repetitions = []
    for r in range(reps):
        series = []
        for c in C:
            series.append(executable.run(c))
        repetitions.append(np.array(series))
    return np.array(repetitions)


def comparison(executables, cores, reps, test_type='strong', fig_name='comparison', print_times=False):
    pass

def test(executable, cores, reps, fig_name='scalability', print_times=False):
    strong = scalability_supporter(executable, cores, reps, 'strong')
    weak   = scalability_supporter(executable, cores, reps, 'weak')

    if print_times:
        np.savetxt(fig_name + '_strong.txt', strong)
        np.savetxt(fig_name + '_weak.txt', weak)

    cores = np.array([np.prod(c) for c in cores[1:]])
    cores_label = [str(c) for c in cores[1:]]

    strong = (strong[:, 0] / strong.T)[1:]
    strong_speedup = np.mean(strong, axis=1)
    strong_speedup_std = np.std(strong, axis=1)
    strong_efficiency = strong_speedup / cores

    weak = (weak[:, 0] / weak.T)[1:]
    weak_speedup = np.mean(weak, axis=1)
    weak_speedup_std = np.std(weak, axis=1)
    weak_efficiency = weak_speedup / cores

    fig, ax1 = plt.subplots()
    ax1.set_xscale('log', basex=2)
    ax1.set_title(fig_name)
    ax1.set_xlabel('Workers')
    plt.xticks(cores, cores_label)

    ax2 = ax1.twinx()
    ax2.set_ylim([0,1])
    ax1.set_ylabel('Speedup')
    ax2.set_ylabel('Efficiency')

    ax1.errorbar(cores, strong_speedup, fmt='-', yerr=strong_speedup_std, label='Strong speedup')
    ax1.errorbar(cores, weak_speedup, fmt='--', yerr=weak_speedup_std, label='Weak speedup')
    ax2.plot(cores, strong_efficiency, '-.', label='Strong efficiency')
    ax2.plot(cores, weak_efficiency, ':', label='Weak efficiency')

    ax1.legend(loc=2)
    ax2.legend(loc=1)
    fig.savefig(fig_name + '.png')

def scalability_main():
    if len(sys.argv[1:]) == 0:
        raise SystemExit('No test name given\nUsage:qsub %s -F test_name' $ sys.argv[0])

    for test in sys.argv[1:]:
        try:
            exec(test + '()')
        except NameError:
            raise SystemExit('Wrong test name')

