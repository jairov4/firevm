# FireVM

Utility to create slim VM images from docker container images.
The idea behind this is you can leverage the existing great tooling for docker images
and get an incredible easy workflow to compose your VM images too.

Example:

```bash
# We create our new VM definition via regular container tooling 
docker build -t my-vm-template:latest .
# We create our 200MB QCOW2 VM image from container image
firevm my-vm-template:latest -s 200 -f qcow2 -o my-vm-template.qcow2  
```

# Requisites

- Docker CE installed
- QEMU utilities installed
- Python 3.6+
