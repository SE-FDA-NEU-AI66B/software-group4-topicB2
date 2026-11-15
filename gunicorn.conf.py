"""Single-instance SQLite WSGI runtime; HTTPS is terminated by the hosting proxy."""

import os

bind = f"0.0.0.0:{int(os.environ.get('PORT', '8000'))}"
workers = 1
threads = 4
timeout = 30
errorlog = "-"
loglevel = "info"
# The app emits sanitized endpoint/status/duration events instead of raw URLs.
accesslog = None
