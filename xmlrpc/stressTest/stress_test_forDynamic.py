import xmlrpc.client
import multiprocessing
import threading
import time
import matplotlib.pyplot as plt

SERVER_URL = "http://localhost:9000"
DURATION   = 30  # seconds to run the test
NUM_SENDERS = 20  # number of parallel sender processes

def sender(stop_event, counter):
    """Continuously call add_insult() until stop_event is set."""
    proxy = xmlrpc.client.ServerProxy(SERVER_URL, allow_none=True)
    while not stop_event.is_set():
        proxy.add_insult("stress-test")
        with counter.get_lock():
            counter.value += 1

def monitor(stop_event, times, workers, throughputs, counter):
    """
    Every second, record:
      - elapsed time since start
      - current worker count from server
      - # of requests sent in the last second (throughput)
    """
    proxy = xmlrpc.client.ServerProxy(SERVER_URL, allow_none=True)
    start = time.time()
    last_count = 0
    while not stop_event.is_set():
        time.sleep(1)
        now = time.time() - start
        times.append(now)
        # ask the server how many workers it has
        try:
            wc = proxy.get_worker_count()
        except Exception:
            wc = None
        workers.append(wc)
        # compute throughput in the last second
        with counter.get_lock():
            current = counter.value
        throughputs.append(current - last_count)
        last_count = current

def main():
    manager = multiprocessing.Manager()
    # shared counter of RPC calls sent
    counter = multiprocessing.Value('i', 0)

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
    mon_thread = threading.Thread(target=monitor,
                                  args=(stop_event, times, workers, throughputs, counter),
                                  daemon=True)
    mon_thread.start()

    print(f"Running stress test for {DURATION} seconds…")
    time.sleep(DURATION)
    stop_event.set()

    # wait a bit for clean shutdown
    mon_thread.join(2)
    for p in senders:
        p.join(1)

    # Plotting
    fig, ax1 = plt.subplots()
    ax2 = ax1.twinx()

    ax1.plot(times, workers, 'g-o', label='Worker count')
    ax2.plot(times, throughputs, 'b-s', label='Throughput (req/sec)')

    ax1.set_xlabel('Time (s)')
    ax1.set_ylabel('Workers', color='g')
    ax2.set_ylabel('Throughput (req/sec)', color='b')

    ax1.grid(True)
    plt.title('Dynamic‐Scaling InsultService: Workers & Throughput Over Time')

    # legends
    lines, labels = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines+lines2, labels+labels2, loc='upper left')

    plt.show()

if __name__ == "__main__":
    main()
