#! /usr/bin/env python3


import subprocess

from step_03_certificate_authority import set_cwd, get_k8s_public_ip


num_workers = 3
num_controllers = 3
cert_dir = '../certs'
cluster = 'k8s-the-hard-way'


def main():
    set_cwd('kubeconfig')
    k8s_public_ip = get_k8s_public_ip()
    make_kubelet_kubeconfigs(k8s_public_ip)
    make_kubeconfig(k8s_public_ip, 'kube-proxy')
    make_kubeconfig('127.0.0.1', 'kube-controller-manager')
    make_kubeconfig('127.0.0.1', 'kube-scheduler')
    make_kubeconfig('127.0.0.1', 'admin', user='admin')
    distribute_kubeconfigs()


def make_kubelet_kubeconfigs(k8s_public_ip):
    for i in range(num_workers):
        instance = f'worker-{i}'
        user = f'system:node:{instance}'
        make_kubeconfig(k8s_public_ip, instance, user=user)


def make_kubeconfig(cluster_ip, name, user=None, kubeconfig=None):
    user = f'system:{name}' if user is None else user
    kubeconfig = f'{name}.kubeconfig' if kubeconfig is None else kubeconfig
    set_cluster(cluster_ip, kubeconfig)
    set_user(user, name, kubeconfig)
    set_context(user, kubeconfig)


def set_cluster(cluster_ip, kubeconfig):
        run_cmd(['kubectl', 'config', 'set-cluster', cluster,
                 f'--certificate-authority={cert_dir}/ca.pem',
                 '--embed-certs=true',
                 f'--server=https://{cluster_ip}:6443',
                 '--kubeconfig', kubeconfig])


def run_cmd(cmd):
    print(' '.join(cmd))
    subprocess.run(cmd)


def set_user(user, client_cert_name, kubeconfig):
        run_cmd(['kubectl', 'config', 'set-credentials', user,
                 f'--client-certificate={cert_dir}/{client_cert_name}.pem',
                 f'--client-key={cert_dir}/{client_cert_name}-key.pem',
                 '--embed-certs=true',
                 '--kubeconfig', kubeconfig])


def set_context(user, kubeconfig):
        run_cmd(['kubectl', 'config', 'set-context', 'default',
                 '--cluster', cluster,
                 '--user', user,
                 '--kubeconfig', kubeconfig])
        run_cmd(['kubectl', 'config', 'use-context', 'default',
                 '--kubeconfig', kubeconfig])


def make_kube_proxy_kubeconfig(k8s_public_ip):
    client_cert = 'kube-proxy'
    kubeconfig = 'kube-proxy.kubeconfig'
    user = 'system:kube-proxy'
    make_kubeconfig(k8s_public_ip, user, client_cert, kubeconfig)


def distribute_kubeconfigs():
    for i in range(num_workers):
        instance = f'worker-{i}'
        run_cmd(['gcloud', 'compute', 'scp',
                 f'{instance}.kubeconfig', 'kube-proxy.kubeconfig',
                 f'{instance}:~/'])

    for i in range(num_controllers):
        run_cmd(['gcloud', 'compute', 'scp',
                 'kube-controller-manager.kubeconfig', 'kube-scheduler.kubeconfig', 'admin.kubeconfig',
                 f'controller-{i}:~/'])


if __name__ == '__main__':
    main()
