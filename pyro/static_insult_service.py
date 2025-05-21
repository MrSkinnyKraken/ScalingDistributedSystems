# static_insult_service.py
import argparse
import random
import time
import Pyro4
from multiprocessing import Manager, Process, Queue

@Pyro4.expose
@Pyro4.behavior(instance_mode="single")
class InsultServiceFrontEnd:
    """XMLRPC/Pyro methods: enqueue work or query state."""
    def __init__(self, queue, insults, subscribers):
        self._queue = queue
        self._insults = insults
        self._subscribers = subscribers

    def add_insult(self, insult):
        """Enqueue an add_insult task for the worker pool."""
        self._queue.put(insult)
        return "Insult enqueued."

    def get_insults(self):
        """Return the current list of insults (processed so far)."""
        return list(self._insults)

    def register_subscriber(self, url):
        if url not in self._subscribers:
            self._subscribers.append(url)
            return f"Subscriber '{url}' registered."
        return f"Subscriber '{url}' already registered."

    def unregister_subscriber(self, url):
        if url in self._subscribers:
            self._subscribers.remove(url)
            return f"Subscriber '{url}' unregistered."
        return f"Subscriber '{url}' not found."

    def broadcast_insult(self):
        """RPC-triggered broadcast to subscribers now."""
        if not self._insults or not self._subscribers:
            return "Nothing to broadcast."
        insult = random.choice(self._insults)
        for url in self._subscribers:
            try:
                subscriber = Pyro4.Proxy(url)
                subscriber.notify(insult)
            except:
                pass
        return f"Broadcasted: {insult}"


def worker_loop(task_queue, insults):
    """Worker: pull insults from the queue and append if new."""
    while True:
        insult = task_queue.get()
        if insult not in insults:
            insults.append(insult)
        task_queue.task_done()


def main():
    p = argparse.ArgumentParser(description="Static-scaled Pyro InsultService")
    p.add_argument("--host", default="localhost", help="Bind host")
    p.add_argument("--port", type=int, default=9090, help="Bind port")
    p.add_argument("--workers", type=int, default=1, choices=[1,2,3],
                   help="Number of worker processes")
    args = p.parse_args()

    mgr = Manager()
    task_queue = mgr.Queue()
    insults = mgr.list(['stupid','lazy','ugly','smelly','dumb','slow'])
    subscribers = mgr.list()

    # Spawn workers
    workers = []
    for _ in range(args.workers):
        p = Process(target=worker_loop, args=(task_queue, insults), daemon=True)
        p.start()
        workers.append(p)
    print(f"[main] Started {len(workers)} worker(s)")

    # Start Pyro
    daemon = Pyro4.Daemon(host=args.host, port=args.port)
    ns = Pyro4.locateNS()
    uri = daemon.register(InsultServiceFrontEnd(task_queue, insults, subscribers))
    ns.register(f"example.insultservice{args.workers}", uri)
    print(f"[main] Pyro InsultService running with {args.workers} workers at {uri}")
    daemon.requestLoop()

if __name__ == "__main__":
    main()