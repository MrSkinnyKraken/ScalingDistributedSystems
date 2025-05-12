import argparse
import random
import time
import threading
import xmlrpc.client
from xmlrpc.server import SimpleXMLRPCServer
from multiprocessing import Manager, Process, Queue
from collections import deque

# ── Configuration ─────────────────────────────────────────────────────────────
MIN_WORKERS    = 1        # minimum workers
MAX_WORKERS    = 8        # maximum workers
C              = 4.9      # measured capacity per worker (req/sec)
T              = 1.0 / C  # average processing time per message
SCALE_INTERVAL = 1.0      # seconds between autoscaler runs
# ────────────────────────────────────────────────────────────────────────────────

class FrontEnd:
    """XMLRPC‐exposed methods: they enqueue tasks or read shared state."""
    def __init__(self, queue, insults, subscribers, timestamps):
        self._queue = queue
        self._insults = insults
        self._subs = subscribers
        self._timestamps = timestamps 

    def add_insult(self, insult):
        """Enqueue an add_insult task."""
        now = time.time()
        self._timestamps.append(now)                 # record arrival
        self._queue.put(("add_insult", insult))      # enqueue work
        return "Insult enqueued."

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
    
    def get_worker_count(self):
        """Return how many worker processes are currently alive (workers list in main)."""
        return len(workers)
        # This method is not thread-safe, but it's only for monitoring purposes.


def worker_loop(queue: Queue, insults, subscribers):
    """Worker process: consume tasks from the queue and apply them."""
    while True:
        task_type, payload = queue.get()
        if task_type == "add_insult":
            if payload not in insults:
                insults.append(payload)
        queue.task_done()

def autoscaler(task_queue, timestamps, workers):
    """
    Periodically compute λ over the last second, then:
        N_desired = floor((λ * T) / C)
    and spawn/kill workers to match N_desired.
    """
    while True:
        now = time.time()
        # purge timestamps older than 1s
        while timestamps and now - timestamps[0] > 1.0:
            timestamps.popleft()
        lam = len(timestamps)  # messages in last second

        # compute desired workers
        N_desired = int((lam * T) / C)
        # clamp
        N_desired = max(MIN_WORKERS, min(MAX_WORKERS, N_desired))

        # scale up
        while len(workers) < N_desired:
            p = Process(target=worker_loop, args=(task_queue, insults), daemon=True)
            p.start()
            workers.append(p)
            print(f"[autoscaler] +1 worker → {len(workers)}")

        # scale down
        while len(workers) > N_desired:
            w = workers.pop()
            w.terminate()
            print(f"[autoscaler] –1 worker → {len(workers)}")

        time.sleep(SCALE_INTERVAL)

if __name__ == "__main__":
    p = argparse.ArgumentParser(description="Dynamic‐scaling XMLRPC InsultService")
    p.add_argument("--host", default="localhost")
    p.add_argument("--port", type=int, default=9000)
    args = p.parse_args()

    mgr = Manager()
    task_queue = mgr.Queue()
    insults = mgr.list(['stupid','lazy','ugly','smelly','dumb','slow'])
    subscribers = mgr.list()
    timestamps = mgr.list() # timestamps of incoming requests

    # convert to collections.deque for efficient pops
    timestamps = deque()

    # Start initial worker pool
    workers = []
    for _ in range(MIN_WORKERS):
        p = Process(target=worker_loop, args=(task_queue, insults, subscribers), daemon=True)
        p.start(); workers.append(p)
    print(f"[main] Started {MIN_WORKERS} worker(s).")

    # Start autoscaler in its own thread
    threading.Thread(target=autoscaler, args=(task_queue, timestamps, workers), daemon=True).start()

    frontend = FrontEnd(task_queue, insults, subscribers, timestamps)
    # Start broadcaster thread
    #threading.Thread(target=frontend.broadcast_insult, daemon=True).start()

    # Start XMLRPC front‐end
    server = SimpleXMLRPCServer((args.host, args.port), allow_none=True, logRequests=False)
    server.register_instance(frontend)
    print(f"[main] Dynamic InsultService listening on {args.host}:{args.port}")
    server.serve_forever()