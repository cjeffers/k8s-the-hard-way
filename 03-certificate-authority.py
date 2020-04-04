#! /usr/bin/env python3

import glob
import os
import subprocess

cert_dir = 'certs'
num_workers = 3


def main():
    set_cwd()
    init_ca()
    make_client_server_certs()
    # make_service_account_cert()
    clean_up()
    # upload_certs()


def set_cwd():
    base_dir = os.path.dirname(os.path.realpath(__file__))
    full_dir = f'{base_dir}/{cert_dir}'
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
    # make_controller_manager_client_cert()
    # make_kube_proxy_client_cert()
    # make_scheduler_client_cert()
    # make_kubernetes_api_server_cert()


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


def run_cmd(cmd):
    print(' '.join(cmd))
    subprocess.run(cmd, check=True)


if __name__ == '__main__':
    main()
