import time
import math
import random
import threading
import Pyro4
from multiprocessing import Manager, Process, Queue
from collections import deque

# ── Configuration ─────────────────────────────────────────────────────────────
PYRO_NAME      = "example.dynamic.insultservice"
MIN_WORKERS    = 1        # minimum worker processes
MAX_WORKERS    = 8        # maximum worker processes
C              = 4900.0    # measured per-worker capacity in calls/sec
SCALE_INTERVAL = 1.0      # how often (s) to recompute λ and scale
# ────────────────────────────────────────────────────────────────────────────────

@Pyro4.expose
@Pyro4.behavior(instance_mode="single")
class FrontEnd:
    def __init__(self, queue, insults, subscribers, timestamps, workers_ref):
        self._queue       = queue
        self._insults     = insults
        self._subs        = subscribers
        self._timestamps = timestamps
        self._workers    = workers_ref

    def add_insult(self, insult):
        # record arrival for λ
        now = time.time()
        self._timestamps.append(now)
        # enqueue work
        self._queue.put(insult)
        return "Insult enqueued."

    def get_insults(self):
        return list(self._insults)

    def register_subscriber(self, uri):
        if uri not in self._subs:
            self._subs.append(uri)
            return f"Subscriber '{uri}' registered."
        return f"Subscriber '{uri}' already registered."

    def unregister_subscriber(self, uri):
        if uri in self._subs:
            self._subs.remove(uri)
            return f"Subscriber '{uri}' unregistered."
        return f"Subscriber '{uri}' not found."

    def get_worker_count(self):
        return len(self._workers)

    def broadcast_insult(self):
        # manual RPC trigger: notify all subs immediately
        if not self._insults or not self._subs:
            return "No insults or subscribers."
        insult = random.choice(self._insults)
        for uri in self._subs:
            try:
                Pyro4.Proxy(uri).notify(insult)
            except:
                pass
        return f"Broadcasted: {insult}"

def worker_loop(task_queue, insults):
    """Consume insults from the queue and update the shared list."""
    while True:
        insult = task_queue.get()
        # simulate light processing
        if insult not in insults:
            insults.append(insult)
        task_queue.task_done()

def autoscaler(task_queue, timestamps, workers):
    """
    Periodically compute λ over the last second, then:
        N_desired = ceil(λ / C)
    and spawn/kill workers to match N_desired.
    """
    while True:
        time.sleep(SCALE_INTERVAL)
        # compute λ from the last 1 second
        now = time.time()
        while timestamps and now - timestamps[0] > SCALE_INTERVAL:
            timestamps.popleft()
        lam = len(timestamps)  # calls in last second

        N_desired = math.ceil(lam / C)
        N_desired = max(MIN_WORKERS, min(MAX_WORKERS, N_desired))

        # scale up
        while len(workers) < N_desired:
            p = Process(target=worker_loop, args=(task_queue, insults), daemon=True)
            p.start()
            workers.append(p)
            print(f"[autoscaler] +1 worker → {len(workers)} (λ={lam})")

        # scale down
        while len(workers) > N_desired:
            w = workers.pop()
            w.terminate()
            print(f"[autoscaler] –1 worker → {len(workers)} (λ={lam})")

if __name__ == "__main__":
    # shared structures via Manager
    mgr        = Manager()
    task_queue = mgr.Queue()
    insults    = mgr.list()  # start empty
    subscribers= mgr.list()
    # local deque for timestamps (fast pops)
    timestamps = deque()

    # start with MIN_WORKERS
    workers = []
    for _ in range(MIN_WORKERS):
        p = Process(target=worker_loop, args=(task_queue, insults), daemon=True)
        p.start(); workers.append(p)
    print(f"[main] Started {MIN_WORKERS} worker(s).")

    # launch autoscaler thread
    threading.Thread(target=autoscaler,
                     args=(task_queue, timestamps, workers),
                     daemon=True).start()

    # start Pyro front-end
    daemon = Pyro4.Daemon()
    ns     = Pyro4.locateNS()
    frontend = FrontEnd(task_queue, insults, subscribers, timestamps, workers)
    uri    = daemon.register(frontend)
    ns.register(PYRO_NAME, uri)
    print(f"[main] Dynamic Pyro InsultService up at {uri}")
    daemon.requestLoop()