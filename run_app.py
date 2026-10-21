"""Start the web app.

In VS Code: open this file and press the ▶ Run button (top right of the editor).
Nothing to type. Your browser opens by itself.

To stop it: click the terminal panel at the bottom and press Ctrl+C,
or press the red square in the debug bar.
"""
import socket
import threading
import webbrowser

import uvicorn

HOST = "127.0.0.1"


def first_free_port(start=8000, tries=10):
    """Use 8000 if it is free, otherwise the next one that is."""
    for port in range(start, start + tries):
        with socket.socket() as s:
            if s.connect_ex((HOST, port)) != 0:      # nothing listening = free
                return port
    raise SystemExit(f"Ports {start}-{start + tries - 1} are all busy. "
                     f"Close the other app and try again.")


def main():
    port = first_free_port()
    url = f"http://{HOST}:{port}/app/"
    print("\n" + "=" * 58)
    print("  Verify-then-Warn is starting")
    print(f"  App   {url}")
    print(f"  API   http://{HOST}:{port}/docs")
    print("  Stop  click the terminal below, then press Ctrl+C")
    print("=" * 58 + "\n")
    threading.Timer(2.0, lambda: webbrowser.open(url)).start()
    uvicorn.run("api.main:app", host=HOST, port=port, reload=False)


if __name__ == "__main__":
    main()
