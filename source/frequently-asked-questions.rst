Frequently Asked Questions
================================

1. **What is OORT?**

   **OORT** is a minimal Docker base image for PHP applications that run as long-lived processes — Laravel Octane, Horizon, Reverb, Symfony Runtime, Messenger workers, and similar workloads. It is not a full stack image: you build your application on top of it and run **one process per container**.

2. **How is OORT different from PHP-FPM images?**

   Traditional images pair PHP-FPM with nginx or Apache and spawn a new PHP process per request. OORT targets applications that stay booted in memory (Swoole via Octane or Symfony Runtime) or workers that loop indefinitely (queues, schedulers, WebSocket servers). There is no bundled web server — the container command is your application entry point.

3. **How do I deploy Laravel or Symfony on OORT?**

   Build an application image with a ``Dockerfile`` that starts from ``thecaliskan/oort:<php-version>``, install Composer dependencies at build time, then run separate containers per role (HTTP, queue, scheduler, etc.). See :doc:`usage/index` for Dockerfile templates and :doc:`usage/laravel` or :doc:`usage/symfony` for framework-specific guides.

4. **Which PHP and framework versions are supported?**

   OORT publishes PHP {% for version in supported_versions %}{{ version }}{% if not loop.last %}, {% endif %}{% endfor %} (default: **{{ latest_version }}**). CI tests Laravel **12** and **13** and Symfony **7.4**, **8.0**, and **8.1** on matching image versions. See :doc:`versions` for available tags and :doc:`usage/laravel` / :doc:`usage/symfony` for compatibility matrices.

5. **Should I pin a PHP version or use ``latest``?**

   Pin an explicit version in your ``FROM`` line (for example ``thecaliskan/oort:{{ latest_version }}``) so rebuilds stay predictable. The ``latest`` tag tracks the current default PHP release and may change when a new version becomes default. Match the tag to your application's PHP requirement and the framework matrix on the guide pages.

6. **Can I run the web server and queue worker in one container?**

   No — that is against the design. Build one image, then run multiple containers with different ``command`` values (Octane for HTTP, Horizon for queues, ``schedule:work`` for the scheduler, and so on). This applies equally to ``docker run``, Compose, Swarm, and Kubernetes.

7. **Where do Redis and the database run?**

   Outside the OORT container. Run Redis, PostgreSQL, or MySQL as separate containers or managed services and connect via environment variables. OORT runs only your PHP process.

8. **How often are images updated?**

   Images are rebuilt daily at approximately **03:00 UTC** with upstream package and security updates. The PHP version tag you pull does not change on rebuild — only the image contents behind that tag. See :doc:`versions`.

9. **How do I report a security vulnerability?**

   Email `security@thecaliskan.com <mailto:security@thecaliskan.com>`_ privately. Do not open a public issue. See :doc:`security` for the full disclosure process and supported PHP versions.
