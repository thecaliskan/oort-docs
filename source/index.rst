Introduction
==========================================

Welcome to the **OORT** documentation.

OORT is a lightweight Docker base image for modern PHP applications — Laravel Octane, Horizon, Reverb, Pulse, Symfony Runtime, Messenger, Scheduler, and similar long-running workloads.

The image is minimal, production-ready, and runs **one process per container**.


At a Glance
-----------

- **PHP** — {% for version in supported_versions %}{{ version }}{% if not loop.last %}, {% endif %}{% endfor %} (latest: **{{ latest_version }}**)
- **Architectures** — {% for arch in supported_architectures %}{{ arch }}{% if not loop.last %}, {% endif %}{% endfor %}
- **Registries** — Docker Hub, GHCR, GitLab, Quay (see :doc:`container-registries`)

.. code-block:: bash

   docker pull thecaliskan/oort:{{ latest_version }}

For Dockerfile templates, deployment patterns, and framework guides, see :doc:`usage`.


.. toctree::
    :titlesonly:
    :maxdepth: 4
    :caption: Contents:

    self
    architecture-support
    container-registries
    tags
    packages
    extensions
    usage
    security
    frequently-asked-questions
