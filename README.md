# FireVM

Utility to create slim VM images from docker container images.
The idea behind this is you can leverage the existing great tooling for docker images
and get an incredible easy workflow to compose your VM images too.

[![asciicast](https://asciinema.org/a/410067.svg)](https://asciinema.org/a/410067)

Example:

```bash
# We create our new VM definition via regular container tooling 
docker build -t my-vm-template:latest .
# We create our 200MB QCOW2 VM image from container image
firevm my-vm-template:latest -s 200 -f qcow2 -o my-vm-template.qcow2
# Launch our new VM
sudo virt-install --name my-vm --ram 1024 --disk /my-vm-template.qcow2,bus=virtio \
    --boot hd --network user,model=virtio --nographics --os-type linux --import
```

# Requisites

- Docker CE installed
- QEMU utilities installed
- Python 3.6+

# How works?

FireVM tool is inspired in Firecraker's Ignite project which provided a similar idea 
focused on VMs targeted to run in Firecracker only.
Our goal in firevm is to ignite slim and generic cloud VM images suitable for a wider
range of hypervisors like KVM and Hyper-V. 

The PoC was tested on CentOS 8.

# Available Kernel Images

They are Docker images holding kernel compiled and ready to use

- `jairov4/firevm-kernel:5.10.25-amd64`
- `jairov4/firevm-kernel:5.4.108-amd64`
- `jairov4/firevm-kernel:4.19.183-amd64`
- `jairov4/firevm-kernel:4.14.227-amd64`

# Compiling own kernel image

```bash
cd kernel
make
```

# Troubleshooting

Remember setup your file ACL in home directory for KVM usage to allow qemu user walk in.

```bash
sudo setfacl -m u:qemu:rx /home/$USER/ 
```