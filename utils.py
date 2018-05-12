import matplotlib
matplotlib.use('Agg')

import math
import numpy as np
import matplotlib.pyplot as plt
import threading
import pickle
import time
from datetime import date, timedelta
from datetime import datetime as dt
import os
from qiskit.backends import discover_local_backends, discover_remote_backends

from IBMQuantumExperience import IBMQuantumExperience

import sys
sys.path.append("res/")
import Qconfig
from qiskit import QuantumProgram

qx_config = {
    "APItoken": Qconfig.APItoken,
    "url": Qconfig.config['url']
}

api = IBMQuantumExperience(token=qx_config['APItoken'], config={'url': qx_config['url']})


class myThread(threading.Thread):
    def __init__(self, delay, run_event):
        threading.Thread.__init__(self)
        self.delay = delay
        self.run_event = run_event

    def run(self):
        dumper(self.delay, self.run_event)


def dumper(delay, run_event):
    if os.path.exists('real_data.pkl') is False:
        data = list()
        with open('real_data.pkl', 'wb') as f:
                pickle.dump(data, f)

    while run_event.is_set():
        # Load.
        with open('real_data.pkl', 'rb') as f:
            data = pickle.load(f)

        # Append.
        remote_backends = discover_remote_backends(api)
        device_status = [api.backend_status(backend) for backend in remote_backends]

        data.append((time.time(), device_status))

        # Store.
        with open('real_data.pkl', 'wb') as f:
            pickle.dump(data, f)

        # Sleep.
        time.sleep(delay)


def make_plot(backend, filename):
    with open('real_data.pkl', 'rb') as f:
        data = pickle.load(f)

    times = sorted([x[0] for x in data])
    pending_jobs = [[y for y in x[1] if y['backend'] == backend][0]['pending_jobs']
                    for x in sorted(data, key=lambda x: x[0])]

    d1 = dt.fromtimestamp(times[0]).date()
    d2 = dt.fromtimestamp(times[-1]).date()
    # Timedelta.
    delta = d2 - d1
    days = list()
    for i in range(delta.days + 1):
        tmp = d1 + timedelta(days=i)
        tmp_ts = float(tmp.strftime('%s'))
        if tmp_ts >= times[0] and tmp_ts <= times[-1]:
            days.append(tmp_ts)
    
    #Display only last 24h of the data
    
    plt.figure(figsize=(11, 5))
    plt.grid(True, zorder=5)
    plt.fill_between(times,pending_jobs)
    
    # New xticks.
    locs, labels = plt.xticks()
    new_ticks = [dt.fromtimestamp(x).strftime('%H')+':00' for x in locs]
    plt.xticks(locs[1:-1], new_ticks[1:-1], rotation=0, fontsize=15)
    plt.yticks(fontsize=15)
    
    # y axis: display only integer values
    yint = []
    locs, labels = plt.yticks()
    for each in locs:
        yint.append(int(each))
    plt.yticks(yint)
    plt.ylim(0, math.ceil(max(pending_jobs))+1) #math.ceil(max(pending_jobs))+1
    
    # Vertical lines.
    #for day in days:
    #    plt.axvline(x=day, color='k', linestyle='-.')

    # Captions.
    plt.title('IBMQ Backend: {}, Local time of bot: {}'.format(backend,
              dt.fromtimestamp(time.time()).strftime('%Y, %b %d, %H:%M')),
              fontsize=15)
    plt.xlabel('Time', fontsize=15)
    plt.ylabel('# of pending jobs', fontsize=15)
    plt.show()
    plt.savefig(filename, bbox_inches='tight')

def plot_calibration(backend):
    Q_program = QuantumProgram()
    Q_program.set_api(Qconfig.APItoken, Qconfig.config["url"])
    full_info = Q_program.get_backend_calibration(backend)
    
    N_qubits = len(full_info['qubits'])
    qubits = [full_info['qubits'][qub]['name'] for qub in range(N_qubits)]
    readout_error = [full_info['qubits'][qub]['readoutError']['value'] for qub in range(N_qubits)]
    readout_error = np.array([readout_error])
    
    last_update = full_info['last_update_date']
    last_update = dt.strptime(last_update, "%Y-%m-%dT%H:%M:%S.000Z").timestamp()
    last_update = dt.fromtimestamp(last_update).strftime('%Y, %b %d, %H:%M')    
 
    plt.matshow(readout_error, cmap='Reds')

    # Placing actual values in the matshow plot
    for (i,), value in np.ndenumerate(readout_error[0]):
        plt.text(i, 0, '{:0.2f}'.format(value), ha='center', va='center')    
    
    # Formatting axes
    locs, labels = plt.xticks()
    plt.xticks(1+locs, qubits)
    plt.yticks([],[])
    plt.autoscale(axis = 'both', tight=True)
    
    plt.title('Backend: {}, Single qubits readout errors,\n last calibration: {}\n'.format(backend, last_update), fontsize=15)
    plt.margins(tight=True)
    plt.savefig(backend+'_readout_err.png', bbox_inches='tight')
    plt.show()
    
    multi_qubit_gates = [full_info['multi_qubit_gates'][qub]['qubits'] for qub in range(N_qubits)]
    multi_qubit_error = [full_info['multi_qubit_gates'][qub]['gateError']['value'] for qub in range(N_qubits)]    
    
    # creating gate error matrix
    error_matrix = np.zeros((N_qubits,N_qubits))
    for i in range(len(multi_qubit_gates)):
        gate = multi_qubit_gates[i]
        qub1, qub2 = gate[0], gate[1]
        error_matrix[qub1][qub2] = multi_qubit_error[i]
    # Symmetrizing the error matrix
    error_matrix = 1./2*(error_matrix + error_matrix.T)
    plt.matshow(error_matrix, cmap='Reds')
    
    # Placing actual values in the matshow plot
    for (i, j), value in np.ndenumerate(error_matrix):
        plt.text(j, i, '{:0.2f}'.format(value), ha='center', va='center')
    
    plt.title('Backend: {}, Two qubit gate errors,\n last calibration: {}\n'.format(backend, last_update), fontsize=15)
    
    # Formatting axes
    locs, labels = plt.yticks()
    plt.yticks(1+locs, qubits)
    
    locs, labels = plt.xticks()
    plt.xticks(1+locs, qubits)
    plt.autoscale(axis = 'both', tight=True)
    plt.savefig(backend+'_multiqubut_err.png', bbox_inches='tight')