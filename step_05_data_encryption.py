#! /usr/bin/env python3

import subprocess

from step_03_certificate_authority import set_cwd


def main():
    set_cwd('encryption')
    key = generate_encryption_key()
    set_encryption_key(key)


def generate_encryption_key():
    cmd = ['head', '-c', '32', '/dev/urandom']
    raw_bytes = subprocess.check_output(cmd)
    proc = subprocess.Popen(['base64'], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
    raw_key = proc.communicate(input=raw_bytes)[0]
    return raw_key.decode('utf-8').strip()


def set_encryption_key(key):
    with open('encryption-config.template.yaml', 'r') as f:
        template = f.read()

    config = template.replace('ENCRYPTION_KEY', key)

    with open('encryption-config.yaml', 'w') as f:
        f.write(config)


if __name__ == '__main__':
    main()
