import matplotlib
matplotlib.use('Agg')

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

    plt.figure(figsize=(11, 5))
    plt.plot(times, pending_jobs, color='blue')
    plt.grid(color='b', linestyle='--', linewidth=1, alpha=0.3)

    # New xticks.
    locs, labels = plt.xticks()
    new_ticks = [dt.fromtimestamp(x).strftime('%H:%M') for x in locs]
    plt.xticks(locs[1:-1], new_ticks[1:-1], rotation=30, fontsize=15)
    plt.yticks(fontsize=15)

    # Vertical lines.
    for day in days:
        plt.axvline(x=day, color='k', linestyle='-.')

    # Captions.
    plt.title('{} - Local time of bot: {}'.format(backend,
              dt.fromtimestamp(time.time()).strftime('%Y, %b %d, %H:%M')),
              fontsize=15)
    plt.xlabel('Time', fontsize=15)
    plt.ylabel('Pending jobs', fontsize=15)
    plt.savefig(filename, bbox_inches='tight')
