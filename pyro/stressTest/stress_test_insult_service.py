import multiprocessing
import time
import matplotlib.pyplot as plt
import Pyro4

# ── Configuration ──────────────────────────────────────────────────────────────
PYRO_NAME      = "example.insultservice"      # the Pyro name under which the service is registered
NUM_PROCESSES  = 10                           # fixed client‐side parallelism
REQUEST_STEPS  = [80000, 90000, 100000, 150000, 160000]   # total requests to sweep
# ────────────────────────────────────────────────────────────────────────────────

def send_requests(args):
    """
    Worker function: each process will send `reqs` add_insult calls.
    """
    uri, reqs = args
    proxy = Pyro4.Proxy(f"PYRONAME:{uri}")
    for i in range(reqs):
        proxy.add_insult(f"StressInsult {i}")

def run_one(total_requests):
    """
    Distribute `total_requests` evenly across NUM_PROCESSES processes,
    run them in parallel, and return the elapsed time.
    """
    per_proc = total_requests // NUM_PROCESSES
    tasks = [(PYRO_NAME, per_proc)] * NUM_PROCESSES

    start = time.time()
    with multiprocessing.Pool(NUM_PROCESSES) as pool:
        pool.map(send_requests, tasks)
    end = time.time()
    return end - start

def main():
    throughputs = []
    print("Pyro InsultService single-node throughput test")
    print(f"Concurrency (processes): {NUM_PROCESSES}")
    print("TotalReq | Time (s) | Throughput (req/s)")
    print("---------|----------|-------------------")

    for total in REQUEST_STEPS:
        t = run_one(total)
        tp = total / t
        throughputs.append(tp)
        print(f"{total:8d} | {t:8.3f} | {tp:15.1f}")

    # Plot
    plt.figure()
    plt.plot(REQUEST_STEPS, throughputs, marker='o', label="Pyro InsultService")
    plt.xscale('log')
    plt.xlabel('Total requests issued')
    plt.ylabel('Throughput (requests/sec)')
    plt.title('Single-node Pyro InsultService Throughput vs Load')
    plt.grid(True)
    plt.legend()
    plt.show()

if __name__ == "__main__":
    main()