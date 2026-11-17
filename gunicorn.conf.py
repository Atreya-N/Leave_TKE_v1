# Gunicorn configuration - run with:  gunicorn app:app
# (gunicorn automatically picks up gunicorn.conf.py from the current directory)

# 0.0.0.0 = listen on every network interface, so other machines on the LAN
# can connect. 127.0.0.1 would mean "this machine only".
bind = "0.0.0.0:8000"

# Number of worker processes. SQLite handles a few writers fine for a small
# office; keep this low.
workers = 2

# Log requests and errors to stdout/stderr (systemd's journal captures them).
accesslog = "-"
errorlog = "-"
loglevel = "info"

