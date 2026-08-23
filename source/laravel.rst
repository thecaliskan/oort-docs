Laravel
==========================

This guide walks through running every major Laravel long-running service on OORT — from scratch setup to production deployment across ``docker run``, Docker Compose, Docker Swarm, and Kubernetes.

Throughout this page, ``my-laravel-app`` refers to the image you built with the Dockerfile on the :doc:`usage` page.


Prerequisites
-------------

Before deploying, ensure your Laravel project has:

- PHP **{{ latest_version }}** compatibility (or your chosen OORT tag)
- **Redis** for queues, Horizon, Reverb, Pulse, and caching
- A **database** (PostgreSQL or MySQL) for application data
- Environment variables configured (``APP_KEY``, ``DB_*``, ``REDIS_*``, etc.)

Install Redis and database as separate containers or managed services — OORT runs only your PHP process.


Laravel Octane
-----------------------

**What it does**

Laravel Octane boots your application once and keeps it in memory, using Swoole to handle concurrent HTTP requests with dramatically lower latency than traditional PHP-FPM.

**When to use it**

Use Octane as your primary HTTP entry point for web traffic, APIs, and the Pulse dashboard.


Installation
^^^^^^^^^^^^

.. code-block:: bash

   composer require laravel/octane
   php artisan octane:install --server=swoole

This publishes the Octane configuration and adds Swoole server settings.


Configuration
^^^^^^^^^^^^^

The deployment examples below use ``curl`` against the ``/up`` endpoint. You must register this route in your application before health checks can succeed.

**Laravel 11+** — enable the health route in ``bootstrap/app.php``:

.. code-block:: php

   return Application::configure(basePath: dirname(__DIR__))
       ->withRouting(
           web: __DIR__.'/../routes/web.php',
           commands: __DIR__.'/../routes/console.php',
           health: '/up',
       )
       // ...

**Laravel 10 and earlier** — add a route that returns HTTP 200:

.. code-block:: php

   use Illuminate\Support\Facades\Route;

   Route::get('/up', fn () => response()->noContent());

Without an active ``/up`` endpoint, probes will fail and orchestrators may restart the container.

Key environment variables:

.. code-block:: text

   OCTANE_SERVER=swoole
   OCTANE_HTTPS=false

In ``config/octane.php``, review ``max_execution_time``, ``workers``, and ``task_workers`` for your workload.


Deployment
^^^^^^^^^^

.. tab-set::

   .. tab-item:: Docker Run

      .. code-block:: bash

         docker run -d \
           --name laravel-octane \
           -p 80:80 \
           --env-file .env \
           --health-cmd "curl -f http://localhost/up || exit 1" \
           --health-interval=30s \
           --health-timeout=10s \
           --health-retries=3 \
           my-laravel-app \
           php artisan octane:start --server=swoole --host=0.0.0.0 --port=80

   .. tab-item:: Docker Compose

      .. code-block:: yaml

         services:
           octane:
             image: my-laravel-app
             ports:
               - "80:80"
             env_file: .env
             command: php artisan octane:start --server=swoole --host=0.0.0.0 --port=80
             depends_on:
               redis:
                 condition: service_started
             healthcheck:
               test: ["CMD", "curl", "-f", "http://localhost/up"]
               interval: 30s
               timeout: 10s
               retries: 3
             restart: unless-stopped

   .. tab-item:: Docker Swarm

      .. code-block:: yaml

         services:
           octane:
             image: my-laravel-app
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
             command: php artisan octane:start --server=swoole --host=0.0.0.0 --port=80
             healthcheck:
               test: ["CMD", "curl", "-f", "http://localhost/up"]
               interval: 30s
               timeout: 10s
               retries: 3

   .. tab-item:: Kubernetes

      .. code-block:: yaml

         apiVersion: apps/v1
         kind: Deployment
         metadata:
           name: laravel-octane
         spec:
           replicas: 2
           selector:
             matchLabels:
               app: laravel-octane
           template:
             metadata:
               labels:
                 app: laravel-octane
             spec:
               containers:
                 - name: octane
                   image: my-laravel-app
                   ports:
                     - containerPort: 80
                   command: ["php", "artisan", "octane:start", "--server=swoole", "--host=0.0.0.0", "--port=80"]
                   envFrom:
                     - secretRef:
                         name: laravel-env
                   livenessProbe:
                     httpGet:
                       path: /up
                       port: 80
                     initialDelaySeconds: 15
                     periodSeconds: 10
                   readinessProbe:
                     httpGet:
                       path: /up
                       port: 80
                     initialDelaySeconds: 5
                     periodSeconds: 5
         ---
         apiVersion: v1
         kind: Service
         metadata:
           name: laravel-octane
         spec:
           selector:
             app: laravel-octane
           ports:
             - port: 80
               targetPort: 80


Laravel Horizon
---------------

**What it does**

Horizon provides a Redis-backed queue dashboard and a robust supervisor for Laravel queue workers. It manages worker processes, balancing, metrics, and failed-job handling.

**When to use it**

Use Horizon when you need managed queue workers with monitoring instead of a single ``queue:work`` process.


Installation
^^^^^^^^^^^^

.. code-block:: bash

   composer require laravel/horizon
   php artisan horizon:install
   php artisan migrate

Publish and customize ``config/horizon.php`` for your queue names, worker counts, and memory limits.


Configuration
^^^^^^^^^^^^^

.. code-block:: text

   QUEUE_CONNECTION=redis
   REDIS_HOST=redis
   REDIS_PORT=6379

Run migrations so Horizon's metadata tables exist. Protect the ``/horizon`` dashboard in production via ``Horizon::auth()`` in ``AppServiceProvider``.


Deployment
^^^^^^^^^^

.. tab-set::

   .. tab-item:: Docker Run

      .. code-block:: bash

         docker run -d \
           --name laravel-horizon \
           --env-file .env \
           --health-cmd "php artisan horizon:status || exit 1" \
           --health-interval=30s \
           --health-timeout=10s \
           --health-retries=3 \
           my-laravel-app \
           php artisan horizon

   .. tab-item:: Docker Compose

      .. code-block:: yaml

         services:
           horizon:
             image: my-laravel-app
             env_file: .env
             command: php artisan horizon
             depends_on:
               redis:
                 condition: service_started
             healthcheck:
               test: ["CMD", "php", "artisan", "horizon:status"]
               interval: 30s
               timeout: 10s
               retries: 3
             restart: unless-stopped

   .. tab-item:: Docker Swarm

      .. code-block:: yaml

         services:
           horizon:
             image: my-laravel-app
             deploy:
               replicas: 1
               restart_policy:
                 condition: on-failure
             env_file: .env
             command: php artisan horizon
             healthcheck:
               test: ["CMD", "php", "artisan", "horizon:status"]
               interval: 30s
               timeout: 10s
               retries: 3

   .. tab-item:: Kubernetes

      .. code-block:: yaml

         apiVersion: apps/v1
         kind: Deployment
         metadata:
           name: laravel-horizon
         spec:
           replicas: 1
           selector:
             matchLabels:
               app: laravel-horizon
           template:
             metadata:
               labels:
                 app: laravel-horizon
             spec:
               containers:
                 - name: horizon
                   image: my-laravel-app
                   command: ["php", "artisan", "horizon"]
                   envFrom:
                     - secretRef:
                         name: laravel-env
                   livenessProbe:
                     exec:
                       command: ["php", "artisan", "horizon:status"]
                     initialDelaySeconds: 30
                     periodSeconds: 30


Laravel Reverb
--------------

**What it does**

Reverb is Laravel's first-party WebSocket server for real-time broadcasting. It integrates with Laravel Echo and supports horizontal scaling via Redis.

**When to use it**

Use Reverb when your application needs WebSocket connections for live updates, notifications, or chat.


Installation
^^^^^^^^^^^^

.. code-block:: bash

   composer require laravel/reverb
   php artisan reverb:install

This publishes ``config/reverb.php`` and adds the required environment variables.


Configuration
^^^^^^^^^^^^^

.. code-block:: text

   REVERB_APP_ID=my-app-id
   REVERB_APP_KEY=my-app-key
   REVERB_APP_SECRET=my-app-secret
   REVERB_HOST=reverb
   REVERB_PORT=8080
   REVERB_SCHEME=http
   BROADCAST_CONNECTION=reverb

   VITE_REVERB_APP_KEY="${REVERB_APP_KEY}"
   VITE_REVERB_HOST="${REVERB_HOST}"
   VITE_REVERB_PORT="${REVERB_PORT}"
   VITE_REVERB_SCHEME="${REVERB_SCHEME}"

The deployment examples below probe ``http://localhost:8080/up`` on the Reverb server process. Recent ``laravel/reverb`` releases expose this endpoint automatically when ``reverb:start`` is running — it responds with ``{"health":"OK"}`` and requires no extra route in ``routes/web.php``.

If probes fail after deploy, confirm your Reverb version includes the ``/up`` endpoint and that the health check port matches ``--port`` in the ``reverb:start`` command.


Deployment
^^^^^^^^^^

.. tab-set::

   .. tab-item:: Docker Run

      .. code-block:: bash

         docker run -d \
           --name laravel-reverb \
           -p 8080:8080 \
           --env-file .env \
           --health-cmd "curl -f http://localhost:8080/up || exit 1" \
           --health-interval=30s \
           --health-timeout=10s \
           --health-retries=3 \
           my-laravel-app \
           php artisan reverb:start --host=0.0.0.0 --port=8080

   .. tab-item:: Docker Compose

      .. code-block:: yaml

         services:
           reverb:
             image: my-laravel-app
             ports:
               - "8080:8080"
             env_file: .env
             command: php artisan reverb:start --host=0.0.0.0 --port=8080
             depends_on:
               redis:
                 condition: service_started
             healthcheck:
               test: ["CMD", "curl", "-f", "http://localhost:8080/up"]
               interval: 30s
               timeout: 10s
               retries: 3
             restart: unless-stopped

   .. tab-item:: Docker Swarm

      .. code-block:: yaml

         services:
           reverb:
             image: my-laravel-app
             deploy:
               replicas: 1
               restart_policy:
                 condition: on-failure
             ports:
               - target: 8080
                 published: 8080
                 protocol: tcp
                 mode: host
             env_file: .env
             command: php artisan reverb:start --host=0.0.0.0 --port=8080
             healthcheck:
               test: ["CMD", "curl", "-f", "http://localhost:8080/up"]
               interval: 30s
               timeout: 10s
               retries: 3

   .. tab-item:: Kubernetes

      .. code-block:: yaml

         apiVersion: apps/v1
         kind: Deployment
         metadata:
           name: laravel-reverb
         spec:
           replicas: 1
           selector:
             matchLabels:
               app: laravel-reverb
           template:
             metadata:
               labels:
                 app: laravel-reverb
             spec:
               containers:
                 - name: reverb
                   image: my-laravel-app
                   ports:
                     - containerPort: 8080
                   command: ["php", "artisan", "reverb:start", "--host=0.0.0.0", "--port=8080"]
                   envFrom:
                     - secretRef:
                         name: laravel-env
                   livenessProbe:
                     httpGet:
                       path: /up
                       port: 8080
                     initialDelaySeconds: 15
                     periodSeconds: 10
                   readinessProbe:
                     httpGet:
                       path: /up
                       port: 8080
                     initialDelaySeconds: 5
                     periodSeconds: 5
         ---
         apiVersion: v1
         kind: Service
         metadata:
           name: laravel-reverb
         spec:
           selector:
             app: laravel-reverb
           ports:
             - port: 8080
               targetPort: 8080


Laravel Queue
--------------------------

**What it does**

``queue:work`` runs a single Laravel queue worker process that listens on a queue connection and processes jobs one at a time (or in parallel with ``--workers``).

**When to use it**

Use a standalone ``queue:work`` container when you need a simple worker without Horizon's dashboard and process management — for example, a dedicated queue name or a lightweight setup.


Installation
^^^^^^^^^^^^

Queue support is built into Laravel. Configure your connection in ``config/queue.php``:

.. code-block:: text

   QUEUE_CONNECTION=redis


Configuration
^^^^^^^^^^^^^

Tune worker options for production:

- ``--sleep=3`` — seconds to wait when no jobs are available
- ``--tries=3`` — max attempts per job
- ``--max-time=3600`` — restart worker after one hour (prevents memory leaks)
- ``--queue=high,default`` — process specific queues in priority order


Deployment
^^^^^^^^^^

.. tab-set::

   .. tab-item:: Docker Run

      .. code-block:: bash

         docker run -d \
           --name laravel-queue \
           --env-file .env \
           my-laravel-app \
           php artisan queue:work redis --sleep=3 --tries=3 --max-time=3600

   .. tab-item:: Docker Compose

      .. code-block:: yaml

         services:
           queue:
             image: my-laravel-app
             env_file: .env
             command: php artisan queue:work redis --sleep=3 --tries=3 --max-time=3600
             depends_on:
               redis:
                 condition: service_started
             restart: unless-stopped

   .. tab-item:: Docker Swarm

      .. code-block:: yaml

         services:
           queue:
             image: my-laravel-app
             deploy:
               replicas: 2
               restart_policy:
                 condition: on-failure
             env_file: .env
             command: php artisan queue:work redis --sleep=3 --tries=3 --max-time=3600

   .. tab-item:: Kubernetes

      .. code-block:: yaml

         apiVersion: apps/v1
         kind: Deployment
         metadata:
           name: laravel-queue
         spec:
           replicas: 2
           selector:
             matchLabels:
               app: laravel-queue
           template:
             metadata:
               labels:
                 app: laravel-queue
             spec:
               containers:
                 - name: queue
                   image: my-laravel-app
                   command:
                     - php
                     - artisan
                     - queue:work
                     - redis
                     - --sleep=3
                     - --tries=3
                     - --max-time=3600
                   envFrom:
                     - secretRef:
                         name: laravel-env


Laravel Scheduler
-----------------

**What it does**

The scheduler runs recurring Artisan commands — reports, cleanups, cache refreshes, and any ``Schedule::`` definitions in ``routes/console.php`` or ``app/Console/Kernel.php``.

**When to use it**

Run ``schedule:work`` as a long-lived process (recommended in containers) instead of relying on host-level cron.


Installation
^^^^^^^^^^^^

Scheduling is built into Laravel. Define tasks in ``routes/console.php`` (Laravel 11+) or ``app/Console/Kernel.php``:

.. code-block:: php

   use Illuminate\Support\Facades\Schedule;

   Schedule::command('reports:daily')->dailyAt('01:00');
   Schedule::command('cache:prune-stale-tags')->hourly();


Configuration
^^^^^^^^^^^^^

``schedule:work`` polls every minute and is ideal for container environments — no cron daemon required.


Deployment
^^^^^^^^^^

.. tab-set::

   .. tab-item:: Docker Run

      .. code-block:: bash

         docker run -d \
           --name laravel-scheduler \
           --env-file .env \
           my-laravel-app \
           php artisan schedule:work

   .. tab-item:: Docker Compose

      .. code-block:: yaml

         services:
           scheduler:
             image: my-laravel-app
             env_file: .env
             command: php artisan schedule:work
             restart: unless-stopped

   .. tab-item:: Docker Swarm

      .. code-block:: yaml

         services:
           scheduler:
             image: my-laravel-app
             deploy:
               replicas: 1
               restart_policy:
                 condition: on-failure
             env_file: .env
             command: php artisan schedule:work

   .. tab-item:: Kubernetes

      .. code-block:: yaml

         apiVersion: apps/v1
         kind: Deployment
         metadata:
           name: laravel-scheduler
         spec:
           replicas: 1
           selector:
             matchLabels:
               app: laravel-scheduler
           template:
             metadata:
               labels:
                 app: laravel-scheduler
             spec:
               containers:
                 - name: scheduler
                   image: my-laravel-app
                   command: ["php", "artisan", "schedule:work"]
                   envFrom:
                     - secretRef:
                         name: laravel-env


Laravel Pulse
-------------

**What it does**

Pulse is Laravel's real-time application performance monitor. It collects server, queue, slow query, and usage metrics and displays them in a web dashboard (typically served through Octane).

**When to use it**

Use Pulse for production observability. Run ``pulse:work`` as a separate ingest worker alongside your web container.


Installation
^^^^^^^^^^^^

.. code-block:: bash

   composer require laravel/pulse
   php artisan vendor:publish --provider="Laravel\Pulse\PulseServiceProvider"
   php artisan migrate

Access the dashboard at ``/pulse`` (protect it in production via ``Gate::define`` in ``AppServiceProvider``).


Configuration
^^^^^^^^^^^^^

.. code-block:: text

   PULSE_ENABLED=true
   PULSE_STORAGE_DRIVER=redis

The ``pulse:work`` command processes incoming metric events. The dashboard itself is served by Octane (or your web server).


Deployment
^^^^^^^^^^

.. tab-set::

   .. tab-item:: Docker Run

      .. code-block:: bash

         docker run -d \
           --name laravel-pulse \
           --env-file .env \
           my-laravel-app \
           php artisan pulse:work

   .. tab-item:: Docker Compose

      .. code-block:: yaml

         services:
           pulse:
             image: my-laravel-app
             env_file: .env
             command: php artisan pulse:work
             depends_on:
               redis:
                 condition: service_started
             restart: unless-stopped

   .. tab-item:: Docker Swarm

      .. code-block:: yaml

         services:
           pulse:
             image: my-laravel-app
             deploy:
               replicas: 1
               restart_policy:
                 condition: on-failure
             env_file: .env
             command: php artisan pulse:work

   .. tab-item:: Kubernetes

      .. code-block:: yaml

         apiVersion: apps/v1
         kind: Deployment
         metadata:
           name: laravel-pulse
         spec:
           replicas: 1
           selector:
             matchLabels:
               app: laravel-pulse
           template:
             metadata:
               labels:
                 app: laravel-pulse
             spec:
               containers:
                 - name: pulse
                   image: my-laravel-app
                   command: ["php", "artisan", "pulse:work"]
                   envFrom:
                     - secretRef:
                         name: laravel-env


Complete Laravel Stack
----------------------

This example runs every Laravel service on OORT in a single stack: Octane (HTTP), Horizon (queues), Reverb (WebSockets), Scheduler, Pulse, plus Redis and PostgreSQL.


Stack Overview
^^^^^^^^^^^^^^

.. list-table::
   :header-rows: 1

   * - Service
     - Role
     - Port
   * - ``octane``
     - HTTP application server (Swoole)
     - 80
   * - ``horizon``
     - Queue supervisor
     -
   * - ``reverb``
     - WebSocket server
     - 8080
   * - ``scheduler``
     - Scheduled tasks
     -
   * - ``pulse``
     - Metrics ingest worker
     -
   * - ``redis``
     - Queues, cache, broadcasting
     - 6379
   * - ``postgres``
     - Application database
     - 5432


.. tab-set::

   .. tab-item:: Docker Run

      Start dependencies first, then each Laravel service in its own container:

      .. code-block:: bash

         docker network create laravel-net

         docker run -d --name redis --network laravel-net redis:alpine
         docker run -d --name postgres --network laravel-net \
           -e POSTGRES_DB=laravel -e POSTGRES_PASSWORD=secret postgres:16-alpine

         docker run -d --name octane --network laravel-net -p 80:80 --env-file .env \
           my-laravel-app php artisan octane:start --server=swoole --host=0.0.0.0 --port=80

         docker run -d --name horizon --network laravel-net --env-file .env \
           my-laravel-app php artisan horizon

         docker run -d --name reverb --network laravel-net -p 8080:8080 --env-file .env \
           --health-cmd "curl -f http://localhost:8080/up || exit 1" \
           --health-interval=30s --health-timeout=10s --health-retries=3 \
           my-laravel-app php artisan reverb:start --host=0.0.0.0 --port=8080

         docker run -d --name scheduler --network laravel-net --env-file .env \
           my-laravel-app php artisan schedule:work

         docker run -d --name pulse --network laravel-net --env-file .env \
           my-laravel-app php artisan pulse:work

   .. tab-item:: Docker Compose

      .. code-block:: yaml

         services:
           octane:
             image: my-laravel-app
             ports:
               - "80:80"
             env_file: .env
             command: php artisan octane:start --server=swoole --host=0.0.0.0 --port=80
             depends_on:
               redis:
                 condition: service_started
               postgres:
                 condition: service_started
             healthcheck:
               test: ["CMD", "curl", "-f", "http://localhost/up"]
               interval: 30s
               timeout: 10s
               retries: 3
             restart: unless-stopped

           horizon:
             image: my-laravel-app
             env_file: .env
             command: php artisan horizon
             depends_on:
               redis:
                 condition: service_started
             healthcheck:
               test: ["CMD", "php", "artisan", "horizon:status"]
               interval: 30s
               timeout: 10s
               retries: 3
             restart: unless-stopped

           reverb:
             image: my-laravel-app
             ports:
               - "8080:8080"
             env_file: .env
             command: php artisan reverb:start --host=0.0.0.0 --port=8080
             depends_on:
               redis:
                 condition: service_started
             healthcheck:
               test: ["CMD", "curl", "-f", "http://localhost:8080/up"]
               interval: 30s
               timeout: 10s
               retries: 3
             restart: unless-stopped

           scheduler:
             image: my-laravel-app
             env_file: .env
             command: php artisan schedule:work
             restart: unless-stopped

           pulse:
             image: my-laravel-app
             env_file: .env
             command: php artisan pulse:work
             depends_on:
               redis:
                 condition: service_started
             restart: unless-stopped

           redis:
             image: redis:alpine
             restart: unless-stopped

           postgres:
             image: postgres:16-alpine
             environment:
               POSTGRES_DB: laravel
               POSTGRES_USER: laravel
               POSTGRES_PASSWORD: secret
             volumes:
               - postgres_data:/var/lib/postgresql/data
             restart: unless-stopped

         volumes:
           postgres_data:

   .. tab-item:: Docker Swarm

      .. code-block:: yaml

         services:
           octane:
             image: my-laravel-app
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
             command: php artisan octane:start --server=swoole --host=0.0.0.0 --port=80
             healthcheck:
               test: ["CMD", "curl", "-f", "http://localhost/up"]
               interval: 30s
               timeout: 10s
               retries: 3

           horizon:
             image: my-laravel-app
             deploy:
               replicas: 1
               restart_policy:
                 condition: on-failure
             env_file: .env
             command: php artisan horizon

           reverb:
             image: my-laravel-app
             deploy:
               replicas: 1
               restart_policy:
                 condition: on-failure
             ports:
               - target: 8080
                 published: 8080
                 protocol: tcp
                 mode: host
             env_file: .env
             command: php artisan reverb:start --host=0.0.0.0 --port=8080
             healthcheck:
               test: ["CMD", "curl", "-f", "http://localhost:8080/up"]
               interval: 30s
               timeout: 10s
               retries: 3

           scheduler:
             image: my-laravel-app
             deploy:
               replicas: 1
               restart_policy:
                 condition: on-failure
             env_file: .env
             command: php artisan schedule:work

           pulse:
             image: my-laravel-app
             deploy:
               replicas: 1
               restart_policy:
                 condition: on-failure
             env_file: .env
             command: php artisan pulse:work

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
               POSTGRES_DB: laravel
               POSTGRES_USER: laravel
               POSTGRES_PASSWORD: secret

   .. tab-item:: Kubernetes

      .. code-block:: yaml

         apiVersion: v1
         kind: Secret
         metadata:
           name: laravel-env
         type: Opaque
         stringData:
           APP_KEY: "base64:your-app-key"
           APP_ENV: production
           DB_CONNECTION: pgsql
           DB_HOST: postgres
           DB_PORT: "5432"
           DB_DATABASE: laravel
           DB_USERNAME: laravel
           DB_PASSWORD: secret
           REDIS_HOST: redis
           REDIS_PORT: "6379"
           QUEUE_CONNECTION: redis
           CACHE_STORE: redis
           BROADCAST_CONNECTION: reverb
           OCTANE_SERVER: swoole
           PULSE_ENABLED: "true"
           PULSE_STORAGE_DRIVER: redis
         ---
         apiVersion: apps/v1
         kind: Deployment
         metadata:
           name: laravel-octane
         spec:
           replicas: 2
           selector:
             matchLabels:
               app: laravel-octane
           template:
             metadata:
               labels:
                 app: laravel-octane
             spec:
               containers:
                 - name: octane
                   image: my-laravel-app
                   ports:
                     - containerPort: 80
                   command: ["php", "artisan", "octane:start", "--server=swoole", "--host=0.0.0.0", "--port=80"]
                   envFrom:
                     - secretRef:
                         name: laravel-env
                   livenessProbe:
                     httpGet:
                       path: /up
                       port: 80
                     initialDelaySeconds: 15
                     periodSeconds: 10
         ---
         apiVersion: v1
         kind: Service
         metadata:
           name: laravel-octane
         spec:
           selector:
             app: laravel-octane
           ports:
             - port: 80
               targetPort: 80
         ---
         apiVersion: apps/v1
         kind: Deployment
         metadata:
           name: laravel-horizon
         spec:
           replicas: 1
           selector:
             matchLabels:
               app: laravel-horizon
           template:
             metadata:
               labels:
                 app: laravel-horizon
             spec:
               containers:
                 - name: horizon
                   image: my-laravel-app
                   command: ["php", "artisan", "horizon"]
                   envFrom:
                     - secretRef:
                         name: laravel-env
         ---
         apiVersion: apps/v1
         kind: Deployment
         metadata:
           name: laravel-reverb
         spec:
           replicas: 1
           selector:
             matchLabels:
               app: laravel-reverb
           template:
             metadata:
               labels:
                 app: laravel-reverb
             spec:
               containers:
                 - name: reverb
                   image: my-laravel-app
                   ports:
                     - containerPort: 8080
                   command: ["php", "artisan", "reverb:start", "--host=0.0.0.0", "--port=8080"]
                   envFrom:
                     - secretRef:
                         name: laravel-env
                   livenessProbe:
                     httpGet:
                       path: /up
                       port: 8080
                     initialDelaySeconds: 15
                     periodSeconds: 10
                   readinessProbe:
                     httpGet:
                       path: /up
                       port: 8080
                     initialDelaySeconds: 5
                     periodSeconds: 5
         ---
         apiVersion: v1
         kind: Service
         metadata:
           name: laravel-reverb
         spec:
           selector:
             app: laravel-reverb
           ports:
             - port: 8080
               targetPort: 8080
         ---
         apiVersion: apps/v1
         kind: Deployment
         metadata:
           name: laravel-scheduler
         spec:
           replicas: 1
           selector:
             matchLabels:
               app: laravel-scheduler
           template:
             metadata:
               labels:
                 app: laravel-scheduler
             spec:
               containers:
                 - name: scheduler
                   image: my-laravel-app
                   command: ["php", "artisan", "schedule:work"]
                   envFrom:
                     - secretRef:
                         name: laravel-env
         ---
         apiVersion: apps/v1
         kind: Deployment
         metadata:
           name: laravel-pulse
         spec:
           replicas: 1
           selector:
             matchLabels:
               app: laravel-pulse
           template:
             metadata:
               labels:
                 app: laravel-pulse
             spec:
               containers:
                 - name: pulse
                   image: my-laravel-app
                   command: ["php", "artisan", "pulse:work"]
                   envFrom:
                     - secretRef:
                         name: laravel-env
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
                       value: laravel
                     - name: POSTGRES_USER
                       value: laravel
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
