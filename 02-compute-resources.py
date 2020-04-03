#! /usr/bin/env python3

import subprocess


vpc_net_name = 'k8s-the-hard-way'
subnet_name = 'kubernetes'
subnet_range = '10.55.0.0/24'
pod_range = '10.100.0.0/16'
num_controllers = 3
num_workers = 3


def main():
    create_network()
    create_subnet()
    create_firewall_rules()
    allocate_static_ip()
    create_controller_nodes()
    create_worker_nodes()


def create_network():
    run_cmd(['gcloud', 'compute', 'networks', 'create', vpc_net_name, '--subnet-mode', 'custom'])


def run_cmd(cmd):
    print(' '.join(cmd))
    subprocess.run(cmd)


def create_subnet():
    run_cmd(['gcloud', 'compute', 'networks', 'subnets', 'create', subnet_name,
             '--network', vpc_net_name,
             '--range', subnet_range])


def create_firewall_rules():
    create_firewall_rule('k8s-the-hard-way-allow-internal', 'tcp,udp,icmp', f'{subnet_range},{pod_range}')
    create_firewall_rule('k8s-the-hard-way-allow-external', 'tcp:22,tcp:6443,icmp', '0.0.0.0/0')


def create_firewall_rule(name, allow, ranges):
    run_cmd(['gcloud', 'compute', 'firewall-rules', 'create', name,
             '--allow', allow,
             '--network', vpc_net_name,
             '--source-ranges', ranges])


def allocate_static_ip():
    region = get_output(['gcloud', 'config', 'get-value', 'compute/region'])
    run_cmd(['gcloud', 'compute', 'addresses', 'create', vpc_net_name,
             '--region', region])


def get_output(cmd):
    print(' '.join(cmd))
    return subprocess.check_output(cmd).decode('utf-8').strip()


def create_controller_nodes():
    for i in range(num_controllers):
        create_instance(f'controller-{i}', get_private_ip(1, i), ['controller'])


def get_private_ip(prefix, index):
    subnet_prefix = '.'.join(subnet_range.split('.')[:3])
    return f'{subnet_prefix}.{prefix}{index}'


def create_instance(name, private_ip, tags, *args):
    run_cmd(['gcloud', 'compute', 'instances', 'create', name,
             '--async',
             '--boot-disk-size', '200GB',
             '--can-ip-forward',
             '--image-family', 'ubuntu-1804-lts',
             '--image-project', 'ubuntu-os-cloud',
             '--machine-type', 'n1-standard-1',
             '--scopes', 'compute-rw,storage-ro,service-management,service-control,logging-write,monitoring',
             '--subnet', subnet_name,
             '--private-network-ip', private_ip,
             '--tags', ','.join(['k8s-the-hard-way'] + tags)] + list(args))


def create_worker_nodes():
    for i in range(num_workers):
        create_instance(f'worker-{i}', get_private_ip(2, i), ['worker'],
                        '--metadata', f'pod-cidr={get_pod_cidr(i)}')


def get_pod_cidr(index):
    pod_cidr_prefix = '.'.join(pod_range.split('.')[:2])
    return f'{pod_cidr_prefix}.{index}.0/24'


if __name__ == '__main__':
    main()
