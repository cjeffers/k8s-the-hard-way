#! /usr/bin/env python3

import subprocess

base_url = 'https://storage.googleapis.com/kubernetes-the-hard-way/cfssl/linux'
deps = ['cfssl', 'cfssljson']
bin_dir = '/usr/local/bin'
required_version = '1.3.4'


def main():
    get_deps()
    install_deps()
    check_version()


def get_deps():
    for dep in deps:
        url = f'{base_url}/{dep}'
        run_cmd(['wget', '-q', '--show-progress', '--https-only', '--timestamping', url])


def run_cmd(cmd):
    print(' '.join(cmd))
    subprocess.run(cmd)


def install_deps():
    for dep in deps:
        run_cmd(['chmod', '+x', dep])
        run_cmd(['sudo', 'mv', dep, bin_dir])


def check_version():
    for dep in deps:
        version = get_version(dep)
        if not is_greater_than_or_equal_to_required(version):
            clean_up()
            raise Exception(f'{dep} version {version} is less than required version {required_version}')
    print(f'versions greater than or equal to {required_version}')


def get_version(dep):
    if 'json' in dep:
        arg = '--version'
    else:
        arg = 'version'

    output_bytes = subprocess.check_output([dep, arg])
    output = output_bytes.decode('utf-8')
    lines = output.split('\n')
    version_line = lines[0]
    version = version_line[len('Version: '):]
    return version


def is_greater_than_or_equal_to_required(version):
    return parse_version(version) >= parse_version(required_version)


def parse_version(version):
    # assume 3 semver levels, and no more than 2 digits per level
    levels = version.split('.')
    levels[0] = int(levels[0]) * 10000
    levels[1] = int(levels[1]) * 100
    levels[2] = int(levels[2]) * 1
    return sum(levels)


def clean_up():
    for dep in deps:
        run_cmd(['sudo', 'rm', f'{bin_dir}/{dep}'])


if __name__ == '__main__':
    main()
