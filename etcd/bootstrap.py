#! /usr/bin/env python3

import subprocess


def main():
    install_etcd()
    configure_etcd()
    start_etcd()


def install_etcd():
    download_tarball()
    extract_binaries()
    install_binaries()


def download_tarball():
    run_cmd(['wget', '-q', '--show-progress', '--https-only', '--timestamping',
             'https://github.com/etcd-io/etcd/releases/download/v3.4.0/etcd-v3.4.0-linux-amd64.tar.gz'])


def run_cmd(cmd):
    print(' '.join(cmd))
    subprocess.run(cmd)


def extract_binaries():
    run_cmd(['tar', '-xvf', 'etcd-v3.4.0-linux-amd64.tar.gz'])


def install_binaries():
    run_cmd(['sudo', 'mv', 'etcd-v3.4.0-linux-amd64/etcd', '/usr/local/bin'])
    run_cmd(['sudo', 'mv', 'etcd-v3.4.0-linux-amd64/etcdctl', '/usr/local/bin'])


def configure_etcd():
    run_cmd(['sudo', 'mkdir', '-p', '/etc/etcd', '/var/lib/etcd'])
    run_cmd(['sudo', 'cp', '../ca.pem', '../kubernetes.pem', '../kubernetes-key.pem', '/etc/etcd'])
    internal_ip = get_internal_ip()
    etcd_name = get_output(['hostname', '-s'])
    write_etcd_service(etcd_name, internal_ip)
    run_cmd(['sudo', 'cp', 'etcd.service', '/etc/systemd/system/'])


def get_internal_ip():
    return get_output(['curl', '-s', '-H', 'Metadata-Flavor: Google',
                       'http://metadata.google.internal/computeMetadata/v1/instance/network-interfaces/0/ip'])


def write_etcd_service(etcd_name, internal_ip):
    with open('etcd.template.service', 'r') as f:
        template = f.read()

    template = template.replace('ETCD_NAME', etcd_name)
    template = template.replace('INTERNAL_IP', internal_ip)

    with open('etcd.service', 'w') as f:
        f.write(template)


def get_output(cmd):
    print(' '.join(cmd))
    return subprocess.check_output(cmd).decode('utf-8').strip()


def start_etcd():
    run_cmd(['sudo', 'systemctl', 'daemon-reload'])
    run_cmd(['sudo', 'systemctl', 'enable', 'etcd'])
    run_cmd(['sudo', 'systemctl', 'start', 'etcd'])



if __name__ == '__main__':
    main()
