from xmlrpc.server import SimpleXMLRPCServer
import argparse, random, time
from multiprocessing import Manager, Process, Queue

class InsultServiceFrontEnd:
    """XMLRPC methods: enqueue work or query state."""
    def __init__(self, task_queue, insults, subscribers):
        self._queue       = task_queue
        self._insults     = insults
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
        """RPC‐triggered broadcast to subscribers now."""
        if not self._insults or not self._subscribers:
            return "Nothing to broadcast."
        insult = random.choice(self._insults)
        for url in self._subscribers:
            try:
                import xmlrpc.client
                xmlrpc.client.ServerProxy(url, allow_none=True).notify(insult)
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
    p = argparse.ArgumentParser(description="Static‑scaling XMLRPC InsultService")
    p.add_argument("--host",    default="localhost", help="Bind host")
    p.add_argument("--port",    type=int, default=9000,      help="Bind port")
    p.add_argument("--workers", type=int, default=1,
                   choices=[1,2,3], help="Number of worker processes")
    args = p.parse_args()

    # Shared state via Manager
    mgr         = Manager()
    task_queue  = mgr.Queue()
    insults     = mgr.list(['stupid','lazy','ugly','smelly','dumb','slow'])
    subscribers = mgr.list()

    # Spawn the fixed pool of worker processes
    workers = []
    for i in range(args.workers):
        p = Process(target=worker_loop, args=(task_queue, insults), daemon=True)
        p.start()
        workers.append(p)
    print(f"Started {len(workers)} worker(s)")

    # Start XMLRPC front‐end
    server = SimpleXMLRPCServer((args.host, args.port),
                                allow_none=True, logRequests=False)
    front = InsultServiceFrontEnd(task_queue, insults, subscribers)
    server.register_instance(front)
    print(f"Static InsultService listening on {args.host}:{args.port} with {args.workers} workers")
    server.serve_forever()

if __name__=="__main__":
    main()
