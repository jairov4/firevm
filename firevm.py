#!python3
import argparse
import json
import logging
import os
import subprocess
import tempfile
from contextlib import contextmanager
from typing import List, Union, Iterable

DEFAULT_KERNEL = 'scratch'  # 'jairov4/firevm-kernel:4.19.183-amd64'
DEFAULT_KERNEL_PATH = '/boot/vmlinuz'


def prepare_cmd_line(args: Iterable[Union[bytes, str]]) -> List[str]:
    sanitized = [arg.decode('utf-8') if isinstance(arg, bytes) else arg for arg in args]
    logging.debug(f'Executing: {" ".join(sanitized)}')
    return sanitized


def ex(*args, stdin=None):
    args = prepare_cmd_line(args)
    return subprocess.run(
        args, stdout=subprocess.PIPE, input=stdin, check=True).stdout.decode('utf-8')


def exe(*args, stdin=None):
    args = prepare_cmd_line(args)
    subprocess.run(args, input=stdin, check=True)


def sudo_exe(*args, stdin=None):
    exe('sudo', *args, stdin=stdin)


def sudo_ex(*args, stdin=None):
    return ex('sudo', *args, stdin=stdin)


def find_init_data(docker_image):
    txt = ex('docker', 'image', 'inspect', docker_image)
    docker = json.loads(txt)
    ep = docker[0]["Config"]["Entrypoint"] or []
    cmd = docker[0]["Config"]["Cmd"] or []
    line = ep + cmd
    return line[0], line[1:]


def export_container(container, tar):
    logging.info(f'Exporting container {container}')
    container_id = ex('docker', 'create', container, 'nop').strip()
    exe('docker', 'export', container_id, '-o', tar)
    exe('docker', 'rm', container_id)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('image', help='Input Docker Image')
    parser.add_argument('-s', '--size', type=int, required=True, help='Size in MB')
    parser.add_argument('-o', '--output', required=True, help='Output filename')
    parser.add_argument('-f', '--format', default='raw', help='Output format')
    parser.add_argument('-p', '--kernel-path', default=DEFAULT_KERNEL_PATH)
    parser.add_argument('-k', '--kernel', default=DEFAULT_KERNEL,
                        help=f'Docker image for kernel. Default: {DEFAULT_KERNEL}')
    opts = parser.parse_args()

    docker_image = opts.image
    size_mb = opts.size
    output = opts.output
    out_format = opts.format
    kernel_img = opts.kernel
    kernel = opts.kernel_path

    init, init_args = find_init_data(docker_image)

    with tempfile.TemporaryDirectory(prefix='firevm') as w:
        logging.debug(f'Using temp folder: {w}')
        mount_point = os.path.join(w, 'fs')
        img_fn = os.path.join(w, 'disk.img')
        kernel_tar = os.path.join(w, 'kernel.tar.gz')
        rootfs_tar = os.path.join(w, 'rootfs.tar.gz')
        mbr_fn = '/usr/share/syslinux/mbr.bin'

        exe('mkdir', '-p', mount_point)

        export_container(kernel_img, kernel_tar) if kernel_img != 'scratch' else None
        export_container(docker_image, rootfs_tar)

        with mount_new_disk(mount_point, img_fn, size_mb) as loop_device:
            sudo_exe('tar', 'xfC', rootfs_tar, mount_point)
            sudo_exe('tar', 'xfC', kernel_tar, mount_point) if kernel_img != 'scratch' else None
            install_bootloader(mount_point, mbr_fn, init, init_args, loop_device, kernel)

        if out_format == 'qcow2':
            logging.info('Converting image to QCOW2')
            exe('qemu-img', 'convert', '-f', 'raw', '-O', 'qcow2', img_fn, output)
        elif out_format == 'vhdx':
            logging.info('Converting image to VHDX')
            exe('qemu-img', 'convert', '-O', 'vhdx', img_fn, output)
        elif out_format == 'raw':
            logging.info('Copying RAW image')
            exe('mv', img_fn, output)

        logging.info(f'Created image {output}')


def install_bootloader(mount_point, mbr_fn, init, init_args, loop, kernel):
    logging.info('Installing bootloader')
    init_args = ' '.join(init_args)
    initramfs_file = 'boot/initramfs'
    try:
        sudo_ex('ls', os.path.join(mount_point, initramfs_file))
        initrd = 'INITRD /' + initramfs_file
        initrd_kp = 'initrd=/' + initramfs_file
        logging.info(initrd)
    except subprocess.CalledProcessError as e:
        logging.exception(e)
        logging.info('No initramfs detected')
        initrd = ''
        initrd_kp = ''

    sudo_exe('mkdir', '-p', f"{mount_point}/boot/syslinux")
    sudo_exe('extlinux', '--install', f"{mount_point}/boot/syslinux")
    sudo_exe('dd', 'bs=440', 'count=1', 'conv=notrunc', f'if={mbr_fn}', f'of={loop}')
    sudo_exe('bash', '-c', '\n'.join([
        f'cat >> \'{mount_point}/boot/syslinux/syslinux.cfg\' <<EOF',
        f'DEFAULT linuxkernel',
        f'LABEL linuxkernel',
        f'  LINUX {kernel}',
        f'  APPEND ip=dhcp root=/dev/vda1 rw console=ttyS0 {initrd_kp} init={init} -- {init_args}',
        f'  {initrd}',
        f'EOF'
    ]))


def unmount_disk(loop, mount_point):
    logging.info('Un-mounting loop device')
    sudo_exe('umount', '-f', mount_point)
    sudo_exe('losetup', '-d', loop)


@contextmanager
def mount_new_disk(mount_point: str, img_fn: str, size_mb: int):
    logging.info('Creating raw disk image')
    exe('dd', 'if=/dev/zero', f'of={img_fn}', 'bs=1M', f'count={size_mb}')
    exe('fdisk', img_fn, stdin="n\n\n\n\n\na\nw\n".encode('utf-8'))
    loop = sudo_ex('losetup', '--show', '-Pf', img_fn).strip()
    sudo_exe('mkfs.ext4', f'{loop}p1')
    sudo_exe('mount', '-t', 'ext4', f'{loop}p1', mount_point)
    uuid = sudo_ex('blkid', '-o', 'value', '-s', 'UUID', f'{loop}p1').strip()
    logging.info(f'Partition UUID: {uuid}')
    yield loop
    unmount_disk(loop, mount_point)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(name)s - %(levelname)s - %(message)s')
    main()
