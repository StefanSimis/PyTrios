#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Connect to a TriOS G1 Radiometer and trigger measurement with a given integration time, store results to file.
@author: stsi
"""
import sys
import os
import time
import datetime
import argparse
import logging
import serial.tools.list_ports as list_ports
import pytrios
import pytrios.radman as radiometer_manager

def single_sample(radiometry_manager, inttime, file):
    log.info(f"Trigger measurement")
    trig_id, specs, sids, itimes, preincs, postincs, inctemps  = radiometry_manager.sample_all(datetime.datetime.now(), inttime=inttime)

    for i, sid in enumerate(sids):
        log.info(f"Received spectrum from {sid}: {trig_id} | int-time: {itimes[i]} ms | Spectrum: {specs[i][0:3]}...{specs[i][-3::]}")

        if file is not None:
            with open(file, 'a+') as outfile:
                outfile.write(f"{str(sid)}\t{trig_id.isoformat()}\t{str(itimes[i])}\t{','.join([str(s) for s in specs[i]])}\n")


def run_sample(port, repeat=1, type=1, inttime=0, file=None):
    """Test connectivity to TriOS RAMSES radiometer sensors"""

    if type == 1:
        log.info("Starting G1 radiometry manager")
        rad_manager = radiometer_manager.TriosManager(port)

    elif type == 2:
        log.info("Starting G2 radiometry manager")
        rad_manager = radiometer_manager.TriosG2Manager(port)

    t0 = time.perf_counter()
    while (not rad_manager.ready) and ((time.perf_counter() - t0) < 5.0):
        log.info(f"Waiting for sensor initialisation to complete..")
        time.sleep(1)

    if rad_manager.ready:
        log.info(f"Starting {repeat} measurements (press CTRL-C to interrupt)")
        while repeat > 0:
            try:
                single_sample(rad_manager, inttime, file)
                repeat = repeat - 1
                time.sleep(1)
            except KeyboardInterrupt:
                repeat = 0
            except Exception:
                raise

    else:
        log.warning(f"Radiometry manager not ready. Exiting")

    log.info("Stopping radiometry manager..")
    if rad_manager is not None:
        rad_manager.stop()
    log.info("Done.")


def parse_args():
    """parse command line arguments"""
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', '--port', type=str, default=None, help="serial port to connect on")
    parser.add_argument('-r', '--repeat', type=int, default=1, help="repeat measurement n times")
    parser.add_argument('-t', '--type', type=int, default=None, help="1 = G1 sensor, 2 = G2 sensor")
    parser.add_argument('-i', '--inttime', type=int, default=0, help="Integration time: 0 (auto), 4 (G2 only), 8, 16, 32, 64, 128, 256, 512, 1024, 2048, 4096, 8192 ms")
    parser.add_argument('-f', '--file', type=str, default=None, help="Append results to file (provide file path)")
    args = parser.parse_args()
    return args


if __name__ == '__main__':
    args = parse_args()

    log = logging.getLogger()
    handler = logging.StreamHandler(sys.stdout)
    log.setLevel(logging.INFO)
    handler.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s| %(levelname)s | %(name)s | %(message)s')
    handler.setFormatter(formatter)
    log.addHandler(handler)

    if args.type is None:
        log.info("No device type selected. Specify G1 or G2 type")
        sys.exit()
    elif args.type == 1 and args.inttime>0:
        if args.inttime not in [8, 16, 32, 64, 128, 256, 512, 1024, 2048, 4096, 8192]:
            log.info("Integration time for G1 sensors must be one of 8, 16, 32, 64, 128, 256, 512, 1024, 2048, 4096, 8192 ms")
            sys.exit()
    elif args.type == 2 and args.inttime>0:
        if args.inttime not in [4, 8, 16, 32, 64, 128, 256, 512, 1024, 2048, 4096, 8192]:
            log.info("Integration time for G2 sensors must be one of 4, 8, 16, 32, 64, 128, 256, 512, 1024, 2048, 4096, 8192 ms")
            sys.exit()
    else:
        log.info("Sensor type must be 1 (G1) or 2 (G2)")
        sys.exit()

    if args.port is None:
        log.info("No device selected. The following are available (select a serial port with the -p argument):")
        ports = list_ports.comports()
        for port, desc, hwid in sorted(ports):
            log.info("\t {0} {1} {2}".format(port, desc, hwid))

    else:
        run_sample(args.port, args.repeat, args.type, args.inttime, args.file)
