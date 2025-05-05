# stress_test_pyro_filter.py
import Pyro4
import multiprocessing
import time
import matplotlib.pyplot as plt

# service name in Pyro name server
PYRO_NAME      = "example.insultfilter"

# fixed client‐side concurrency
NUM_PROCESSES  = 10

# different total loads to test
REQUEST_STEPS  = [100, 500, 1000, 1500, 1600]

def send_requests(per_proc: int) -> float:
    """
    Each worker process will:
      1. connect to the filter service
      2. submit per_proc texts
      3. call process_queue() once
    Returns the elapsed time in seconds.
    """
    proxy = Pyro4.Proxy("PYRONAME:" + PYRO_NAME)
    start = time.time()
    for i in range(per_proc):
        proxy.submit_text(f"This is a stupid mistake {i}")
    proxy.process_queue()
    return time.time() - start

def run_load(total_requests: int) -> float:
    """
    Distribute total_requests evenly across NUM_PROCESSES,
    run them in parallel, and return the wall‑clock time.
    """
    per_proc = total_requests // NUM_PROCESSES
    # build list of “per_proc” repeated
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

    # plot
    plt.plot(REQUEST_STEPS, throughputs, marker='s', label="Pyro FilterService")
    plt.xscale('log')
    plt.xlabel('Total requests issued')
    plt.ylabel('Throughput (requests/sec)')
    plt.title('Single‑node Pyro InsultFilterService Throughput vs Load')
    plt.grid(True)
    plt.legend()
    plt.show()

if __name__ == "__main__":
    main()
