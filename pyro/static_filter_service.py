# static_insult_filter_service.py
import argparse
import Pyro4
from multiprocessing import Manager, Pool

# insults to filter
INSULTS = ["stupid", "idiot", "dumb"]

def censor(text):
    out = text
    for w in INSULTS:
        out = out.replace(w, "CENSORED")
    return out

@Pyro4.expose
@Pyro4.behavior(instance_mode="single")
class InsultFilterFrontEnd:
    def __init__(self, store, workers):
        self._store = store
        self._workers = workers

    def submit_text(self, text):
        self._store.append(text)
        return "Text submitted."

    def get_results(self):
        pending = list(self._store)
        del self._store[:]
        if not pending:
            return []
        with Pool(self._workers) as p:
            results = p.map(censor, pending)
        return results


def main():
    p = argparse.ArgumentParser(description="Static-scaled Pyro InsultFilterService")
    p.add_argument("--host", default="localhost", help="Bind host")
    p.add_argument("--port", type=int, default=9091, help="Bind port")
    p.add_argument("--workers", type=int, default=1, choices=[1,2,3],
                   help="Number of filter worker processes")
    args = p.parse_args()

    mgr = Manager()
    store = mgr.list()

    front = InsultFilterFrontEnd(store, args.workers)

    daemon = Pyro4.Daemon(host=args.host, port=args.port)
    ns = Pyro4.locateNS()
    uri = daemon.register(front)
    ns.register(f"example.insultfilter{args.workers}", uri)
    print(f"[main] Pyro InsultFilterService with {args.workers} workers at {uri}")
    daemon.requestLoop()

if __name__ == "__main__":
    main()
