Extensions
==============

PHP extensions included in each **OORT** image, listed by version. Check here before deploying if your application depends on a specific extension.


latest ({{ latest_version }})
---------------------------

.. json-table::
   :file: source/_data/php-extensions-{{ latest_version }}/php-extensions-{{ latest_version }}.json
   :headers: Name, Version
   :columns: name, version

{% for supported_version in supported_versions %}
{{ supported_version }}
---------------------------

.. json-table::
   :file: source/_data/php-extensions-{{ supported_version }}/php-extensions-{{ supported_version }}.json
   :headers: Name, Version
   :columns: name, version

{% endfor %}