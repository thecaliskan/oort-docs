Tags
==============

The **OORT** Docker image is available with several version tags to meet your specific requirements. Below are the available tags:

Supported Tags
--------------

{% for supported_version in supported_versions %}
.. |image-size-{{ supported_version }}| image:: https://img.shields.io/docker/image-size/thecaliskan/oort/{{ supported_version }}?label=
   :target: https://hub.docker.com/r/thecaliskan/oort/tags?page=1&name={{ supported_version }}
   :alt: Docker Image Size {{ supported_version }}
.. |image-tag-{{ supported_version }}| image:: https://img.shields.io/docker/v/thecaliskan/oort/{{ supported_version }}?label=thecaliskan%2Foort
   :target: https://hub.docker.com/r/thecaliskan/oort/tags?page=1&name={{ supported_version }}
   :alt: Docker Version Tag {{ supported_version }}
{% endfor %}

.. list-table::
   :header-rows: 1

   * - Tag
     - PHP Version
     - Alpine Version
     - Image Size
     - From
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


Automatic Image Updates
-----------------------

The **OORT** Docker image is automatically rebuilt and updated every day at approximately **03:00 UTC+0**. This ensures that the image stays up-to-date with the latest improvements, bug fixes, and security patches.
