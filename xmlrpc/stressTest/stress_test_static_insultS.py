# stress_test_static_insultS.py

import xmlrpc.client
import multiprocessing
import time
import matplotlib.pyplot as plt

# ── Configuration ─────────────────────────────────────────────────────────────
PORTS           = [9000, 9001, 9002]  # 1, 2, 3-worker services
HOST            = "localhost"
TOTAL_REQUESTS  = 1200
NUM_PROCESSES   = 10
# ────────────────────────────────────────────────────────────────────────────────

def send_requests(args):
    """
    Worker: each process sends `per_proc` add_insult calls to the given port.
    """
    host, port, per_proc = args
    proxy = xmlrpc.client.ServerProxy(f"http://{host}:{port}", allow_none=True)
    for i in range(per_proc):
        proxy.add_insult(f"stress-insult {i}")

def run_test_on_port(port):
    """
    Distribute TOTAL_REQUESTS over NUM_PROCESSES against a single port,
    return elapsed time T.
    """
    per_proc = TOTAL_REQUESTS // NUM_PROCESSES
    tasks = [(HOST, port, per_proc)] * NUM_PROCESSES
    t0 = time.time()
    with multiprocessing.Pool(NUM_PROCESSES) as pool:
        pool.map(send_requests, tasks)
    return time.time() - t0

def main():
    times = []
    print(f"Static InsultService test: {TOTAL_REQUESTS} requests, {NUM_PROCESSES} clients")
    for port in PORTS:
        print(f"\nTesting port {port} ...")
        t = run_test_on_port(port)
        print(f"  Time on port {port}: {t:.3f} s")
        times.append(t)

    # Compute speedups S_n = T1 / Tn
    T1 = times[0]
    speedups = [T1 / t for t in times]

    # Print summary
    print("\nNumber of workers |  Time (s)  | Speedup")
    print("------------------|------------|--------")
    for n, (t, s) in enumerate(zip(times, speedups), start=1):
        print(f"{n:17d} | {t:10.3f} | {s:6.3f}")

    # Plot Speedup vs Workers
    workers = [1, 2, 3]
    plt.figure()
    plt.plot(workers, speedups, marker='o')
    plt.xticks(workers)
    plt.xlabel("Number of Worker Processes")
    plt.ylabel("Speedup (T₁ / Tₙ)")
    plt.title("Static Scaling Speedup of InsultService (XMLRPC)")
    plt.grid(True)
    plt.show()

if __name__ == "__main__":
    main()
