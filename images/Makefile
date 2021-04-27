SHELL := /bin/bash
DOCKER := docker
PYTHON3 := python3

REGISTRY ?= jairov4
IMAGE_NAME_PREFIX ?= ${REGISTRY}/firevm-

BUILDS = centos-8-amd64.qcow2 ubuntu-20.04-amd64.qcow2

all: $(BUILDS)

%.qcow2: OS=$(word 1,$(subst -, ,$*))
%.qcow2: VERSION=$(word 2,$(subst -, ,$*))
%.qcow2: ARCH=$(word 3,$(subst -, ,$*))
%.qcow2: IMAGE_NAME=$(IMAGE_NAME_PREFIX)$(OS)
%.qcow2: DOCKER_FILE=$(OS)-$(VERSION)-$(ARCH).dockerfile
%.qcow2: IMAGE_FILE=$(OS)-$(VERSION)-$(ARCH).qcow2

%.qcow2: %.dockerfile ../firevm.py
	$(DOCKER) build . -f $(DOCKER_FILE) -t $(IMAGE_NAME):$(VERSION)-$(ARCH)
	$(PYTHON3) ../firevm.py $(IMAGE_NAME):$(VERSION)-$(ARCH) -s 1000 -f qcow2 -o $(IMAGE_FILE)

test-%: OS=$(word 1,$(subst -, ,$*))
test-%: VERSION=$(word 2,$(subst -, ,$*))
test-%: ARCH=$(word 3,$(subst -, ,$*))
test-%: IMAGE_FILE=$(OS)-$(VERSION)-$(ARCH).qcow2
test-%: VM_NAME=$(OS)-$(VERSION)-$(ARCH)
test-%: %.qcow2
	chmod a+w $(IMAGE_FILE)
	sudo virt-install --name $(VM_NAME) --ram 1024 --disk $(IMAGE_FILE),bus=virtio --boot hd \
		--network user,model=virtio --nographics --os-type linux --import --boot machine=q35
	sudo virsh -c qemu:///system destroy $(VM_NAME) || echo Destroy not performed
	sudo virsh -c qemu:///system undefine $(VM_NAME)
