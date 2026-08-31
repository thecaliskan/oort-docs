Architecture Support
==========================

**OORT** ships multi-architecture images so you can deploy the same PHP application on amd64 servers, ARM hardware, and enterprise platforms without changing your Dockerfile.


Supported Architectures
-----------------------

- **linux/amd64** — Standard 64-bit Intel and AMD processors.
- **linux/arm64** — 64-bit ARM, including Apple Silicon, cloud ARM instances, and embedded targets.
- **linux/ppc64le** — IBM PowerPC 64-bit Little Endian for HPC and enterprise servers.
- **linux/s390x** — IBM Z and LinuxONE mainframes.

Pull the image on any supported platform; the registry serves the matching architecture automatically.
