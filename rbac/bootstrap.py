#! /usr/bin/env python3

import subprocess


def main():
    apply_file('kube-apiserver-to-kubelet.clusterrole.yaml')
    apply_file('kube-apiserver-to-kubelet.clusterrolebinding.yaml')


def apply_file(filename):
    cmd = ['kubectl', 'apply', '--validate=false', '--filename', '-']

    with open(filename, 'rb') as f:
        yaml = f.read()

    print(' '.join(cmd + [filename]))
    subprocess.run(cmd, input=yaml)


if __name__ == '__main__':
    main()
