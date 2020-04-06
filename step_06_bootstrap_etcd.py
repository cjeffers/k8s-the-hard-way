#! /usr/bin/env python3

import subprocess

num_controllers = 3

def main():
    for i in range(num_controllers):
        cmd = ['gcloud', 'compute', 'scp', '--recurse', 'etcd/', f'controller-{i}:~/']
        print(' '.join(cmd))
        subprocess.run(cmd)


if __name__ == '__main__':
    main()
