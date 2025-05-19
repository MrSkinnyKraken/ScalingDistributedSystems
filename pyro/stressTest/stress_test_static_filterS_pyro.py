# stress_test_static_filterS_pyro.py

import Pyro4
import multiprocessing
import time
import matplotlib.pyplot as plt

# ── Configuration ─────────────────────────────────────────────────────────────
PYRO_NAMES      = [
    "PYRONAME:example.insultfilter1",
    "PYRONAME:example.insultfilter2",
    "PYRONAME:example.insultfilter3",
]
TOTAL_REQUESTS  = 7000
NUM_PROCESSES   = 10
# ────────────────────────────────────────────────────────────────────────────────

def send_submissions(args):
    """
    Worker: each process submits per_proc texts via submit_text().
    """
    uri, per_proc = args
    proxy = Pyro4.Proxy(uri)
    for i in range(per_proc):
        proxy.submit_text(f"This is a stupid mistake #{i}")

def run_test_on_uri(uri):
    """
    Submit all texts in parallel, then call get_results() once.
    Return elapsed time for both phases.
    """
    per_proc = TOTAL_REQUESTS // NUM_PROCESSES
    tasks = [(uri, per_proc)] * NUM_PROCESSES

    t0 = time.time()
    # 1) parallel submissions
    with multiprocessing.Pool(NUM_PROCESSES) as pool:
        pool.map(send_submissions, tasks)
    # 2) trigger filtering
    proxy = Pyro4.Proxy(uri)
    _ = proxy.get_results()
    return time.time() - t0

def main():
    times = []
    print(f"Static InsultFilterService (Pyro4) test: {TOTAL_REQUESTS} submissions, {NUM_PROCESSES} clients\n")

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
    plt.plot(nodes, speedups, marker='s')
    plt.xticks(nodes)
    plt.xlabel("Number of Service Instances")
    plt.ylabel("Speedup (T₁ / Tₙ)")
    plt.title("Static Scaling Speedup of InsultFilterService (Pyro4)")
    plt.grid(True)
    plt.show()

if __name__ == "__main__":
    main()
