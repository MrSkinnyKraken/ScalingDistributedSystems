import xmlrpc.client
import multiprocessing
import time
import matplotlib.pyplot as plt

# ── Configuration ───────────────────────────────────────────────────────────────────
# XMLRPC server URL, port 9001 for InsultFilterService
SERVER_URL = "http://localhost:9001"

# Fixed number of current processes
NUM_PROCESSES = 10
# Different total loads to test
REQUEST_STEPS = [100, 500, 700, 900]
# ─────────────────────────────────────────────────────────────────────────────────────

def send_requests(args):
    """
    Worker function: each process will submit 'reqs' texts and then call process_queue().
    """
    url, reqs = args
    proxy = xmlrpc.client.ServerProxy(url, allow_none=True)
    # submit reqs texts
    for i in range(reqs):
        proxy.submit_text(f"This is a stupid mistake {i}")
    # once done, flush the queue
    proxy.process_queue()

def run_one(total_requests):
    """
    Distribute 'total_requests' evenly across NUM_PROCESSES processes,
    run them in parallel, and return the elapsed time.
    """
    per_process = total_requests // NUM_PROCESSES
    tasks = [(SERVER_URL, per_process)] * NUM_PROCESSES

    start = time.time()
    with multiprocessing.Pool(NUM_PROCESSES) as pool:
        pool.map(send_requests, tasks)
    end = time.time()
    return end - start

def main():
    throughputs = []
    print("Single-node throughput test (InsultFilterService)")
    print(f"Concurrency (processes): {NUM_PROCESSES}")
    print("TotalReq | Time (s) | Throughput (req/s)")
    print("---------|----------|-------------------")

    # Sweep total load
    for total in REQUEST_STEPS:
        t = run_one(total)
        tp = total / t
        throughputs.append(tp)
        print(f"{total:8d} | {t:8.3f} | {tp:15.1f}")

    # Plot
    plt.figure()
    plt.plot(REQUEST_STEPS, throughputs, marker='s', label="FilterService")
    plt.xscale('log')
    plt.xlabel('Total texts submitted')
    plt.ylabel('Throughput (texts processed/sec)')
    plt.title('Single-node InsultFilterService Throughput vs Load')
    plt.grid(True)
    plt.show()

if __name__ == "__main__":
    main()
