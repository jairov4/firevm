# FireVM

Utility to create slim VM images from docker container images.
The idea behind this is you can leverage the existing great tooling for docker images
and get an incredible easy workflow to compose your VM images too.

Example:

```bash
docker build -t my-vm-template:latest .
firevm my-vm-template:latest 500 -f qcow2 -o my-vm-template.qcow2  
```

# Requisites

- Docker CE installed
- QEMU utilities installed
- Python 3.6+
