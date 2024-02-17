#
#
import os
from typing import Dict

import matplotlib.pyplot as plt
import numpy as np
import json


def iperf_tcp_json_to_np(json_data: Dict) -> np.ndarray:
    """Converts a json tcp iperf stats to a numpy array
    :param json_data:
    :return:
    """
    stats = []

    for interval in json_data['intervals']:
        for stream in interval['streams']:
            socket = stream['socket']
            bytes_val = stream['bytes']
            bps = stream['bits_per_second']
            cwnd = stream.get('snd_cwnd', np.nan)
            wnd = stream.get('snd_wnd', np.nan)
            rtt_val = stream.get('rtt', np.nan)
            rttvar_val = stream.get('rttvar', np.nan)
            stats.append([socket, bytes_val, bps, cwnd, wnd, rtt_val, rttvar_val])

    return np.array(stats)


def plot_tcp_perf(
        np_data: np.ndarray,
        metric: str,
        save_dir: str,
        file_name: str
) -> None:
    """
    Plot TCP performance (bps, cwnd, wnd, rtt) over time for each socket
    and save the plot to a file.

    :param np_data: Numpy array containing the data. Each row represents a data point, with
                    various metrics such as bits per second and round-trip time.
    :param metric: String specifying which metric to plot ('bps' for bits per second or 'rtt' for round-trip time).
    :param save_dir: String specifying the directory where the plot should be saved.
    :param file_name: String specifying the name of the file to save the plot as.
    """
    if metric not in ['bps', 'cwnd', 'wnd', 'rtt']:
        raise ValueError("Metric must be 'bps', 'cwnd', 'wnd', or 'rtt'.")

    metric_info = {
        'bps': (2, 'Bits per Second'),
        'cwnd': (3, 'Congestion Window Size'),
        'wnd': (4, 'Window Size'),
        'rtt': (5, 'Round-Trip Time (ms)')
    }

    metric_col, metric_label = metric_info[metric]

    unique_sockets = np.unique(np_data[:, 0])

    plt.figure(figsize=(10, 6))

    for socket in unique_sockets:
        socket_data = np_data[np_data[:, 0] == socket]
        plt.plot(
            socket_data[:, 1],
            socket_data[:, metric_col],
            label=f'Socket {int(socket)}'
        )

    plt.xlabel('Time Interval')
    plt.ylabel(metric_label)
    plt.title(f'Performance of Each Socket Over Time ({metric_label})')
    plt.legend()
    plt.grid(True)

    if not os.path.exists(save_dir):
        os.makedirs(save_dir)

    plt.savefig(os.path.join(save_dir, file_name))
    plt.close()
