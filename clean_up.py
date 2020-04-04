#! /usr/bin/env python3

import subprocess
import os
import glob


num_workers = 3
num_controllers = 3
cert_dir = 'certs'


def main():
    delete_compute_instances()
    delete_pems()


def delete_compute_instances():
    workers = [f'worker-{i}' for i in range(num_workers)]
    controllers = [f'controller-{i}' for i in range(num_controllers)]
    delete_instances(workers + controllers)


def delete_instances(instances):
    cmd = ['gcloud', 'compute', 'instances', 'delete', '--quiet'] + instances
    run_cmd(cmd)


def run_cmd(cmd):
    print(' '.join(cmd))
    subprocess.run(cmd)


def delete_pems():
    base_dir = os.path.dirname(os.path.realpath(__file__))
    pems = glob.glob(f'{base_dir}/{cert_dir}/*.pem')
    print(f'deleting {len(pems)} pem files')
    run_cmd(['rm'] + pems)


if __name__ == '__main__':
    main()
