#same stress test as stress_test_insult_service.py but for dynamic - sending a bigger number of requests to force the autoscaler to scale up

import xmlrpc.client
import multiprocessing
import time
import matplotlib.pyplot as plt

# ── Configuration ───────────────────────────────────────────────────────────────────
# XMLRPC server URL, port 9000 for InsultService
SERVER_URL = "http://localhost:9000"
# Fixed number of current processes
NUM_PROCESSES = 10
# Different total loads to test
REQUEST_STEPS = [700, 900, 1300, 1500, 1700]
# ─────────────────────────────────────────────────────────────────────────────────────


def send_requests(args):
    """
    Worker function: each process will send 'reqs' requests to the service.
    """
    url, reqs = args
    proxy = xmlrpc.client.ServerProxy(url, allow_none=True)
    for i in range(reqs):
        proxy.add_insult(f"Test Insult {i}")


def run(total_requests):
    """
    Distribute 'total_requests' evenly across NUM_PROCESSES processes,
    run them in parallel, and return the total elapsed time.
    """
    # Determine how many requests each process should send
    per_process = total_requests // NUM_PROCESSES
    # Build argument list for pool
    tasks = [(SERVER_URL, per_process)] * NUM_PROCESSES

    start = time.time()
    with multiprocessing.Pool(NUM_PROCESSES) as pool:
        pool.map(send_requests, tasks)
    end = time.time()
    return end - start

def main():
    throughputs = []
    times = []
    
    print("Single‑node throughput test (InsultService)")
    print(f"Concurrency (processes): {NUM_PROCESSES}")
    print("TotalReq | Time (s) | Throughput (req/s)")
    
    # Sweep over different total request loads
    for total in REQUEST_STEPS:
        t = run(total)
        tp = total / t
        times.append(t)
        throughputs.append(tp)
        print(f"{total:8d} | {t:8.3f} | {tp:8.1f}")
    
    # Plot throughput vs total requests
    plt.figure()
    plt.plot(REQUEST_STEPS, throughputs, marker='o')
    plt.xscale('log')
    plt.xlabel('Total requests issued')
    plt.ylabel('Throughput (requests/sec)')
    plt.title('Single‑node InsultService Throughput vs Load')
    plt.grid(True)
    plt.show()

if __name__ == "__main__":
    main()