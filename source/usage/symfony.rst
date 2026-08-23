Symfony
==========================

This guide covers running Symfony long-running services on OORT — from project setup to production deployment across ``docker run``, Docker Compose, Docker Swarm, and Kubernetes.

Throughout this page, ``my-symfony-app`` refers to the image you built with the Dockerfile on the :doc:`/usage/index` page.


Prerequisites
-------------

Before deploying, ensure your Symfony project has:

- A supported Symfony and OORT version pair (see `Supported Versions`_ below)
- PHP **{{ latest_version }}** compatibility (or your chosen OORT version)
- **Redis** for Messenger transport and cache
- A **database** for application data
- Environment variables configured (``APP_ENV``, ``DATABASE_URL``, ``REDIS_URL``, etc.)

Install Redis and database as separate containers or managed services.


Supported Versions
------------------

.. _symfony-supported-versions:

OORT images are tested in CI against the Symfony releases below on matching PHP versions. See :doc:`/versions` for image sizes and :doc:`/security` for support windows.

.. list-table::
   :header-rows: 1

   * - Symbol
     - Meaning
   * - ✅
     - **Tested** — CI runs against this Symfony and stable OORT version pair
   * - β
     - **Pre-release** — tested in CI on an RC OORT image (not a stable PHP release)
   * - —
     - **Not tested** — omitted from CI (typically incompatible PHP requirement)

Compatibility matrix
^^^^^^^^^^^^^^^^^^^^

.. list-table::
   :header-rows: 1
   :stub-columns: 2

   * - Symfony
     - PHP
{% for oort in compatibility_oort_versions %}
     - OORT {{ oort }}
{% endfor %}
{% for row in symfony_compat %}
   * - **{{ row.version }}**
     - {{ row.php }}
{% for oort in compatibility_oort_versions %}
     - {% if oort not in row.oort_versions %}—{% elif oort in compatibility_prerelease_oort_versions %}β{% else %}✅{% endif %}
{% endfor %}
{% endfor %}


Symfony Runtime
------------------------

**What it does**

The Symfony Runtime component with Swoole keeps your application bootstrapped in memory and handles HTTP requests through a high-performance async server — similar to Laravel Octane.

**When to use it**

Use Swoole Runtime as your primary HTTP entry point for web traffic and APIs.


Installation
^^^^^^^^^^^^

.. code-block:: bash

   composer require runtime/swoole symfony/runtime

Add runtime configuration to ``composer.json``:

.. code-block:: json

   {
       "extra": {
           "runtime": {
               "swoole": {
                   "host": "0.0.0.0",
                   "port": 80,
                   "mode": "SWOOLE_PROCESS",
                   "options": {
                       "worker_num": 4
                   }
               }
           }
       }
   }


Configuration
^^^^^^^^^^^^^

The Swoole runtime reads settings from ``composer.json`` ``extra.runtime.swoole``. Override at runtime with environment variables if needed:

.. code-block:: text

   APP_RUNTIME=Runtime\Swoole\Runtime
   APP_ENV=prod
   APP_SECRET=change-me
   DEFAULT_URI=http://localhost
   SWOOLE_HOST=0.0.0.0
   SWOOLE_PORT=80

Starting ``public/index.php`` boots the Swoole server when the runtime is configured.

The deployment examples below probe ``/health``. Add a lightweight route that returns HTTP 200 — Symfony does not register one by default:

.. code-block:: php

   namespace App\Controller;

   use Symfony\Component\HttpFoundation\Response;
   use Symfony\Component\Routing\Attribute\Route;

   final class HealthController
   {
       #[Route('/health', name: 'health', methods: ['GET'])]
       public function health(): Response
       {
           return new Response('OK');
       }
   }

Without this route, health checks will fail and orchestrators may restart the container.


Deployment
^^^^^^^^^^

.. tab-set::

   .. tab-item:: Docker Run

      .. code-block:: bash

         docker run -d \
           --name symfony-swoole \
           -p 80:80 \
           --env-file .env \
           --health-cmd "curl -f http://localhost/health || exit 1" \
           --health-interval=30s \
           --health-timeout=10s \
           --health-retries=3 \
           my-symfony-app \
           php public/index.php

   .. tab-item:: Docker Compose

      .. code-block:: yaml

         services:
           app:
             image: my-symfony-app
             ports:
               - "80:80"
             env_file: .env
             command: php public/index.php
             depends_on:
               redis:
                 condition: service_started
             healthcheck:
               test: ["CMD", "curl", "-f", "http://localhost/health"]
               interval: 30s
               timeout: 10s
               retries: 3
             restart: unless-stopped

   .. tab-item:: Docker Swarm

      .. code-block:: yaml

         services:
           app:
             image: my-symfony-app
             deploy:
               replicas: 2
               restart_policy:
                 condition: on-failure
               update_config:
                 parallelism: 1
                 delay: 10s
             ports:
               - target: 80
                 published: 80
                 protocol: tcp
                 mode: host
             env_file: .env
             command: php public/index.php
             healthcheck:
               test: ["CMD", "curl", "-f", "http://localhost/health"]
               interval: 30s
               timeout: 10s
               retries: 3

   .. tab-item:: Kubernetes

      .. code-block:: yaml

         apiVersion: apps/v1
         kind: Deployment
         metadata:
           name: symfony-app
         spec:
           replicas: 2
           selector:
             matchLabels:
               app: symfony-app
           template:
             metadata:
               labels:
                 app: symfony-app
             spec:
               containers:
                 - name: app
                   image: my-symfony-app
                   ports:
                     - containerPort: 80
                   command: ["php", "public/index.php"]
                   envFrom:
                     - secretRef:
                         name: symfony-env
                   livenessProbe:
                     httpGet:
                       path: /health
                       port: 80
                     initialDelaySeconds: 15
                     periodSeconds: 10
                   readinessProbe:
                     httpGet:
                       path: /health
                       port: 80
                     initialDelaySeconds: 5
                     periodSeconds: 5
         ---
         apiVersion: v1
         kind: Service
         metadata:
           name: symfony-app
         spec:
           selector:
             app: symfony-app
           ports:
             - port: 80
               targetPort: 80


Symfony Messenger
-----------------

**What it does**

Messenger routes messages (commands, events, queries) to handlers synchronously or asynchronously via transport backends like Redis, AMQP, or Doctrine.

**When to use it**

Run a ``messenger:consume`` worker container for every async transport your application defines.


Installation
^^^^^^^^^^^^

.. code-block:: bash

   composer require symfony/messenger

Configure transports in ``config/packages/messenger.yaml``:

.. code-block:: yaml

   framework:
       messenger:
           transports:
               async: '%env(MESSENGER_TRANSPORT_DSN)%'
           routing:
               'App\Message\AsyncMessage': async


Configuration
^^^^^^^^^^^^^

.. code-block:: text

   MESSENGER_TRANSPORT_DSN=redis://redis:6379/messages
   REDIS_URL=redis://redis:6379

List available transports:

.. code-block:: bash

   php bin/console debug: messenger


Deployment
^^^^^^^^^^

.. tab-set::

   .. tab-item:: Docker Run

      .. code-block:: bash

         docker run -d \
           --name symfony-messenger \
           --env-file .env \
           my-symfony-app \
           php bin/console messenger:consume async --time-limit=3600 --memory-limit=256M -vv

   .. tab-item:: Docker Compose

      .. code-block:: yaml

         services:
           messenger:
             image: my-symfony-app
             env_file: .env
             command: php bin/console messenger:consume async --time-limit=3600 --memory-limit=256M
             depends_on:
               redis:
                 condition: service_started
             restart: unless-stopped

   .. tab-item:: Docker Swarm

      .. code-block:: yaml

         services:
           messenger:
             image: my-symfony-app
             deploy:
               replicas: 2
               restart_policy:
                 condition: on-failure
             env_file: .env
             command: php bin/console messenger:consume async --time-limit=3600 --memory-limit=256M

   .. tab-item:: Kubernetes

      .. code-block:: yaml

         apiVersion: apps/v1
         kind: Deployment
         metadata:
           name: symfony-messenger
         spec:
           replicas: 2
           selector:
             matchLabels:
               app: symfony-messenger
           template:
             metadata:
               labels:
                 app: symfony-messenger
             spec:
               containers:
                 - name: messenger
                   image: my-symfony-app
                   command:
                     - php
                     - bin/console
                     - messenger:consume
                     - async
                     - --time-limit=3600
                     - --memory-limit=256M
                   envFrom:
                     - secretRef:
                         name: symfony-env


Symfony Scheduler
-----------------

**What it does**

The Scheduler component defines recurring tasks as messages. A dedicated Messenger transport (``scheduler_default``) dispatches scheduled messages to their handlers.

**When to use it**

Run a ``messenger:consume scheduler_default`` worker to process scheduled tasks without relying on host cron.


Installation
^^^^^^^^^^^^

.. code-block:: bash

   composer require symfony/scheduler

Define schedules as message classes with ``#[AsSchedule]`` or ``#[AsPeriodicTask]`` attributes:

.. code-block:: php

   namespace App\Task;

   use Symfony\Component\Scheduler\Attribute\AsPeriodicTask;

   #[AsPeriodicTask(frequency: '1 hour')]
   final class CleanupOldRecords
   {
       public function __invoke(): void
       {
           // cleanup logic
       }
   }


Configuration
^^^^^^^^^^^^^

The scheduler uses Messenger under the hood. Ensure ``framework.scheduler`` is enabled (auto-configured with the component).

Verify scheduled tasks:

.. code-block:: bash

   php bin/console debug:scheduler


Deployment
^^^^^^^^^^

.. tab-set::

   .. tab-item:: Docker Run

      .. code-block:: bash

         docker run -d \
           --name symfony-scheduler \
           --env-file .env \
           my-symfony-app \
           php bin/console messenger:consume scheduler_default --time-limit=3600

   .. tab-item:: Docker Compose

      .. code-block:: yaml

         services:
           scheduler:
             image: my-symfony-app
             env_file: .env
             command: php bin/console messenger:consume scheduler_default --time-limit=3600
             restart: unless-stopped

   .. tab-item:: Docker Swarm

      .. code-block:: yaml

         services:
           scheduler:
             image: my-symfony-app
             deploy:
               replicas: 1
               restart_policy:
                 condition: on-failure
             env_file: .env
             command: php bin/console messenger:consume scheduler_default --time-limit=3600

   .. tab-item:: Kubernetes

      .. code-block:: yaml

         apiVersion: apps/v1
         kind: Deployment
         metadata:
           name: symfony-scheduler
         spec:
           replicas: 1
           selector:
             matchLabels:
               app: symfony-scheduler
           template:
             metadata:
               labels:
                 app: symfony-scheduler
             spec:
               containers:
                 - name: scheduler
                   image: my-symfony-app
                   command:
                     - php
                     - bin/console
                     - messenger:consume
                     - scheduler_default
                     - --time-limit=3600
                   envFrom:
                     - secretRef:
                         name: symfony-env



Complete Symfony Stack
----------------------

This example runs every Symfony service on OORT in a single stack: Swoole Runtime (HTTP), Messenger worker, Scheduler worker, plus Redis and PostgreSQL.


Stack Overview
^^^^^^^^^^^^^^

.. list-table::
   :header-rows: 1

   * - Service
     - Role
     - Port
   * - ``app``
     - HTTP application server (Swoole)
     - 80
   * - ``messenger``
     - Async message consumer
     -
   * - ``scheduler``
     - Scheduled task consumer
     -
   * - ``redis``
     - Messenger transport, cache
     - 6379
   * - ``postgres``
     - Application database
     - 5432


.. tab-set::

   .. tab-item:: Docker Run

      .. code-block:: bash

         docker network create symfony-net

         docker run -d --name redis --network symfony-net redis:alpine
         docker run -d --name postgres --network symfony-net \
           -e POSTGRES_DB=symfony -e POSTGRES_PASSWORD=secret postgres:16-alpine

         docker run -d --name symfony-app --network symfony-net -p 80:80 --env-file .env \
           my-symfony-app php public/index.php

         docker run -d --name symfony-messenger --network symfony-net --env-file .env \
           my-symfony-app php bin/console messenger:consume async --time-limit=3600

         docker run -d --name symfony-scheduler --network symfony-net --env-file .env \
           my-symfony-app php bin/console messenger:consume scheduler_default --time-limit=3600

   .. tab-item:: Docker Compose

      .. code-block:: yaml

         services:
           app:
             image: my-symfony-app
             ports:
               - "80:80"
             env_file: .env
             command: php public/index.php
             depends_on:
               redis:
                 condition: service_started
               postgres:
                 condition: service_started
             healthcheck:
               test: ["CMD", "curl", "-f", "http://localhost/health"]
               interval: 30s
               timeout: 10s
               retries: 3
             restart: unless-stopped

           messenger:
             image: my-symfony-app
             env_file: .env
             command: php bin/console messenger:consume async --time-limit=3600 --memory-limit=256M
             depends_on:
               redis:
                 condition: service_started
             restart: unless-stopped

           scheduler:
             image: my-symfony-app
             env_file: .env
             command: php bin/console messenger:consume scheduler_default --time-limit=3600
             restart: unless-stopped

           redis:
             image: redis:alpine
             restart: unless-stopped

           postgres:
             image: postgres:16-alpine
             environment:
               POSTGRES_DB: symfony
               POSTGRES_USER: symfony
               POSTGRES_PASSWORD: secret
             volumes:
               - postgres_data:/var/lib/postgresql/data
             restart: unless-stopped

         volumes:
           postgres_data:

   .. tab-item:: Docker Swarm

      .. code-block:: yaml

         services:
           app:
             image: my-symfony-app
             deploy:
               replicas: 2
               restart_policy:
                 condition: on-failure
             ports:
               - target: 80
                 published: 80
                 protocol: tcp
                 mode: host
             env_file: .env
             command: php public/index.php
             healthcheck:
               test: ["CMD", "curl", "-f", "http://localhost/health"]
               interval: 30s
               timeout: 10s
               retries: 3

           messenger:
             image: my-symfony-app
             deploy:
               replicas: 2
               restart_policy:
                 condition: on-failure
             env_file: .env
             command: php bin/console messenger:consume async --time-limit=3600 --memory-limit=256M

           scheduler:
             image: my-symfony-app
             deploy:
               replicas: 1
               restart_policy:
                 condition: on-failure
             env_file: .env
             command: php bin/console messenger:consume scheduler_default --time-limit=3600

           redis:
             image: redis:alpine
             deploy:
               replicas: 1
               restart_policy:
                 condition: on-failure

           postgres:
             image: postgres:16-alpine
             deploy:
               replicas: 1
               restart_policy:
                 condition: on-failure
             environment:
               POSTGRES_DB: symfony
               POSTGRES_USER: symfony
               POSTGRES_PASSWORD: secret

   .. tab-item:: Kubernetes

      .. code-block:: yaml

         apiVersion: v1
         kind: Secret
         metadata:
           name: symfony-env
         type: Opaque
         stringData:
           APP_ENV: prod
           DATABASE_URL: "postgresql://symfony:secret@postgres:5432/symfony?serverVersion=16"
           MESSENGER_TRANSPORT_DSN: "redis://redis:6379/messages"
           REDIS_URL: "redis://redis:6379"
         ---
         apiVersion: apps/v1
         kind: Deployment
         metadata:
           name: symfony-app
         spec:
           replicas: 2
           selector:
             matchLabels:
               app: symfony-app
           template:
             metadata:
               labels:
                 app: symfony-app
             spec:
               containers:
                 - name: app
                   image: my-symfony-app
                   ports:
                     - containerPort: 80
                   command: ["php", "public/index.php"]
                   envFrom:
                     - secretRef:
                         name: symfony-env
                   livenessProbe:
                     httpGet:
                       path: /health
                       port: 80
                     initialDelaySeconds: 15
                     periodSeconds: 10
                   readinessProbe:
                     httpGet:
                       path: /health
                       port: 80
                     initialDelaySeconds: 5
                     periodSeconds: 5
         ---
         apiVersion: v1
         kind: Service
         metadata:
           name: symfony-app
         spec:
           selector:
             app: symfony-app
           ports:
             - port: 80
               targetPort: 80
         ---
         apiVersion: apps/v1
         kind: Deployment
         metadata:
           name: symfony-messenger
         spec:
           replicas: 2
           selector:
             matchLabels:
               app: symfony-messenger
           template:
             metadata:
               labels:
                 app: symfony-messenger
             spec:
               containers:
                 - name: messenger
                   image: my-symfony-app
                   command:
                     - php
                     - bin/console
                     - messenger:consume
                     - async
                     - --time-limit=3600
                     - --memory-limit=256M
                   envFrom:
                     - secretRef:
                         name: symfony-env
         ---
         apiVersion: apps/v1
         kind: Deployment
         metadata:
           name: symfony-scheduler
         spec:
           replicas: 1
           selector:
             matchLabels:
               app: symfony-scheduler
           template:
             metadata:
               labels:
                 app: symfony-scheduler
             spec:
               containers:
                 - name: scheduler
                   image: my-symfony-app
                   command:
                     - php
                     - bin/console
                     - messenger:consume
                     - scheduler_default
                     - --time-limit=3600
                   envFrom:
                     - secretRef:
                         name: symfony-env
         ---
         apiVersion: apps/v1
         kind: Deployment
         metadata:
           name: redis
         spec:
           replicas: 1
           selector:
             matchLabels:
               app: redis
           template:
             metadata:
               labels:
                 app: redis
             spec:
               containers:
                 - name: redis
                   image: redis:alpine
                   ports:
                     - containerPort: 6379
         ---
         apiVersion: v1
         kind: Service
         metadata:
           name: redis
         spec:
           selector:
             app: redis
           ports:
             - port: 6379
               targetPort: 6379
         ---
         apiVersion: apps/v1
         kind: Deployment
         metadata:
           name: postgres
         spec:
           replicas: 1
           selector:
             matchLabels:
               app: postgres
           template:
             metadata:
               labels:
                 app: postgres
             spec:
               containers:
                 - name: postgres
                   image: postgres:16-alpine
                   ports:
                     - containerPort: 5432
                   env:
                     - name: POSTGRES_DB
                       value: symfony
                     - name: POSTGRES_USER
                       value: symfony
                     - name: POSTGRES_PASSWORD
                       value: secret
         ---
         apiVersion: v1
         kind: Service
         metadata:
           name: postgres
         spec:
           selector:
             app: postgres
           ports:
             - port: 5432
               targetPort: 5432
