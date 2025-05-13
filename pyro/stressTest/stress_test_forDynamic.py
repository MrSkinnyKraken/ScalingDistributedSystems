import Pyro4
import multiprocessing
import threading
import time
import matplotlib.pyplot as plt

# ── Configuration ─────────────────────────────────────────────────────────────
PYRO_URI    = "PYRONAME:example.dynamic.insultservice"
DURATION    = 30     # total seconds to run test
NUM_SENDERS = 25     # number of parallel sender processes
MIN_WORKERS = 1      # minimum workers
# ────────────────────────────────────────────────────────────────────────────────

def sender(stop_event, counter):
    """Continuously call add_insult() until stop_event is set."""
    proxy = Pyro4.Proxy(PYRO_URI)
    while not stop_event.is_set():
        try:
            proxy.add_insult("stress-test")
        except Exception:
            pass
        with counter.get_lock():
            counter.value += 1

def monitor(stop_event, times, workers, throughputs, counter):
    """
    Every second, record:
      - elapsed time
      - current worker count
      - requests sent in the last second (throughput)
    """
    proxy = Pyro4.Proxy(PYRO_URI)
    start = time.time()
    last_count = 0
    while not stop_event.is_set():
        time.sleep(1)
        now = time.time() - start
        times.append(now)
        # get current worker count
        try:
            wc = proxy.get_worker_count()
        except Exception:
            wc = None
        workers.append(wc)
        # compute throughput
        with counter.get_lock():
            current = counter.value
        throughputs.append(current - last_count)
        last_count = current

def main():
    manager = multiprocessing.Manager()
    counter = multiprocessing.Value('i', 0)   # shared RPC counter
    stop_event = multiprocessing.Event()

    times = []
    workers = []
    throughputs = []

    # start sender processes
    senders = []
    for _ in range(NUM_SENDERS):
        p = multiprocessing.Process(target=sender, args=(stop_event, counter), daemon=True)
        p.start()
        senders.append(p)

    # start monitoring thread
    mon = threading.Thread(target=monitor,
                           args=(stop_event, times, workers, throughputs, counter),
                           daemon=True)
    mon.start()

    print(f"Running dynamic‐scaling Pyro stress test for {DURATION} seconds…")
    time.sleep(DURATION)
    stop_event.set()

    # allow clean shutdown
    mon.join(2)
    for p in senders:
        p.join(1)

    # Plot results
    fig, ax1 = plt.subplots()
    ax2 = ax1.twinx()

    # make sure times, workers, throughputs are the same length
    n = min(len(times), len(workers), len(throughputs))
    times = times[:n]
    workers = workers[:n]
    throughputs = throughputs[:n]
    # Replace any None in workers with previous or MIN_WORKERS
    #cleaned = []
    #prev = MIN_WORKERS
    #for w in workers:
    #    if w is None:
    #        cleaned.append(prev)
    #    else:
    #        cleaned.append(w)
    #        prev = w
    #workers = cleaned

    ax1.plot(times, workers, 'g-o', label='Worker count')
    ax2.plot(times, throughputs, 'b-s', label='Throughput (req/sec)')

    ax1.set_xlabel('Time (s)')
    ax1.set_ylabel('Workers', color='g')
    # zoom the y-axis so the workers line is visible
    #ax1.set_ylim(0, max(workers) + 1)

    ax2.set_ylabel('Throughput (req/sec)', color='b')
    ax1.grid(True)
    plt.title('Dynamic‐Scaling Pyro InsultService: Workers & Throughput Over Time')

    # combine legends
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper left')

    plt.show()

if __name__ == "__main__":
    main()