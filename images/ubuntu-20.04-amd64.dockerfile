FROM weaveworks/ignite-ubuntu:20.04-amd64
RUN apt-get update -y && apt-get install -y linux-image-5.4.0-1009-kvm
ENTRYPOINT ["/lib/systemd/systemd"]
