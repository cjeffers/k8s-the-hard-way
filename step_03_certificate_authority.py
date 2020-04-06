#! /usr/bin/env python3

import glob
import os
import subprocess

num_workers = 3
num_controllers = 3


def main():
    set_cwd('certs')
    init_ca()
    make_client_server_certs()
    make_client_cert('service-account')
    clean_up()
    distribute_certs()


def set_cwd(dir):
    base_dir = os.path.dirname(os.path.realpath(__file__))
    full_dir = f'{base_dir}/{dir}'
    os.chdir(full_dir)


def init_ca():
    cfssl_out = get_output(['cfssl', 'gencert', '-initca', 'ca-csr.json'])
    write_pems(cfssl_out, 'ca')


def get_output(cmd):
    print(' '.join(cmd))
    return subprocess.check_output(cmd)


def write_pems(cfssl_out, name):
    cmd = ['cfssljson', '-bare', name]
    print(' '.join(cmd))
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    proc.communicate(cfssl_out)


def make_client_server_certs():
    make_client_cert('admin')
    make_kubelet_client_certs()
    make_controller_client_certs()
    make_kubernetes_api_server_cert()


def make_client_cert(name, hostnames=[]):
    cmd = ['cfssl', 'gencert',
           '-ca=ca.pem',
           '-ca-key=ca-key.pem',
           '-config=ca-config.json',
           '-profile=kubernetes',
           f'{name}-csr.json']

    if any(hostnames):
        hostname_arg = f'-hostname={",".join(hostnames)}'
        cmd = cmd[:-1] + [hostname_arg] + cmd[-1:]

    cfssl_out = get_output(cmd)
    write_pems(cfssl_out, name)


def make_kubelet_client_certs():
    for i in range(num_workers):
        instance = f'worker-{i}'
        write_kubelet_csr_json(instance)
        make_kubelet_client_cert(instance)


def write_kubelet_csr_json(instance):
    with open('worker-csr.template.json', 'r') as f:
        template_json = f.read()

    worker_json = template_json.replace('INSTANCE', instance)

    with open(f'{instance}-csr.json', 'w') as f:
        f.write(worker_json)


def make_kubelet_client_cert(instance):
    hostnames = [instance, get_external_ip(instance), get_internal_ip(instance)]
    make_client_cert(instance, hostnames=hostnames)


def get_external_ip(instance):
    return describe_instance(instance, 'value(networkInterfaces[0].accessConfigs[0].natIP)')


def describe_instance(instance, fmt):  # using fmt to avoid python keyword 'format'
    output = get_output(['gcloud', 'compute', 'instances', 'describe', instance, '--format', fmt])
    return output.decode('utf-8')


def get_internal_ip(instance):
    return describe_instance(instance, 'value(networkInterfaces[0].networkIP)')


def clean_up():
    run_cmd(['rm'] + glob.glob('*.csr'))
    run_cmd(['rm'] + glob.glob('worker-*-csr.json'))
    run_cmd(['rm', 'kube-controller-manager-csr.json', 'kube-proxy-csr.json', 'kube-scheduler-csr.json'])


def run_cmd(cmd):
    print(' '.join(cmd))
    subprocess.run(cmd, check=True)


def make_controller_client_certs():
    make_controller_client_cert('kube-controller-manager')
    make_controller_client_cert('kube-proxy', 'node-proxier')
    make_controller_client_cert('kube-scheduler')


def make_controller_client_cert(name, group=None):
    if group is None:
        group = name

    write_controller_client_csr_json(name, group)
    make_client_cert(name)


def write_controller_client_csr_json(name, group):
    with open('controller-client-csr.template.json', 'r') as f:
        template_json = f.read()

    client_json = template_json.replace('COMPONENT', name)
    client_json = client_json.replace('COMPONENT_GROUP', group)

    with open(f'{name}-csr.json', 'w') as f:
        f.write(client_json)


def make_kubernetes_api_server_cert():
    hostnames=['10.32.0.1',  # first IP in service ClusterIP CIDR
               '10.55.0.10',  # controller instance IP
               '10.55.0.11',  # controller instance IP
               '10.55.0.12',  # controller instance IP
               get_k8s_public_ip(),
               '127.0.0.1',
               'kubernetes',
               'kubernetes.default',
               'kubernetes.default.svc',
               'kubernetes.default.svc.cluster',
               'kubernetes.default.svc.cluster.local']
    make_client_cert('kubernetes', hostnames=hostnames)


def get_k8s_public_ip():
    region = get_output(['gcloud', 'config', 'get-value', 'compute/region']).decode('utf-8').strip()
    return get_output(['gcloud', 'compute', 'addresses', 'describe', 'k8s-the-hard-way',
                       '--region', region,
                       '--format', 'value(address)']).decode('utf-8').strip()


def distribute_certs():
    upload_worker_certs()
    upload_controller_certs()


def upload_worker_certs():
    for i in range(num_workers):
        instance = f'worker-{i}'
        certs = ['ca.pem', f'{instance}-key.pem', f'{instance}.pem']
        upload_certs(instance, certs)


def upload_certs(instance, certs):
    run_cmd(['gcloud', 'compute', 'scp'] + certs + [f'{instance}:~/'])


def upload_controller_certs():
    for i in range(num_controllers):
        certs = ['ca.pem', 'ca-key.pem',
                 'kubernetes.pem', 'kubernetes-key.pem',
                 'service-account.pem', 'service-account-key.pem']
        upload_certs(f'controller-{i}', certs)


if __name__ == '__main__':
    main()
