#!python3
import os, sys, json, logging


DEFAULT_KERNEL = 'weaveworks/ignite-kernel:4.19.183-amd64'


def ex(*args, *, stdin=None):
	return subprocess.run(args, stdout=subprocess.PIPE, input=stdin, check=True).stdout


def exe(*args):
	subprocess.run(args, check=True)


def find_init_data(docker_image):
	txt = ex('docker', 'image', 'inspect', docker_image)
	docker = json.loads(txt)
	ep = docker[0]["Config"]["Entrypoint"] || []
	cmd = docker[0]["Config"]["Cmd"] || []
	line = ep + cmd
	return line[1], line[1:]


def export_container(container, tar):
	logging.info(f'Exporting container {container}')
	container_id = ex('docker', 'create', container)
	exe('docker', 'export', container_id, '-o', tar)
	exe('docker', 'rm', container_id)


def main():
	docker_image = sys.argv[1]
	size = sys.argv[2]

	init, init_args = find_init_data(docker_image)
	kernel_img = DEFAULT_KERNEL
	if len(sys.argv):
		kernel_img = sys.argv[3]

	syslinux = '/usr/lib/syslinux'
	w = '_firevm'
	dev = os.path.join(w, 'fs')
	img = os.path.join(w, 'disk.img')
	qcow2 = os.path.join(w, 'disk.qcow2')
	kernel_tar = os.path.join(w, 'kernel.tar.gz')
	rootfs_tar = os.path.join(w, 'rootfs.tar.gz')

	exe('rm', '-rf', w)
	exe('mkdir', '-p', dev)

	export_container(kernel_img, kernel_tar)
	export_container(docker_image, rootfs_tar)

	logging.info('Creating raw disk image')
	exe('dd', 'if=/dev/zero', f'of={img}', 'bs=1M', f'count={size}')
	exe('fdisk', img, stdin="n\n\n\n\na\nw\n")
	loop = ex('sudo', 'losetup', '--show', '-Pf', img)
	exe('sudo', 'mkfs.ext4', f'{loop}p1')
	exe('sudo', 'mount', '-t', 'ext4', f'{loop}p1', dev)
	uuid = exe('sudo', 'blkid', '-o', 'value', '-s', 'UUID', f'{loop}p1')
	exe('sudo', 'tar', 'xfC', kernel_tar, dev)
	exe('sudo', 'tar', 'xfC', rootfs_tar, dev)

	logging.info('Installing bootloader')
	exe('sudo', 'mkdir', '-p', f"{dev}/boot/syslinux")
	exe('sudo', 'extlinux', '--install', f"{dev}/boot/syslinux")
	# exe('sudo', 'cp', '/usr/share/syslinux/*.c32', "$DEV/boot/syslinux/")
	exe('sudo', 'dd', 'bs=440', 'count=1', 'conv=notrunc', 'if=/usr/share/syslinux/mbr.bin', f'of={loop}')
	exe('sudo', 'bash', '-c', '\n'.join([
		f'\'cat >> \'"{dev}/boot/syslinux/syslinux.cfg" <<EOF',
		f'DEFAULT linuxkernel',
		f'LABEL linuxkernel',
		f'  LINUX /boot/vmlinux',
		f'  APPEND ip=dhcp root=/dev/vda1 rw console=ttyS0 init={init} -- {init_args}'
		f'EOF'
	]))
	exe('sudo', 'umount', dev)
	exe('sudo', 'losetup', '-d', loop)

	logging.info('Convert disk image')
	exe('qemu-img', 'convert', '-f', 'raw', '-O', 'qcow2', img, qcow2)
	exe('qemu-img', 'convert', '-O', 'vhdx', qcow2, vhdx)


if __name__ == "__main__"
	logging.basicConfig(level=logging.INFO, format='%(name)s - %(levelname)s - %(message)s')
	main()
