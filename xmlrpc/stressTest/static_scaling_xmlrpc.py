# static_scaling_xmlrpc.py

import xmlrpc.client
import multiprocessing
import time
import matplotlib.pyplot as plt

# ── Configuration ────────────────────────────────────────────────────
SERVER_PORTS    = [9000, 9001, 9002]   # the three server nodes you have running
HOST            = "localhost"
TOTAL_REQUESTS  = 1600                 # keep this constant for all N
NUM_PROCESSES   = 10                   # client‑side parallelism
# ────────────────────────────────────────────────────────────────────

def send_requests(args):
    """
    Each worker process:
      - args = (ports, per_proc, proc_index)
      - Round-robin across the given ports, issuing per_proc calls.
    """
    ports, per_proc, pid = args
    # build proxies for each node once
    proxies = [xmlrpc.client.ServerProxy(f"http://{HOST}:{p}", allow_none=True) for p in ports]
    calls = per_proc
    for i in range(calls):
        # pick node in round‑robin fashion
        proxy = proxies[i % len(proxies)]   #cycles through the proxies—this is round‑robin distribution of calls across N nodes.
        proxy.add_insult(f"node‑test from proc{pid} call{i}")
    return

def measure_time(ports):
    """
    Run the test against the given list of ports (nodes),
    return the elapsed time.
    """
    per_proc = TOTAL_REQUESTS // NUM_PROCESSES
    # prepare args for each client process
    tasks = [(ports, per_proc, pid) for pid in range(NUM_PROCESSES)]
    t0 = time.time()
    with multiprocessing.Pool(NUM_PROCESSES) as pool:
        pool.map(send_requests, tasks)
    return time.time() - t0

def main():
    times = []
    speedups = []
    Ns = [1, 2, 3]

    # Measure T1, T2, T3
    for N in Ns:
        ports = SERVER_PORTS[:N]
        tN = measure_time(ports)
        times.append(tN)
        print(f"N={N} nodes → time = {tN:.3f}s")

    # Compute speedups S(N) = T1 / T(N)
    T1 = times[0]
    speedups = [T1 / t for t in times]

    # Plot
    plt.plot(Ns, speedups, marker='o')
    plt.xticks(Ns)
    plt.xlabel("Number of InsultService nodes")
    plt.ylabel("Speedup (T₁ / Tₙ)")
    plt.title("Static Scaling: Speedup of InsultService (XMLRPC)")
    plt.grid(True)
    plt.show()

if __name__ == "__main__":
    main()
