#! /usr/bin/env python3

import subprocess

from step_03_certificate_authority import get_k8s_public_ip

num_controllers = 3

def main():
    for i in range(num_controllers):
        run_cmd(['gcloud', 'compute', 'scp', '--recurse', 'etcd/', f'controller-{i}:~/'])
        run_cmd(['gcloud', 'compute', 'scp', '--recurse', 'control_plane/', f'controller-{i}:~/'])

    run_cmd(['gcloud', 'compute', 'scp', '--recurse', 'rbac/', f'controller-0:~/'])

    provision_external_load_balancer()


def run_cmd(cmd):
    print(' '.join(cmd))
    subprocess.run(cmd)


def provision_external_load_balancer():
    run_cmd(['gcloud', 'compute', 'http-health-checks', 'create', 'kubernetes',
             '--description', 'Kubernetes Health Check',
             '--host', 'kubernetes.default.svc.cluster.local',
             '--request-path', '/healthz'])
    run_cmd(['gcloud', 'compute', 'firewall-rules', 'create', 'k8s-the-hard-way-allow-health-check',
             '--network', 'k8s-the-hard-way',
             '--source-ranges', '209.85.152.0/22,209.85.204.0/22,35.191.0.0/16',
             '--allow', 'tcp'])
    run_cmd(['gcloud', 'compute', 'target-pools', 'create', 'kubernetes-target-pool',
             '--http-health-check', 'kubernetes'])
    run_cmd(['gcloud', 'compute', 'target-pools', 'add-instances', 'kubernetes-target-pool',
             '--instances', 'controller-0,controller-1,controller-2'])
    run_cmd(['gcloud', 'compute', 'forwarding-rules', 'create', 'kubernetes-forwarding-rule',
             '--address', get_k8s_public_ip(),
             '--ports', '6443',
             '--region', get_region(),
             '--target-pool', 'kubernetes-target-pool'])


def get_region():
    cmd = ['gcloud', 'config', 'get-value', 'compute/region']
    print(' '.join(cmd))
    return subprocess.check_output(cmd).decode('utf-8').strip()


if __name__ == '__main__':
    main()
