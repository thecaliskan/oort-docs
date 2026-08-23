Versions
==============

**OORT** is published as separate images per PHP version. Each release uses a Docker image tag that matches the PHP version (for example ``8.5``). The ``latest`` tag always points to the current default release.

Pick the version that matches your application's PHP requirement. For security support windows, see :doc:`security`.

Available Versions
------------------

{% for supported_version in supported_versions %}
.. |image-size-{{ supported_version }}| image:: https://img.shields.io/docker/image-size/thecaliskan/oort/{{ supported_version }}?label=
   :target: https://hub.docker.com/r/thecaliskan/oort/tags?page=1&name={{ supported_version }}
   :alt: Image size for PHP {{ supported_version }}
.. |image-tag-{{ supported_version }}| image:: https://img.shields.io/docker/v/thecaliskan/oort/{{ supported_version }}?label=thecaliskan%2Foort
   :target: https://hub.docker.com/r/thecaliskan/oort/tags?page=1&name={{ supported_version }}
   :alt: Registry label for PHP {{ supported_version }}
{% endfor %}

.. list-table::
   :header-rows: 1

   * - Version
     - PHP
     - Alpine
     - Image Size
     - On Registry
   * - **latest**
     - {{ latest_version }}
     - {{ alpine_version }}
     - |image-size-{{ latest_version }}|
     - |image-tag-{{ latest_version }}|
{% for supported_version in supported_versions %}
   * - **{{ supported_version }}**
     - {{ supported_version }}
     - {{ alpine_version }}
     - |image-size-{{ supported_version }}|
     - |image-tag-{{ supported_version }}|
{% endfor %}


Image Updates
-------------

**OORT** images are rebuilt daily at approximately **03:00 UTC**. Rebuilds pick up upstream package updates, bug fixes, and security patches without changing the PHP version you pull.
