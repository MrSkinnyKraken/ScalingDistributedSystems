import argparse
import random
import time
import threading
import xmlrpc.client
from xmlrpc.server import SimpleXMLRPCServer
from multiprocessing import Manager, Process, Queue

# ── Configuration ─────────────────────────────────────────────────────────────
MIN_WORKERS    = 1        # never drop below this many workers
MAX_WORKERS    = 8        # never exceed this many
HIGH_WATER     = 50       # if queue length > HIGH_WATER, scale up
LOW_WATER      = 10       # if queue length < LOW_WATER, scale down
CHECK_INTERVAL = 1.0      # seconds between autoscaler checks
# ────────────────────────────────────────────────────────────────────────────────

class FrontEnd:
    """XMLRPC‐exposed methods: they enqueue tasks or read shared state."""
    def __init__(self, queue, insults, subscribers):
        self._queue = queue
        self._insults = insults
        self._subs = subscribers

    def add_insult(self, insult):
        """Enqueue an add_insult task."""
        self._queue.put(("add_insult", insult))
        return "Insult enqueued for addition."

    def get_insults(self):
        """Return the current insults list."""
        return list(self._insults)

    def register_subscriber(self, url):
        if url not in self._subs:
            self._subs.append(url)
            return f"Subscriber '{url}' registered."
        return f"Subscriber '{url}' already registered."

    def unregister_subscriber(self, url):
        if url in self._subs:
            self._subs.remove(url)
            return f"Subscriber '{url}' unregistered."
        return f"Subscriber '{url}' not found."

    def broadcast_insult(self):
        """Notify all subscribers every 5 seconds in a background thread."""
        while True:
            time.sleep(5)
            if self._insults and self._subs:
                insult = random.choice(self._insults)
                for url in self._subs:
                    try:
                        xmlrpc.client.ServerProxy(url, allow_none=True).notify(insult)
                    except:
                        pass

def worker_loop(queue: Queue, insults, subscribers):
    """Worker process: consume tasks from the queue and apply them."""
    while True:
        task_type, payload = queue.get()
        if task_type == "add_insult":
            if payload not in insults:
                insults.append(payload)
        queue.task_done()

def autoscaler(queue: Queue, workers):
    """Autoscaler thread/process: adjust number of workers to queue length."""
    while True:
        qlen = queue.qsize()
        # scale up?
        if qlen > HIGH_WATER and len(workers) < MAX_WORKERS:
            p = Process(target=worker_loop, args=(queue, insults, subscribers), daemon=True)
            p.start(); workers.append(p)
            print(f"[autoscaler] scaled UP to {len(workers)} workers (qlen={qlen})")
        # scale down?
        elif qlen < LOW_WATER and len(workers) > MIN_WORKERS:
            p = workers.pop()
            p.terminate()
            print(f"[autoscaler] scaled DOWN to {len(workers)} workers (qlen={qlen})")
        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    p = argparse.ArgumentParser(description="Dynamic‐scaling XMLRPC InsultService")
    p.add_argument("--host", default="localhost")
    p.add_argument("--port", type=int, default=9000)
    args = p.parse_args()

    mgr = Manager()
    queue = mgr.Queue()
    insults = mgr.list(['stupid','lazy','ugly','smelly','dumb','slow'])
    subscribers = mgr.list()

    # Start initial worker pool
    workers = []
    for _ in range(MIN_WORKERS):
        p = Process(target=worker_loop, args=(queue, insults, subscribers), daemon=True)
        p.start(); workers.append(p)
    print(f"[main] Started {MIN_WORKERS} worker(s).")

    # Start autoscaler in its own thread
    threading.Thread(target=autoscaler, args=(queue, workers), daemon=True).start()

    frontend = FrontEnd(queue, insults, subscribers)
    # Start broadcaster thread
    #threading.Thread(target=frontend.broadcast_insult, daemon=True).start()

    # Start XMLRPC front‐end
    server = SimpleXMLRPCServer((args.host, args.port), allow_none=True, logRequests=False)
    server.register_instance(frontend)
    print(f"[main] Dynamic InsultService listening on {args.host}:{args.port}")
    server.serve_forever()