# stress_test_static_insultS_pyro.py

import Pyro4
import multiprocessing
import time
import matplotlib.pyplot as plt

# ── Configuration ─────────────────────────────────────────────────────────────
PYRO_NAMES      = [
    "PYRONAME:example.insultservice1",
    "PYRONAME:example.insultservice2",
    "PYRONAME:example.insultservice3",
]
TOTAL_REQUESTS  = 7000
NUM_PROCESSES   = 10
# ────────────────────────────────────────────────────────────────────────────────

def send_requests(args):
    """
    Worker: each process sends per_proc add_insult() calls to the given URI.
    """
    uri, per_proc = args
    proxy = Pyro4.Proxy(uri)
    for i in range(per_proc):
        proxy.add_insult(f"stress-insult {i}")

def run_test_on_uri(uri):
    """
    Distribute TOTAL_REQUESTS across NUM_PROCESSES to proxy.add_insult(),
    return elapsed time.
    """
    per_proc = TOTAL_REQUESTS // NUM_PROCESSES
    tasks = [(uri, per_proc)] * NUM_PROCESSES
    t0 = time.time()
    with multiprocessing.Pool(NUM_PROCESSES) as pool:
        pool.map(send_requests, tasks)
    return time.time() - t0

def main():
    times = []
    print(f"Static InsultService (Pyro4) test: {TOTAL_REQUESTS} requests, {NUM_PROCESSES} clients\n")

    # sequentially test each name
    for uri in PYRO_NAMES:
        print(f"Testing {uri} ... ", end="", flush=True)
        t = run_test_on_uri(uri)
        print(f"{t:.3f}s")
        times.append(t)

    # compute speedup
    T1 = times[0]
    speedups = [T1 / t for t in times]

    print("\nNodes |   Time (s)   | Speedup")
    print("------|--------------|--------")
    for n, (t, s) in enumerate(zip(times, speedups), start=1):
        print(f"{n:5d} | {t:12.3f} | {s:6.3f}")

    # plot
    nodes = [1, 2, 3]
    plt.figure()
    plt.plot(nodes, speedups, marker='o')
    plt.xticks(nodes)
    plt.xlabel("Number of Service Instances")
    plt.ylabel("Speedup (T₁ / Tₙ)")
    plt.title("Static Scaling Speedup of InsultService (Pyro4)")
    plt.grid(True)
    plt.show()

if __name__ == "__main__":
    main()
