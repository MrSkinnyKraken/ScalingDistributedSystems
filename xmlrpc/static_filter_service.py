#!/usr/bin/env python3
# static_insult_filter_service.py

from xmlrpc.server import SimpleXMLRPCServer
import argparse
from multiprocessing import Manager, Pool
import time

# list of insults to censor
INSULTS = ["stupid", "idiot", "dumb"]

def censor_text(text):
    """Helper: replace insults with CENSORED."""
    out = text
    for w in INSULTS:
        out = out.replace(w, "CENSORED")
    return out

class InsultFilterFrontEnd:
    def __init__(self, store_list, workers):
        """
        store_list: Manager().list() where submitted texts accumulate
        workers: number of parallel processes to use in get_results()
        """
        self._store   = store_list
        self._workers = workers

    def submit_text(self, text):
        self._store.append(text)
        return "Text submitted."

    def get_results(self):
        """
        This method is where the “work” happens.  We:
          1. snapshot all pending texts in one list
          2. clear the shared store
          3. use a multiprocessing.Pool of size self._workers
             to censor them in parallel
          4. return the filtered list
        """
        # 1) snapshot & clear
        pending = list(self._store)
        del self._store[:]  

        # 2) parallel filter
        if not pending:
            return []
        with Pool(self._workers) as p:
            results = p.map(censor_text, pending)

        return results

def main():
    p = argparse.ArgumentParser(description="Static‑scaling XMLRPC InsultFilterService")
    p.add_argument("--host",    default="localhost", help="Bind host")
    p.add_argument("--port",    type=int, default=9001,      help="Bind port")
    p.add_argument("--workers", type=int, default=1, choices=[1,2,3],
                   help="Number of parallel worker processes for filtering")
    args = p.parse_args()

    mgr    = Manager()
    store  = mgr.list()  # holds submitted texts

    front = InsultFilterFrontEnd(store, args.workers)
    server = SimpleXMLRPCServer((args.host, args.port),
                                allow_none=True, logRequests=False)
    server.register_instance(front)
    print(f"Static InsultFilterService on {args.host}:{args.port} with {args.workers} workers")
    server.serve_forever()

if __name__=="__main__":
    main()
