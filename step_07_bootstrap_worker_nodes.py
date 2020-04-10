#! /usr/bin/env python3

import subprocess

num_workers = 3


def main():
    for i in range(num_workers):
        cmd = ['gcloud', 'compute', 'scp', '--recurse', 'workers', f'worker-{i}:~/']
        print(' '.join(cmd))
        subprocess.run(cmd)


if __name__ == '__main__':
    main()
