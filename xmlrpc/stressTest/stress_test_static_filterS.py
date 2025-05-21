#!/usr/bin/env python3
# stress_test_static_filterS.py

import xmlrpc.client
import multiprocessing
import time
import matplotlib.pyplot as plt

# ── Configuration ─────────────────────────────────────────────────────────────
HOST            = "localhost"
PORTS           = [9001, 9002, 9003]  # 1-, 2-, and 3-worker filter services
TOTAL_REQUESTS  = 1200
NUM_PROCESSES   = 10
# ────────────────────────────────────────────────────────────────────────────────

def send_submissions(args):
    """
    Worker: each process submits `per_proc` texts to the filter service at host:port.
    """
    host, port, per_proc = args
    proxy = xmlrpc.client.ServerProxy(f"http://{host}:{port}", allow_none=True)
    for i in range(per_proc):
        proxy.submit_text(f"This is a stupid mistake #{i}")

def run_test_on_port(port):
    """
    Distribute TOTAL_REQUESTS over NUM_PROCESSES for submit_text(),
    then call get_results() once to process the queue.
    Returns the elapsed time.
    """
    per_proc = TOTAL_REQUESTS // NUM_PROCESSES
    tasks = [(HOST, port, per_proc)] * NUM_PROCESSES

    t0 = time.time()
    # 1) Submit all texts in parallel
    with multiprocessing.Pool(NUM_PROCESSES) as pool:
        pool.map(send_submissions, tasks)
    # 2) Trigger processing and wait for results
    proxy = xmlrpc.client.ServerProxy(f"http://{HOST}:{port}", allow_none=True)
    _ = proxy.get_results()
    t1 = time.time()
    return t1 - t0

def main():
    times = []
    print(f"Static InsultFilterService test: {TOTAL_REQUESTS} submissions, {NUM_PROCESSES} clients")
    print()

    # run sequentially on each port
    for port in PORTS:
        print(f"Testing port {port} ... ", end="", flush=True)
        t = run_test_on_port(port)
        print(f"{t:.3f} s")
        times.append(t)

    # compute speedups S_n = T1 / Tn
    T1 = times[0]
    speedups = [T1 / t for t in times]

    # summary table
    print("\nWorkers |   Time (s)   | Speedup")
    print("--------|--------------|--------")
    for n, (t, s) in enumerate(zip(times, speedups), start=1):
        print(f"{n:7d} | {t:12.3f} | {s:6.3f}")

    # plot
    workers = [1, 2, 3]
    plt.figure()
    plt.plot(workers, speedups, marker='o')
    plt.xticks(workers)
    plt.xlabel("Number of Worker Processes")
    plt.ylabel("Speedup (T₁ / Tₙ)")
    plt.title("Static Scaling Speedup of InsultFilterService (XMLRPC)")
    plt.grid(True)
    plt.show()

if __name__ == "__main__":
    main()
