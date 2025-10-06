#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Extract wheel running phase directly from logger rows in a session pickle.

We now ignore orientations entirely and parse wheel data from logger entries
whose 'Value' field contains the substring '-Deg-'. Example row:
        {'Timestamp': '0.090086100000000169', 'Frame': '3',
         'Value': 'Wheel-Index-42793322-Count-4785-Deg-210.2783203125'}

From each such row we pull:
    timestamp  = float(row['Timestamp'])
    degrees_in = float(<value after '-Deg-'>)

Conversion to phase (per provided formula):
    phase_raw_degrees = ( 2 * pi * ITEM2 * ITEM1 / tan( (1/ITEM3) * pi / 180 ) ) % 360
    phase_radians = phase_raw_degrees * pi / 180
Where:
    ITEM1 = degrees_in (wheel degrees from logger)
    ITEM2 = 0.36
    ITEM3 = 0.04

Outputs:
    CSV: Index, Timestamp, Phase  (Phase in radians, 0..2π mapped from 0..360°)
    PNG: Quick static plot (if matplotlib available)

If no wheel rows are found, exits non‑zero.

Python 2.7 compatible.
"""
from __future__ import print_function
import os
import sys
import csv
import argparse
import pickle
import math

try:
    import numpy as np
except ImportError:
    np = None

def load_session(path):
    with open(path, 'rb') as f:
        return pickle.load(f)


def parse_wheel_rows(logger_rows):
    """Return detailed phase lists from wheel logger rows.

    Returns:
        timestamps (list[float])
        wheel_deg_raw (list[float])  - raw wheel degrees parsed after '-Deg-'
        phase_deg (list[float])      - grating phase (0..360) after formula
        phase_rad (list[float])      - phase in radians (0..2π)
    """
    ts_out = []
    wheel_deg_raw = []
    phase_deg = []
    phase_rad = []
    ITEM2 = 0.36
    ITEM3 = 0.04
    denom_angle_rad = (1.0/ITEM3) * math.pi / 180.0  # (1/ITEM3) * pi/180
    denom = math.tan(denom_angle_rad)
    if denom == 0:
        denom = 1e-12
    for row in logger_rows:
        val = row.get('Value', '')
        if '-Deg-' in val:
            try:
                # timestamp
                ts = float(row.get('Timestamp', '0'))
                # degree value is after last '-Deg-'
                deg_str = val.split('-Deg-')[-1]
                # Some safety: strip any trailing non-number chars
                deg_str = deg_str.strip()
                # Remove possible trailing tokens after space
                if ' ' in deg_str:
                    deg_str = deg_str.split()[0]
                deg_in = float(deg_str)
                # Formula
                phase_raw_deg = (2.0 * math.pi * ITEM2 * deg_in / denom) % 360.0
                phase_raw_rad = phase_raw_deg * math.pi / 180.0
                ts_out.append(ts)
                wheel_deg_raw.append(deg_in)
                phase_deg.append(phase_raw_deg)
                phase_rad.append(phase_raw_rad)
            except Exception:
                continue
    return ts_out, wheel_deg_raw, phase_deg, phase_rad


########## (old orientation-based extraction removed) ##########


def save_csv(path, timestamps, wheel_deg, phase_deg, phase_rad):
    with open(path, 'wb') as f:
        writer = csv.writer(f)
        writer.writerow(['Index','Timestamp','Wheel_Degrees','Phase_Degrees','Phase_Radians'])
        for i in range(len(phase_rad)):
            writer.writerow([i, timestamps[i], wheel_deg[i], phase_deg[i], phase_rad[i]])


def plot_phases(path, timestamps, phases):
    try:
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
    except Exception:
        print('Plotting libraries unavailable; skipping plot.')
        return
    if not phases:
        return
    plt.figure(figsize=(8,3))
    plt.plot(timestamps, phases, lw=0.6)
    plt.xlabel('Time (s)')
    plt.ylabel('Phase')
    plt.title('Wheel Phase (motor blocks)')
    plt.tight_layout()
    plt.savefig(path, dpi=150)
    plt.close()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--input', required=True)
    ap.add_argument('--output', default='running_phase.csv')
    ap.add_argument('--plot', default='running_phase.png')
    args = ap.parse_args()

    data = load_session(args.input)

    bonsai = data.get('bonsai', {})
    logger_rows = bonsai.get('logger', [])

    timestamps, wheel_deg, phase_deg, phase_rad = parse_wheel_rows(logger_rows)
    if not phase_rad:
        print('No wheel logger rows with -Deg- found. Exiting.')
        sys.exit(1)
    # Ensure sorted by timestamp
    pairs = sorted(zip(timestamps, wheel_deg, phase_deg, phase_rad), key=lambda x: x[0])
    timestamps = [p[0] for p in pairs]
    wheel_deg = [p[1] for p in pairs]
    phase_deg = [p[2] for p in pairs]
    phase_rad = [p[3] for p in pairs]
    print('Extracted %d wheel samples' % len(phase_rad))

    # Save CSV
    save_csv(args.output, timestamps, wheel_deg, phase_deg, phase_rad)
    print('Saved phase CSV to %s (rows=%d)' % (args.output, len(phase_rad)))

    # Plot
    plot_phases(args.plot, timestamps, phase_rad)
    if os.path.exists(args.plot):
        print('Saved phase plot to %s' % args.plot)

if __name__ == '__main__':
    main()
