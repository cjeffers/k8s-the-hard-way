#! /usr/bin/env python3

import subprocess

k8s_binaries = ['kube-apiserver', 'kube-controller-manager', 'kube-scheduler', 'kubectl']
k8s_bin_dir = '/usr/local/bin'
k8s_data_dir = '/var/lib/kubernetes'

def main():
    download_k8s_binaries()
    install_k8s_binaries()
    configure_api_server()
    configure_service('kube-controller-manager')
    configure_scheduler()
    start_controller_services()
    enable_health_checks()


def get_output(cmd):
    print(' '.join(cmd))
    return subprocess.check_output(cmd).decode('utf-8')


def download_k8s_binaries():
    urls = [f'https://storage.googleapis.com/kubernetes-release/release/v1.15.3/bin/linux/amd64/{binary}'
            for binary in k8s_binaries]
    run_cmd(['wget', '-q', '--show-progress', '--https-only', '--timestamping'] + urls)


def run_cmd(cmd):
    print(' '.join(cmd))
    subprocess.run(cmd)


def install_k8s_binaries():
    run_cmd(['chmod', '+x'] + k8s_binaries)
    run_cmd(['sudo', 'mv'] + k8s_binaries + [k8s_bin_dir])


def configure_api_server():
    run_cmd(['sudo', 'mkdir', '-p', k8s_data_dir])
    cert_names = ['ca', 'kubernetes', 'service-account']
    certs = [f'../{cert}.pem' for cert in cert_names]
    certs += [f'../{cert}-key.pem' for cert in cert_names]
    run_cmd(['sudo', 'cp'] + certs + ['../encryption-config.yaml', k8s_data_dir])

    with open('kube-apiserver.template.service', 'r') as f:
        template = f.read()
    config = template.replace('INTERNAL_IP', get_internal_ip())
    with open('kube-apiserver.service', 'w') as f:
        f.write(config)

    run_cmd(['sudo', 'mv', 'kube-apiserver.service', '/etc/systemd/system/'])


def get_internal_ip():
    return get_output(['curl', '-s', '-H', 'Metadata-Flavor: Google',
                       'http://metadata.google.internal/computeMetadata/v1/instance/network-interfaces/0/ip'])


def configure_service(name):
    run_cmd(['sudo', 'cp', f'../{name}.kubeconfig', k8s_data_dir])
    run_cmd(['sudo', 'cp', f'{name}.service', '/etc/systemd/system/'])


def configure_scheduler():
    run_cmd(['sudo', 'mkdir', '-p', '/etc/kubernetes/config/'])
    run_cmd(['sudo', 'cp', 'kube-scheduler.yaml', '/etc/kubernetes/config/'])
    configure_service('kube-scheduler')


def start_controller_services():
    run_cmd(['sudo', 'systemctl', 'daemon-reload'])
    run_cmd(['sudo', 'systemctl', 'enable'] + k8s_binaries[:-1])
    run_cmd(['sudo', 'systemctl', 'start'] + k8s_binaries[:-1])


def enable_health_checks():
    nginx_conf = 'kubernetes.default.svc.cluster.local'
    sites_dir = '/etc/nginx/sites-available'
    run_cmd(['sudo', 'apt-get', 'update'])
    run_cmd(['sudo', 'apt-get', 'install', '-y', 'nginx'])
    run_cmd(['sudo', 'cp', nginx_conf, sites_dir])
    run_cmd(['sudo', 'ln', '-s', f'{sites_dir}/{nginx_conf}', '/etc/nginx/sites-enabled/'])
    run_cmd(['sudo', 'systemctl', 'restart', 'nginx'])
    run_cmd(['sudo', 'systemctl', 'enable', 'nginx'])


if __name__ == '__main__':
    main()
