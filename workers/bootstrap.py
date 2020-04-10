#! /usr/bin/env python3

import glob
import os
import subprocess


def main():
    pod_cidr = get_output(['curl', '-s', '-H', 'Metadata-Flavor: Google',
                           'http://metadata.google.internal/computeMetadata/v1/instance/attributes/pod-cidr'])

    install_os_deps()
    disable_swap()
    download_install_worker_binaries()
    configure_cni_networking(pod_cidr)
    configure_containerd()
    configure_kubelet(pod_cidr)
    configure_kube_proxy()
    start_worker_services()


def get_output(cmd):
    print(' '.join(cmd))
    return subprocess.check_output(cmd).decode('utf-8').strip()


def install_os_deps():
    run_cmd(['sudo', 'apt-get', 'update'])
    run_cmd(['sudo', 'apt-get', 'install', '-y',
             'socat',
             'conntrack',
             'ipset'])


def run_cmd(cmd):
    print(' '.join(cmd))
    subprocess.run(cmd)


def disable_swap():
    if swap_is_enabled():
        run_cmd(['sudo', 'swapoff', '-a'])


def swap_is_enabled():
    swapon = get_output(['sudo', 'swapon', '--show'])
    return swapon != ''


def download_install_worker_binaries():
    run_cmd([
        'wget', '-q', '--show-progress', '--https-only', '--timestamping',
        'https://github.com/kubernetes-sigs/cri-tools/releases/download/v1.15.0/crictl-v1.15.0-linux-amd64.tar.gz',
        'https://github.com/opencontainers/runc/releases/download/v1.0.0-rc8/runc.amd64',
        'https://github.com/containernetworking/plugins/releases/download/v0.8.2/cni-plugins-linux-amd64-v0.8.2.tgz',
        'https://github.com/containerd/containerd/releases/download/v1.2.9/containerd-1.2.9.linux-amd64.tar.gz',
        'https://storage.googleapis.com/kubernetes-release/release/v1.15.3/bin/linux/amd64/kubectl',
        'https://storage.googleapis.com/kubernetes-release/release/v1.15.3/bin/linux/amd64/kube-proxy',
        'https://storage.googleapis.com/kubernetes-release/release/v1.15.3/bin/linux/amd64/kubelet'])
    run_cmd(['sudo', 'mkdir', '-p',
             '/etc/cni/net.d',
             '/opt/cni/bin',
             '/var/lib/kubelet',
             '/var/lib/kube-proxy',
             '/var/lib/kubernetes',
             '/var/run/kubernetes'])
    run_cmd(['mkdir', 'containerd'])
    run_cmd(['tar', '-xvf', 'crictl-v1.15.0-linux-amd64.tar.gz'])
    run_cmd(['tar', '-xvf', 'containerd-1.2.9.linux-amd64.tar.gz', '-C', 'containerd'])
    run_cmd(['sudo', 'tar', '-xvf', 'cni-plugins-linux-amd64-v0.8.2.tgz', '-C', '/opt/cni/bin/'])
    run_cmd(['sudo', 'cp', 'runc.amd64', 'runc'])

    bins = ['crictl', 'kubectl', 'kube-proxy', 'kubelet', 'runc']
    run_cmd(['sudo', 'chmod', '+x'] + bins )
    run_cmd(['sudo', 'cp'] + bins + ['/usr/local/bin/'])
    run_cmd(['sudo', 'cp', '-r'] + glob.glob('containerd/bin/*') + ['/bin/'])


def configure_cni_networking(pod_cidr):
    with open('bridge.template.conf', 'r') as f: template = f.read()
    bridge_conf = template.replace('POD_CIDR', pod_cidr)
    with open('bridge.conf', 'w') as f: f.write(bridge_conf)

    run_cmd(['sudo', 'cp', 'bridge.conf', '/etc/cni/net.d/10-bridge.conf'])
    run_cmd(['sudo', 'cp', 'loopback.conf', '/etc/cni/net.d/99-loopback.conf'])


def configure_containerd():
    run_cmd(['sudo', 'mkdir', '-p', '/etc/containerd'])
    run_cmd(['sudo', 'cp', 'containerd-config.toml', '/etc/containerd/config.toml'])
    run_cmd(['sudo', 'cp', 'containerd.service', '/etc/systemd/system/'])


def configure_kubelet(pod_cidr):
    hostname = os.uname().nodename
    run_cmd(['sudo', 'cp', f'../{hostname}-key.pem', f'../{hostname}.pem', '/var/lib/kubelet/'])
    run_cmd(['sudo', 'cp', f'../{hostname}.kubeconfig', '/var/lib/kubelet/kubeconfig'])
    run_cmd(['sudo', 'cp', '../ca.pem', '/var/lib/kubernetes'])

    with open('kubelet-config.template.yaml', 'r') as f: template = f.read()
    kubelet_config = template.replace('HOSTNAME', hostname)
    kubelet_config = kubelet_config.replace('POD_CIDR', pod_cidr)
    with open('kubelet-config.yaml', 'w') as f: f.write(kubelet_config)

    run_cmd(['sudo', 'cp', 'kubelet-config.yaml', '/var/lib/kubelet/'])
    run_cmd(['sudo', 'cp', 'kubelet.service', '/etc/systemd/system/'])


def configure_kube_proxy():
    run_cmd(['sudo', 'cp', '../kube-proxy.kubeconfig', '/var/lib/kube-proxy/kubeconfig'])
    run_cmd(['sudo', 'cp', 'kube-proxy-config.yaml', '/var/lib/kube-proxy/'])
    run_cmd(['sudo', 'cp', 'kube-proxy.service', '/etc/systemd/system/'])


def start_worker_services():
    services = ['containerd', 'kubelet', 'kube-proxy']
    run_cmd(['sudo', 'systemctl', 'daemon-reload'])
    run_cmd(['sudo', 'systemctl', 'enable'] + services)
    run_cmd(['sudo', 'systemctl', 'start'] + services)


if __name__ == '__main__':
    main()
