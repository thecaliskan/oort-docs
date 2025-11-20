Packages
==============

This page provides a detailed list of all packages included in our Docker image. You can use this as a reference to understand the image’s contents and manage dependencies effectively.


latest
---------------------------



{% for supported_architecture in supported_architectures %}

{{ supported_architecture }}
^^^^^^^^^^^^^^^^^^

.. json-table::
   :file: source/_data/sbom-{{ latest_version }}/{{ supported_architecture.replace('/', '_') }}/sbom.spdx.json
   :path: predicate.packages
   :headers: Name, Version, License
   :columns: name, versionInfo, licenseDeclared


{% endfor %}


{% for supported_version in supported_versions %}
{{ supported_version }}
---------------------------
{% for supported_architecture in supported_architectures %}

{{ supported_architecture }}
^^^^^^^^^^^^^^^^^^

.. json-table::
   :file: source/_data/sbom-{{ supported_version }}/{{ supported_architecture.replace('/', '_') }}/sbom.spdx.json
   :path: predicate.packages
   :headers: Name, Version, License
   :columns: name, versionInfo, licenseDeclared


{% endfor %}
{% endfor %}