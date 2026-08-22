Symfony
==========================

This guide covers running Symfony long-running services on OORT — from project setup to production deployment across ``docker run``, Docker Compose, Docker Swarm, and Kubernetes.

Throughout this page, ``my-symfony-app`` refers to the image you built with the Dockerfile on the :doc:`usage` page.


Prerequisites
-------------

Before deploying, ensure your Symfony project has:

- PHP **{{ latest_version }}** compatibility (or your chosen OORT tag)
- **Redis** for Messenger transport and Mercure scaling
- A **database** for application data
- Environment variables configured (``APP_ENV``, ``DATABASE_URL``, ``REDIS_URL``, etc.)

Install Redis, Mercure hub, and database as separate containers or managed services.


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

Starting ``public/index.php`` boots the Swoole server when the runtime is configured.

The deployment examples below probe ``/health``. Add a lightweight route that returns HTTP 200 — Symfony does not register one by default:

.. code-block:: php

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

   use Symfony\Component\Scheduler\Attribute\AsPeriodicTask;

   #[AsPeriodicTask(frequency: '1 hour')]
   class CleanupOldRecords
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


Symfony Mercure
---------------

**What it does**

Mercure enables real-time updates via the Mercure protocol (Server-Sent Events). The Symfony Mercure bundle publishes updates from your application; the Mercure **hub** distributes them to subscribers.

**When to use it**

Use Mercure for live dashboards, notifications, and collaborative features. You typically run the Mercure hub as a separate container alongside your Symfony app.


Installation
^^^^^^^^^^^^

.. code-block:: bash

   composer require symfony/mercure-bundle

Configure the bundle in ``config/packages/mercure.yaml``:

.. code-block:: yaml

   mercure:
       hubs:
           default:
               url: '%env(MERCURE_URL)%'
               public_url: '%env(MERCURE_PUBLIC_URL)%'
               jwt:
                   secret: '%env(MERCURE_JWT_SECRET)%'
                   publish: ['*']


Configuration
^^^^^^^^^^^^^

**Symfony application**

.. code-block:: text

   MERCURE_URL=http://mercure:80/.well-known/mercure
   MERCURE_PUBLIC_URL=http://localhost:3000/.well-known/mercure
   MERCURE_JWT_SECRET=!ChangeThisMercureHubJWTSecretKey!

**Mercure hub** (separate container)

.. code-block:: text

   MERCURE_PUBLISHER_JWT_KEY=!ChangeThisMercureHubJWTSecretKey!
   MERCURE_SUBSCRIBER_JWT_KEY=!ChangeThisMercureHubJWTSecretKey!
   MERCURE_EXTRA_DIRECTIVES=cors_origins *

**Health checks**

The Mercure hub exposes transport-aware health endpoints on the Caddy admin API (default ``localhost:2019``). They verify that the hub can dispatch updates — not merely that the HTTP listener is up.

.. list-table::
   :header-rows: 1

   * - Endpoint
     - Use
   * - ``GET /mercure/health/ready``
     - Readiness — ``200`` when all transports can serve traffic, ``503`` otherwise
   * - ``GET /mercure/health/live``
     - Liveness — ``200`` when transports are operational; ``503`` after prolonged failure

The admin API binds to ``localhost`` for security, so probes must run **inside** the container (``exec`` / ``CMD`` with ``wget``), not as external ``httpGet`` checks against the public hub port.

Use a ``start_period`` of at least **60s** on first boot — BoltDB may need a moment to open before readiness passes.

Do not use the legacy ``/healthz`` endpoint on the main HTTP port; it only checks that Caddy is alive. See the official guide: `Mercure hub health check <https://mercure.rocks/docs/hub/config#healthcheck>`_.


Deployment
^^^^^^^^^^

.. tab-set::

   .. tab-item:: Docker Run

      Start the Mercure hub and Symfony app:

      .. code-block:: bash

         docker run -d \
           --name mercure \
           -p 3000:80 \
           -e MERCURE_PUBLISHER_JWT_KEY='!ChangeThisMercureHubJWTSecretKey!' \
           -e MERCURE_SUBSCRIBER_JWT_KEY='!ChangeThisMercureHubJWTSecretKey!' \
           -e MERCURE_EXTRA_DIRECTIVES='cors_origins *' \
           --health-cmd "wget -q --spider http://localhost:2019/mercure/health/ready || exit 1" \
           --health-interval=10s \
           --health-timeout=5s \
           --health-retries=5 \
           --health-start-period=60s \
           dunglas/mercure:v0.16

         docker run -d \
           --name symfony-app \
           -p 80:80 \
           --env-file .env \
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
               mercure:
                 condition: service_healthy
             restart: unless-stopped

           mercure:
             image: dunglas/mercure:v0.16
             ports:
               - "3000:80"
             environment:
               MERCURE_PUBLISHER_JWT_KEY: "!ChangeThisMercureHubJWTSecretKey!"
               MERCURE_SUBSCRIBER_JWT_KEY: "!ChangeThisMercureHubJWTSecretKey!"
               MERCURE_EXTRA_DIRECTIVES: "cors_origins *"
             healthcheck:
               test: ["CMD", "wget", "-q", "--spider", "http://localhost:2019/mercure/health/ready"]
               timeout: 5s
               retries: 5
               start_period: 60s
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
             ports:
               - target: 80
                 published: 80
                 protocol: tcp
                 mode: host
             env_file: .env
             command: php public/index.php

           mercure:
             image: dunglas/mercure:v0.16
             deploy:
               replicas: 1
               restart_policy:
                 condition: on-failure
             ports:
               - target: 80
                 published: 3000
                 protocol: tcp
                 mode: host
             environment:
               MERCURE_PUBLISHER_JWT_KEY: "!ChangeThisMercureHubJWTSecretKey!"
               MERCURE_SUBSCRIBER_JWT_KEY: "!ChangeThisMercureHubJWTSecretKey!"
               MERCURE_EXTRA_DIRECTIVES: "cors_origins *"
             healthcheck:
               test: ["CMD", "wget", "-q", "--spider", "http://localhost:2019/mercure/health/ready"]
               timeout: 5s
               retries: 5
               start_period: 60s

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
           name: mercure
         spec:
           replicas: 1
           selector:
             matchLabels:
               app: mercure
           template:
             metadata:
               labels:
                 app: mercure
             spec:
               containers:
                 - name: mercure
                   image: dunglas/mercure:v0.16
                   ports:
                     - containerPort: 80
                   env:
                     - name: MERCURE_PUBLISHER_JWT_KEY
                       value: "!ChangeThisMercureHubJWTSecretKey!"
                     - name: MERCURE_SUBSCRIBER_JWT_KEY
                       value: "!ChangeThisMercureHubJWTSecretKey!"
                     - name: MERCURE_EXTRA_DIRECTIVES
                       value: "cors_origins *"
                   readinessProbe:
                     exec:
                       command:
                         - wget
                         - -q
                         - --spider
                         - http://localhost:2019/mercure/health/ready
                     initialDelaySeconds: 10
                     periodSeconds: 10
                   livenessProbe:
                     exec:
                       command:
                         - wget
                         - -q
                         - --spider
                         - http://localhost:2019/mercure/health/live
                     initialDelaySeconds: 30
                     periodSeconds: 30
         ---
         apiVersion: v1
         kind: Service
         metadata:
           name: mercure
         spec:
           selector:
             app: mercure
           ports:
             - port: 80
               targetPort: 80


Complete Symfony Stack
----------------------

This example runs every Symfony service on OORT in a single stack: Swoole Runtime (HTTP), Messenger worker, Scheduler worker, Mercure hub, plus Redis and PostgreSQL.


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
   * - ``mercure``
     - Real-time event hub
     - 3000
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

         docker run -d --name mercure --network symfony-net -p 3000:80 \
           -e MERCURE_PUBLISHER_JWT_KEY='!ChangeThisMercureHubJWTSecretKey!' \
           -e MERCURE_SUBSCRIBER_JWT_KEY='!ChangeThisMercureHubJWTSecretKey!' \
           -e MERCURE_EXTRA_DIRECTIVES='cors_origins *' \
           --health-cmd "wget -q --spider http://localhost:2019/mercure/health/ready || exit 1" \
           --health-interval=10s --health-timeout=5s --health-retries=5 --health-start-period=60s \
           dunglas/mercure:v0.16

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
               mercure:
                 condition: service_healthy
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

           mercure:
             image: dunglas/mercure:v0.16
             ports:
               - "3000:80"
             environment:
               MERCURE_PUBLISHER_JWT_KEY: "!ChangeThisMercureHubJWTSecretKey!"
               MERCURE_SUBSCRIBER_JWT_KEY: "!ChangeThisMercureHubJWTSecretKey!"
               MERCURE_EXTRA_DIRECTIVES: "cors_origins *"
             healthcheck:
               test: ["CMD", "wget", "-q", "--spider", "http://localhost:2019/mercure/health/ready"]
               timeout: 5s
               retries: 5
               start_period: 60s
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

           mercure:
             image: dunglas/mercure:v0.16
             deploy:
               replicas: 1
               restart_policy:
                 condition: on-failure
             ports:
               - target: 80
                 published: 3000
                 protocol: tcp
                 mode: host
             environment:
               MERCURE_PUBLISHER_JWT_KEY: "!ChangeThisMercureHubJWTSecretKey!"
               MERCURE_SUBSCRIBER_JWT_KEY: "!ChangeThisMercureHubJWTSecretKey!"
               MERCURE_EXTRA_DIRECTIVES: "cors_origins *"
             healthcheck:
               test: ["CMD", "wget", "-q", "--spider", "http://localhost:2019/mercure/health/ready"]
               timeout: 5s
               retries: 5
               start_period: 60s

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
           MERCURE_URL: "http://mercure/.well-known/mercure"
           MERCURE_PUBLIC_URL: "http://localhost:3000/.well-known/mercure"
           MERCURE_JWT_SECRET: "!ChangeThisMercureHubJWTSecretKey!"
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
           name: mercure
         spec:
           replicas: 1
           selector:
             matchLabels:
               app: mercure
           template:
             metadata:
               labels:
                 app: mercure
             spec:
               containers:
                 - name: mercure
                   image: dunglas/mercure:v0.16
                   ports:
                     - containerPort: 80
                   env:
                     - name: MERCURE_PUBLISHER_JWT_KEY
                       value: "!ChangeThisMercureHubJWTSecretKey!"
                     - name: MERCURE_SUBSCRIBER_JWT_KEY
                       value: "!ChangeThisMercureHubJWTSecretKey!"
                     - name: MERCURE_EXTRA_DIRECTIVES
                       value: "cors_origins *"
                   readinessProbe:
                     exec:
                       command:
                         - wget
                         - -q
                         - --spider
                         - http://localhost:2019/mercure/health/ready
                     initialDelaySeconds: 10
                     periodSeconds: 10
                   livenessProbe:
                     exec:
                       command:
                         - wget
                         - -q
                         - --spider
                         - http://localhost:2019/mercure/health/live
                     initialDelaySeconds: 30
                     periodSeconds: 30
         ---
         apiVersion: v1
         kind: Service
         metadata:
           name: mercure
         spec:
           selector:
             app: mercure
           ports:
             - port: 80
               targetPort: 80
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
