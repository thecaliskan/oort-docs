Security
===============

Supported Versions
------------------

The following versions of **OORT** are actively supported for security updates:

.. list-table::
   :header-rows: 1

   * - Version
     - Supported
     - Security Support Until
{% for version, support in version_security_supports.items() %}
   * - {{ version }}
     - ✅ Actively Supported
     - {{ support }}
{% endfor %}
   * - <= {{ no_longer_supported_version }}
     - ❌ No longer supported
     - End of Life

Known Vulnerabilities
--------------------------


{% for supported_version in supported_versions %}
{{ supported_version }}
^^^^^^^^^^^^^^^^^^

.. json-table::
   :file: source/_data/sarif-{{ supported_version }}/sarif.output.json
   :path: runs.0.results
   :headers: Vulnerability, Description
   :columns: ruleId, message.text
   :error_message: No known vulnerabilities found.

{% endfor %}

Reporting a Vulnerability
--------------------------

If you discover a security vulnerability in **OORT**, please **do not** create a public issue.
Instead, report it privately via email.

🔒 **Security Contact:** `security@thecaliskan.com <mailto:security@thecaliskan.com>`_

We will review your report and respond within **48 hours**. If the issue is confirmed as a valid vulnerability,
we will work on a fix and provide an estimated timeline for resolution.

Security Fix Process
--------------------

1. We validate and confirm the vulnerability.
2. A fix is developed in a private branch.
3. The fix is tested and released in a patched version.
4. The reporter will be credited (if they choose).
5. The vulnerability details will be disclosed after a fix is released.

Responsible Disclosure
----------------------

- Please allow us time to patch before publicly disclosing any vulnerabilities.
- If you believe a security issue poses an **immediate critical risk**, please include `[URGENT]` in your email subject.

Thanks for helping us keep **OORT** secure! 🚀
