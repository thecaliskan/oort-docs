Usage
==========================

This section covers building your application image, deployment conventions, and per-framework guides for Laravel and Symfony.


Dockerfile
----------

Create a ``Dockerfile`` in your project root. Copy application code into the image and install Composer dependencies at build time.

**Laravel**

.. code-block:: dockerfile

   FROM thecaliskan/oort:{{ latest_version }}

   WORKDIR /var/www

   COPY --chown=oort:oort composer.json composer.lock ./
   RUN composer install --no-dev --no-scripts --no-autoloader

   COPY --chown=oort:oort . .
   RUN composer install --no-dev --optimize-autoloader

   RUN php artisan config:cache \
       && php artisan route:cache \
       && php artisan view:cache

.. code-block:: bash

   docker build -t my-laravel-app .


**Symfony**

.. code-block:: dockerfile

   FROM thecaliskan/oort:{{ latest_version }}

   WORKDIR /var/www

   COPY --chown=oort:oort composer.json composer.lock symfony.lock ./
   RUN composer install --no-dev --no-scripts --no-autoloader

   COPY --chown=oort:oort . .
   RUN composer install --no-dev --optimize-autoloader

   RUN php bin/console cache:clear --env=prod \
       && php bin/console cache:warmup --env=prod

.. code-block:: bash

   docker build -t my-symfony-app .


How OORT Runs
-------------

OORT follows **one container, one process**:

1. Build one application image per project.
2. Run separate containers per role (web, queue worker, scheduler, etc.).
3. Set the Artisan or Console command as the container ``command``.
4. Configure health checks and restart policies in your orchestrator.

This works the same across ``docker run``, Docker Compose, Docker Swarm, and Kubernetes.


Dependencies
------------

Typical external services:

- **Redis** — queues, broadcasting, caching
- **Database** — PostgreSQL or MySQL
- **Secrets** — via ``.env``, Compose ``environment``, or Kubernetes secrets (never in the image)


Framework Guides
----------------

Each guide includes zero-to-production setup for every supported service, with deployment examples in four tabs: **Docker Run**, **Docker Compose**, **Docker Swarm**, and **Kubernetes**.

.. grid:: 1 1 2 2
   :gutter: 3

   .. grid-item-card:: Laravel
      :link: laravel
      :link-type: doc

      Octane, Horizon, Reverb, Queue, Scheduler, Pulse, and a full stack example.

   .. grid-item-card:: Symfony
      :link: symfony
      :link-type: doc

      Runtime, Messenger, Scheduler, and a full stack example.


.. toctree::
    :titlesonly:
    :maxdepth: 2

    laravel
    symfony
