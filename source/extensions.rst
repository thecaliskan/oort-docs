Extensions
==============

PHP extensions loaded in each **OORT** image, grouped by PHP version and architecture. CI verifies extension loading on every supported platform before each image is published.

Bundled extensions
------------------

Every OORT image ships with these extensions enabled and verified in CI:

- **PECL** — igbinary, redis, swoole, ssh2
- **Core** — bcmath, ftp, intl, pcntl, pdo_mysql, pdo_pgsql, zip

The tables below list every extension PHP reports as loaded, including runtime dependencies.


latest ({{ latest_version }})
---------------------------

{% for supported_architecture in supported_architectures %}

{{ supported_architecture }}
^^^^^^^^^^^^^^^^^^

.. json-table::
   :file: source/_data/php-extensions-{{ latest_version }}/php-extensions-{{ latest_version }}-{{ supported_architecture.replace('linux/', '') }}.json
   :headers: Name, Version
   :columns: name, version


{% endfor %}


{% for supported_version in supported_versions %}
{{ supported_version }}
---------------------------
{% for supported_architecture in supported_architectures %}

{{ supported_architecture }}
^^^^^^^^^^^^^^^^^^

.. json-table::
   :file: source/_data/php-extensions-{{ supported_version }}/php-extensions-{{ supported_version }}-{{ supported_architecture.replace('linux/', '') }}.json
   :headers: Name, Version
   :columns: name, version


{% endfor %}
{% endfor %}
