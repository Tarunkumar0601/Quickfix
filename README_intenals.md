# Answers for Questions

## Multi-Site & Configuration

1. This App uses Standard Frappe config files `site_config.json` for site specific settings and `common_site_config.json` for value shared across all sites. Do no put passwords, API Keys or Other secrets into `common_site_config.json` , because it is often commited or copied across environments and expose sensitive data to every site using bench. If a secret is stored there by mistake, it can break security, cause developments to fail, and make it hard to keep different sites ceredentials isolated

2. When you run `bench start`, it launches four processes: `web` for HTTP requests, `worker` for background jobs, `scheduler` for scheduled tasks, and `socketio` for websocket and realtime notifications. If the `worker` process crashes, queued background jobs stop being processed until it is restarted. Any jobs already running may fail or remain in an incomplete state, and new jobs will accumulate in the queue. This can delay email sending, reports, and other asynchronous work until the worker is back online.

## Routing

1. Frappe finds it by parsing the URL to extract the app   name (quickfix), module name (api), and method name (get_job_summary), then dynamically importing the module and calling the function with the request data. If the function doesn't exist, Frappe will raise an ImportError or AttributeError.

2. When a browser hits /api/resource/Job Card/JC-2024-0001, Frappe treats it as a request to perform CRUD operations (Create, Read, Update, Delete) on a specific document of the "Job Card" DocType with the name "JC-2024-0001". This goes through Frappe's built-in ORM layer, which handles permissions, field validations, hooks, and database interactions automatically, without needing custom code.

3. When a browser hits /track-job, Frappe routes it to a custom page defined in the app's templates/pages/track-job/ directory. The handler is typically the track-job.py file (containing a get_context function for server-side data preparation) paired with track-job.html for the template, or just the HTML file for static content.

## Session & CSRF

1. The X-Frappe-CSRF-Token value in a POST request comes from the csrf_token cookie that Frappe sets in the browser when a user logs in or visits the site. This token is generated server-side using Frappe's session management and cryptography utilities, ensuring it's unique per session to prevent replay attacks.

> If you omit the X-Frappe-CSRF-Token header from a POST request, Frappe's CSRF protection middleware will reject it with a 403 Forbidden error, as it verifies the token against the session to block potential cross-site request forgery attempts. This is enforced in frappe.csrf.validate_csrf() or similar core functions.

2. frappe.session.data is a dictionary containing session-specific information for the current user in Frappe. It typically includes keys like 'user' (the logged-in username), 'csrf_token' (for CSRF protection), 'sid' (session ID), 'full_name', 'user_type', and other session metadata such as 'last_updated' or 'ip_address'. This data is stored in the session store (usually Redis or database) and is used to maintain user state across requests, enforce permissions, and secure operations. If no user is logged in, it may be empty or contain default values.

## Error visibility

1. With developer_mode: 1 enabled in site_config.json, triggering a Python exception in a whitelisted method (decorated with @frappe.whitelist()) causes Frappe to return a detailed error response to the browser instead of a sanitized one.

The browser receives a JSON object like:

```
{
  "exc": "Traceback (most recent call last):\n  File \"...\", line ..., in ...\n    raise Exception('Test error')\nException: Test error",
  "exc_type": "Exception",
  "message": "Test error",
  "_server_messages": "[\"Test error\"]"
}

```

2. With developer_mode: 0 (production mode), triggering a Python exception in a whitelisted method causes Frappe to return a generic sanitized error response to the browser:
```
{
  "message": "Internal Server Error",
  "exc": null,
  "exc_type": null,
  "_server_messages": ["An error occurred"]
}

```

3. In production mode with developer_mode: 0, errors are logged server-side in several places:

* Frappe Error Log – Stored in the database under the Error Log DocType, viewable by administrators in the Frappe UI at /app/error-log

* System logs – Written to disk at logs/ directory (e.g., error.log, bench.log)

* Error email notifications – If configured in site_config.json, emails are sent to specified admins with full error details

## Permission check location

1. When you call frappe.get_doc("Job Card", name) without ignore_permissions=True and the logged-in QF Technician user lacks read permission for that Job Card, Frappe raises:

 This error is raised at the ORM layer (in frappe/model/document.py) during the document loading process, before any of your method logic executes. The permission check happens inside frappe.get_doc() itself.

 From an API perspective, the request is stopped at the whitelist handler layer — the error bubbles up from get_doc(), is caught by the /api/method/ handler, and is returned to the browser as:

```
{
  "message": "User does not have permission to read",
  "exc_type": "PermissionError"
}
```

## ORM Internals & Query Builder

1. I ran the query and found:

* tabScheduled Job Log
* tabScheduled Job Type

> In Frappe, the database table convention is to prefix document tables with tab, so a DocType named Job Card maps to tabJob Card. This makes it easy to distinguish DocType tables from other tables and is part of Frappe’s ORM convention for document storage.

## Document Hooks & Recursion Pitfalls

### on_update() Recursion Pitfall

Calling `self.save()` inside an `on_update()` hook causes infinite recursion because the `save()` method triggers all `on_update` hooks, including the one that called it. This leads to a `RecursionError: maximum recursion depth exceeded` and can crash the application.

**Issues:**
- **Infinite Loop**: Each `save()` call re-triggers `on_update`, creating an endless cycle.
- **Performance Degradation**: Consumes stack space rapidly, leading to stack overflow.
- **Data Corruption Risk**: If the hook modifies data, repeated saves can overwrite changes unexpectedly.
- **Hard to Debug**: The error occurs deep in the call stack, making it difficult to trace back to the hook.

**Corrected Pattern:**
Use a flag to prevent re-entry into the hook. Set a temporary attribute (e.g., `self._updating_status = True`) before performing updates, and check it at the start. Reset it after the operation. This ensures the hook runs only once per save cycle.

Example:
```python
def on_update(self):
    if not getattr(self, '_updating_status', False):
        self._updating_status = True
        # Perform updates here
        self._updating_status = False
```

This pattern allows controlled updates without recursion while maintaining hook functionality. 