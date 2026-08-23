Introduction
==========================================

Welcome to the **OORT** documentation.

OORT is a lightweight Docker base image for modern PHP applications — Laravel Octane, Horizon, Reverb, Pulse, Symfony Runtime, Messenger, Scheduler, and similar long-running workloads.

The image is minimal, production-ready, and designed for **one process per container**.


At a Glance
-----------

- **PHP** — {% for version in supported_versions %}{{ version }}{% if not loop.last %}, {% endif %}{% endfor %} (default: **{{ latest_version }}**; see :doc:`versions`)
- **Architectures** — {% for arch in supported_architectures %}{{ arch }}{% if not loop.last %}, {% endif %}{% endfor %} (see :doc:`architecture-support`)
- **Registries** — Docker Hub, GHCR, GitLab, Quay (see :doc:`container-registries`)
- **Frameworks** — Laravel 12–13 and Symfony 7.4–8.1 tested in CI (see :doc:`usage/index`)

.. code-block:: bash

   docker pull thecaliskan/oort:{{ latest_version }}

For Dockerfile templates, deployment patterns, and framework guides, see :doc:`usage/index`.


.. toctree::
    :titlesonly:
    :maxdepth: 4
    :caption: Contents:

    self
    architecture-support
    container-registries
    versions
    packages
    extensions
    usage/index
    security
    frequently-asked-questions
