Container Registries
====================================

**OORT** is published on several container registries. Use whichever fits your infrastructure; image content is the same across registries.


Supported Registries
--------------------

.. list-table::
   :header-rows: 1

   * - Registry
     - Repository
   * - **Docker Hub**
     - `thecaliskan/oort <https://hub.docker.com/r/thecaliskan/oort>`_
   * - **GitHub Container Registry**
     - `ghcr.io/thecaliskan/oort <https://github.com/thecaliskan/oort/pkgs/container/oort>`_
   * - **GitLab Container Registry**
     - `registry.gitlab.com/thecaliskan/oort <https://gitlab.com/thecaliskan/oort/container_registry>`_
   * - **Quay.io**
     - `quay.io/thecaliskan/oort <https://quay.io/thecaliskan/oort>`_

Pull with the registry prefix and PHP version you need, for example ``docker pull thecaliskan/oort:{{ latest_version }}``. See :doc:`versions` for all available versions.

