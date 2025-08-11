"""
WSGI entrypoint for production servers (Gunicorn/Waitress).

Usage (Gunicorn):
  gunicorn -w 4 -k gthread --threads 8 -b 0.0.0.0:3000 wsgi:app

Usage (Waitress on Windows):
  waitress-serve --listen=0.0.0.0:3000 wsgi:app
"""

from web_application.backend import app

# Optional: expose 'application' for some WSGI hosts
application = app

if __name__ == "__main__":
    import os
    host = os.environ.get("HOST", "0.0.0.0")
    port = int(os.environ.get("PORT", "3000"))
    app.run(host=host, port=port)
