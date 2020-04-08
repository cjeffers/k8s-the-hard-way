#! /usr/bin/env python3

import subprocess

num_controllers = 3

def main():
    for i in range(num_controllers):
        run_cmd(['gcloud', 'compute', 'scp', '--recurse', 'etcd/', f'controller-{i}:~/'])
        run_cmd(['gcloud', 'compute', 'scp', '--recurse', 'control_plane/', f'controller-{i}:~/'])


def run_cmd(cmd):
    print(' '.join(cmd))
    subprocess.run(cmd)


if __name__ == '__main__':
    main()
