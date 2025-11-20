Extensions
==============

This page provides a detailed list of all PHP extensions included in our Docker image.
You can use this as a reference to understand the image’s capabilities and manage dependencies effectively.


latest
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