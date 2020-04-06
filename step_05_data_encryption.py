#! /usr/bin/env python3

import subprocess

from step_03_certificate_authority import set_cwd


num_controllers = 3
encryption_template = 'encryption-config.template.yaml'
encryption_config = 'encryption-config.yaml'


def main():
    set_cwd('encryption')
    key = generate_encryption_key()
    set_encryption_key(key)
    distribute_encryption_config()


def generate_encryption_key():
    cmd = ['head', '-c', '32', '/dev/urandom']
    raw_bytes = subprocess.check_output(cmd)
    proc = subprocess.Popen(['base64'], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
    raw_key = proc.communicate(input=raw_bytes)[0]
    return raw_key.decode('utf-8').strip()


def set_encryption_key(key):
    with open(encryption_template, 'r') as f:
        template = f.read()

    config = template.replace('ENCRYPTION_KEY', key)

    with open(encryption_config, 'w') as f:
        f.write(config)


def distribute_encryption_config():
    for i in range(num_controllers):
        cmd = ['gcloud', 'compute', 'scp', encryption_config, f'controller-{i}:~/']
        print(' '.join(cmd))
        subprocess.run(cmd)


if __name__ == '__main__':
    main()
