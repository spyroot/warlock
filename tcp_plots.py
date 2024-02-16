import matplotlib.pyplot as plt

import numpy as np
import json


def iperf_data_as_np(json_data):
    measurements = []

    # Iterate over each interval and stream
    for interval in json_data['intervals']:
        for stream in interval['streams']:
            socket = stream['socket']
            bytes_val = stream['bytes']
            bps = stream['bits_per_second']
            cwnd = stream.get('snd_cwnd', np.nan)  # Use np.nan for missing values
            wnd = stream.get('snd_wnd', np.nan)
            rtt_val = stream.get('rtt', np.nan)
            rttvar_val = stream.get('rttvar', np.nan)

            # Append a new row for each stream
            measurements.append([socket, bytes_val, bps, cwnd, wnd, rtt_val, rttvar_val])

    measurements_np = np.array(measurements)
    return measurements_np



with open('test.json', 'r') as f:
    data = json.load(f)
    stats = iperf_data_as_np(data)
    plot_bps_core_perf(stats)
    print(stats)
