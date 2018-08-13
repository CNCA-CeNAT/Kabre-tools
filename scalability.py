import matplotlib
matplotlib.use('Agg')

import time
import numpy as np
import matplotlib.pyplot as plt 
import sys
import modules 

def dummy_setup():
    pass

def poli_growth(factor, order):
    return lambda c: int(factor * np.power(c, 1/order))

class Executable:
    def __init__(self, P, setup, name='scaling_test', parse_output_func=None):
        self.P            = P
        self.name         = name
        self.parse_output = parse_output_func
        setup()

    def run(self, c, s):
        start = time.time()
        out = modules.run(self.P(c, s), capture_output=True)
        end = time.time()
        if self.parse_output != None:
            r_value = self.parse_output(out.stdout)
            if type(r_value) is not float:
                raise SystemExit('Value returned by self.parse_output() isn´t a float')
        else:
            r_value = float(end - start)
        return r_value

def tester(executable, G, cores, repetitions):
    reps = []
    for r in range(repetitions):
        series = []
        for c in cores:
            base_run = executable.run(cores[0], G(c))
            test_run = executable.run(c, G(c))
            series.append(base_run / test_run)
        reps.append(np.array(series))
    return np.array(reps)

def scaling_sigle_test(executable, G, cores, repetitions, print_times=False):
    scaling = tester(executable, G, cores, repetitions)
    if print_times:
        np.savetxt(executable.name.replace(' ', '_') + '_scaling_test.txt', scaling)

    workers = np.array([np.prod(c) for c in cores])
    cores_label = [str(c) for c in cores]

    speedup = np.mean(scaling, axis=0) 
    speedup_std = np.std(scaling, axis=0) 
    efficiency = speedup / workers

    fig, ax1 = plt.subplots()
    ax1.set_xscale('log', basex=2)
    ax1.set_title(executable.name + ' scalablity')
    ax1.set_xlabel('Workers')
    plt.xticks(workers, cores_label)

    ax1.set_ylabel('Speedup')
    ax1.errorbar(workers, speedup, fmt='-', yerr=speedup_std, label='Speedup')

    ax2 = ax1.twinx()
    ax2.set_ylabel('Efficiency')
    ax2.set_ylim([0,1.1])
    ax2.plot(workers, efficiency, '--', label='Efficiency')

    ax1.legend(loc=2)
    ax2.legend(loc=4)

    fig.savefig(executable.name.replace(' ', '_') + '_scaling.png')

def scaling_full_test(executable, G_strong, G_weak, cores, repetitions, print_times=False):
    strong_scaling = tester(executable, G_strong, cores, repetitions)
    weak_scaling   = tester(executable, G_weak, cores, repetitions)
    if print_times:
        np.savetxt(executable.name.replace(' ', '_') + '_strong.txt', strong_scaling)
        np.savetxt(executable.name.replace(' ', '_') + '_weak.txt', weak_scaling)

    workers = np.array([np.prod(c) for c in cores])
    cores_label = [str(c) for c in cores]

    strong_speedup = np.mean(strong_scaling, axis=0)
    strong_speedup_std = np.std(strong_scaling, axis=0)
    strong_efficiency = strong_speedup / workers

    weak_speedup = np.mean(weak_scaling, axis=0)
    weak_speedup_std = np.std(weak_scaling, axis=0)
    weak_efficiency = weak_speedup / workers

    fig, ax1 = plt.subplots()
    ax1.set_xscale('log', basex=2)
    ax1.set_title(executable.name + ' scalability')
    ax1.set_xlabel('Workers')
    plt.xticks(workers, cores_label)

    ax2 = ax1.twinx()
    ax2.set_ylim([0,1.1])
    ax1.set_ylabel('Speedup') 
    ax2.set_ylabel('Efficiency')

    ax1.errorbar(workers, strong_speedup, fmt='-', yerr=strong_speedup_std, label='Strong speedup')
    ax1.errorbar(workers, weak_speedup, fmt='--', yerr=weak_speedup_std, label='Weak speedup')
    ax2.plot(workers, strong_efficiency, '-.', label='Strong efficiency')
    ax2.plot(workers, weak_efficiency, ':', label='Weak efficiency')

    ax1.legend(loc=2)
    ax2.legend(loc=4)
    fig.savefig(executable.name.replace(' ', '_') + '_full_scaling.png')


def scaling_multiple(name, exec_list, G, cores, repetitions, print_time=False):
    scaling = []
    for e in exec_list:
        scaling.append(tester(e, G, cores, repetitions))
        if print_time:
            np.savetxt(e.name.replace(' ', '_') + 'scaling_multiple.txt', scaling[-1])

    workers = np.array([np.prod(c) for c in cores])
    cores_label = [str(c) for c in cores]

    speedup     = [np.mean(s, axis=0) for s in scaling]
    speedup_std = [np.std(s, axis=0) for s in scaling]

    fig, ax = plt.subplots()
    ax.set_xscale('log', basex=2)
    ax.set_title(name + ' scalablity')
    ax.set_xlabel('Workers')
    plt.xticks(workers, cores_label)

    ax.set_ylabel('Speedup')
    for s, s_std, e in zip(speedup, speedup_std, exec_list):
        ax.errorbar(workers, s, fmt='-', yerr=s_std, label=e.name.replace(' ', '_'))

    ax.legend(loc=2)
    fig.savefig(name + '_cmp_scaling_test.png')

def scalability_main(test_funcs):
    if len(sys.argv[1:]) == 0:
        raise SystemExit('No test name given\nUsage:qsub %s -F test_name' % sys.argv[0])

    for test in sys.argv[1:]:
        try:
            test_funcs[test.strip()]()
        except KeyError:
            raise SystemExit('Wrong test name: ' + str(test))

