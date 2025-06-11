Usage
==========================

This section provides examples and guidance on how to use the features and tools supported by the environment. It covers common usage patterns, runtime configurations, and integration tips to help you get started quickly.

Dockerfile
--------------------------

This Dockerfile sets up the environment required to quickly run PHP-based projects. To use it, create this file in the root directory of your project. After that, simply follow the setup instructions in your project to start working with the containerized environment.

.. code-block:: dockerfile

    FROM thecaliskan/oort:latest

    COPY --chown=oort:oort . .

    RUN composer install --no-dev

The command below builds the Docker image using the Dockerfile in the current directory and tags it as ``my-oort-app``.

.. code-block:: bash

   docker build -t my-oort-app .

Laravel Octane
--------------------------

Laravel Octane is a high-performance application server for Laravel that utilizes Swoole to handle concurrent requests efficiently. It significantly improves application throughput and latency by keeping the framework bootstrapped in memory. When running Laravel Octane in containerized environments, it is important to properly configure health checks, such as enabling the /up endpoint, to ensure reliable operation.

.. tab-set::

   .. tab-item:: Docker Compose

      .. code-block:: yaml

         services:
           app:
             image: my-oort-app
             container_name: my-oort-app
             ports:
               - "80:80"
             command: php artisan octane:start --server=swoole --host=0.0.0.0 --port=80
             healthcheck:
               test: ["CMD", "curl", "-f", "http://localhost/up"]
               interval: 30s
               timeout: 10s
               retries: 3

   .. tab-item:: Docker Swarm

      .. code-block:: yaml

         services:
           app:
             image: my-oort-app
             container_name: my-oort-app
             deploy:
               replicas: 2
               restart_policy:
                 condition: on-failure
             ports:
               - target: 80
                 published: 80
                 protocol: tcp
                 mode: host
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
           name: my-oort-app
         spec:
           replicas: 2
           selector:
             matchLabels:
               app: my-oort-app
           template:
             metadata:
               labels:
                 app: my-oort-app
             spec:
               containers:
                 - name: my-oort-app
                   image: my-oort-app
                   ports:
                     - containerPort: 80
                   command: ["php", "artisan", "octane:start", "--server=swoole", "--host=0.0.0.0", "--port=80"]
                   livenessProbe:
                     httpGet:
                       path: /up
                       port: 80
                     initialDelaySeconds: 10
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
           name: my-oort-app
         spec:
           selector:
             app: my-oort-app
           ports:
             - protocol: TCP
               port: 80
               targetPort: 80

   .. tab-item:: Docker Run

      .. code-block:: bash

         docker run -p 80:80 --name my-oort-app --health-cmd "curl -f http://localhost/up || exit 1" --health-interval=30s --health-timeout=10s --health-retries=3 my-oort-app php artisan octane:start --server=swoole --host=0.0.0.0 --port=80
