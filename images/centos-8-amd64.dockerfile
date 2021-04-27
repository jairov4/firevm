FROM weaveworks/ignite-centos:8
RUN rm -f /etc/systemd/system/getty.target \
 && rm -f /etc/systemd/system/console-getty.service \
 && rm -f /etc/systemd/system/sys-fs-fuse-connections.mount \
 && rm -f /etc/systemd/system/dev-hugepages.mount \
 && rm -f /etc/systemd/system/systemd-logind.service \
 && rm -f /etc/systemd/system/systemd-remount-fs.service \
 && rm -f /etc/systemd/system/multi-user.target.wants/kdump.service \
 && rm -rf /etc/sysconfig/network-scripts/* \
 && yum install -y kernel NetworkManager \
 && yum clean all

RUN dracut -f --kver $(ls /lib/modules | head -n1) --add-drivers \
    "virtio_blk virtio_net virtio_vdpa virtio_input virtio_scsi pci-hyperv pci-hyperv-intf hid-hyperv hyperv-keyboard hv_netvsc hv_utils hv_vmbus hv_balloon hv_storvsc ext4 isofs nfs xfs fat squashfs" \
 && cp /lib/modules/*/vmlinuz /boot/ \
 && cp /lib/modules/*/config /boot/ \
 && ln -sf /boot/initramfs-* /boot/initramfs

ENTRYPOINT ["/sbin/init"]
