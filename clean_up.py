#! /usr/bin/env python3

import subprocess
import os
import glob


num_workers = 3
num_controllers = 3
cert_dir = 'certs'
kubeconfig_dir = 'kubeconfig'

base_dir = os.path.dirname(os.path.realpath(__file__))


def main():
    # delete_compute_instances()
    # delete_pems()
    delete_kubeconfigs()


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
    pems = glob.glob(f'{base_dir}/{cert_dir}/*.pem')
    print(f'deleting {len(pems)} pem files')
    run_cmd(['rm'] + pems)


def delete_kubeconfigs():
    kubeconfigs = glob.glob(f'{base_dir}/{kubeconfig_dir}/*.kubeconfig')
    print(f'deleting {len(kubeconfigs)} kubeconfig files')
    run_cmd(['rm'] + kubeconfigs)


if __name__ == '__main__':
    main()
