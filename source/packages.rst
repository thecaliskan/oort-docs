Packages
==============

OS packages bundled in each **OORT** image, grouped by PHP version and architecture. Use this page to audit dependencies or confirm what ships in a specific release.


latest ({{ latest_version }})
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