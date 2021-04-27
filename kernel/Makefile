SHELL:=/bin/bash
# Set the command for running `docker`
# -- allows user to override for things like sudo usage or container images
DOCKER := docker

REGISTRY?=jairov4
IMAGE_NAME?=${REGISTRY}/firevm-kernel
KERNEL_BUILDER_NAME=${REGISTRY}/firevm-kernel-builder
# Check https://git.kernel.org/pub/scm/linux/kernel/git/stable/linux.git/refs/ for updates
KERNEL_VERSIONS ?= 4.14.227 4.19.183 5.4.108 5.10.25
GOARCH?=amd64
GOARCH_LIST = amd64 arm64

ifeq ($(GOARCH),amd64)
    KERNEL_ARCH=x86
    VMLINUX_PATH ?= arch/x86/boot/bzImage
endif
ifeq ($(GOARCH),arm64)
    ARCH_MAKE_PARAMS="ARCH=arm64 CROSS_COMPILE=aarch64-linux-gnu-"
    KERNEL_ARCH=arm64
    VMLINUX_PATH ?= arch/arm64/boot/bzImage
endif

all: build

kernel-builder:
	$(DOCKER) build -t ${KERNEL_BUILDER_NAME}:dev -f Dockerfile.builder .

build: $(addprefix build-,$(KERNEL_VERSIONS))
build-%: kernel-builder
	$(DOCKER) build -t $(IMAGE_NAME):$*-${GOARCH} \
		--build-arg KERNEL_VERSION=$* \
		--build-arg ARCH=${KERNEL_ARCH} \
		--build-arg GOARCH=${GOARCH} \
		--build-arg ARCH_MAKE_PARAMS=${ARCH_MAKE_PARAMS} \
		--build-arg VMLINUX_PATH=${VMLINUX_PATH} .

push: $(addprefix push-,$(KERNEL_VERSIONS))
push-%: build-%
	$(DOCKER) push $(IMAGE_NAME):$*-${GOARCH}
