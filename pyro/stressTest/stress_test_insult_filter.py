# stress_test_pyro_filter.py

import Pyro4
import multiprocessing
import time
import matplotlib.pyplot as plt

# ── Configuration ──────────────────────────────────────────────────────────────
PYRO_NAME      = "example.insultfilter"        # the Pyro name of the filter service
NUM_PROCESSES  = 10                            # fixed client‑side parallelism
REQUEST_STEPS  = [150000, 160000, 170000, 180000 ,190000, 200000]  # total texts to sweep
# ────────────────────────────────────────────────────────────────────────────────

def send_requests(per_proc: int) -> None:
    """
    Each worker process:
      1. connects to the filter service,
      2. submits `per_proc` texts,
      3. calls process_queue() once to flush the queue.
    """
    proxy = Pyro4.Proxy("PYRONAME:" + PYRO_NAME)
    # submit texts
    for i in range(per_proc):
        proxy.submit_text(f"This is a stupid mistake {i}")
    # flush queue
    proxy.process_queue()

def run_load(total_requests: int) -> float:
    """
    Distribute `total_requests` evenly across NUM_PROCESSES,
    run them in parallel, and return the elapsed wall‑clock time.
    """
    per_proc = total_requests // NUM_PROCESSES
    tasks = [per_proc] * NUM_PROCESSES
    t0 = time.time()
    with multiprocessing.Pool(NUM_PROCESSES) as pool:
        pool.map(send_requests, tasks)
    return time.time() - t0

def main():
    throughputs = []
    print("Single‑node Pyro InsultFilterService throughput test")
    print(f"Concurrency (processes): {NUM_PROCESSES}")
    print("TotalReq | Time (s) | Throughput (req/s)")
    print("---------|----------|---------------------")
    
    for total in REQUEST_STEPS:
        t = run_load(total)
        tp = total / t
        throughputs.append(tp)
        print(f"{total:8d} | {t:8.3f} | {tp:19.1f}")
    
    # Plot throughput vs load
    plt.plot(REQUEST_STEPS, throughputs, marker='s', label="Pyro FilterService")
    plt.xscale('log')
    plt.xlabel('Total requests issued')
    plt.ylabel('Throughput (texts processed/sec)')
    plt.title('Single‑node Pyro InsultFilterService Throughput vs Load')
    plt.grid(True)
    plt.legend()
    plt.show()

if __name__ == "__main__":
    main()
