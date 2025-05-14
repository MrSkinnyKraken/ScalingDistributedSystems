#static_scaling_insult_filter.py
import redis
import subprocess
import time
import multiprocessing
import matplotlib.pyplot as plt

# ── Configuración ─────────────────────────────────────────────────────────
REDIS_HOST = 'localhost'
CHANNEL_NAME = 'insult_raw'
NUM_PROCESSES = 10
TOTAL_MESSAGES = 10000
WORKER_COUNTS = [1, 2, 3]
# ─────────────────────────────────────────────────────────────────────────

def send_requests(reqs):
    r = redis.Redis(host=REDIS_HOST, decode_responses=True)
    for i in range(reqs):
        msg = f"This is a stupid mistake {i}"
        r.lpush(CHANNEL_NAME, msg)


def run_sender(total_requests):
    """Distribuye las peticiones entre procesos y mide el tiempo total."""
    per_process = total_requests // NUM_PROCESSES
    tasks = [per_process] * NUM_PROCESSES

    start = time.time()
    with multiprocessing.Pool(NUM_PROCESSES) as pool:
        pool.map(send_requests, tasks)
    end = time.time()
    return end - start

def launch_insult_service_instances(n):
    procs = []
    for _ in range(n):
        p = subprocess.Popen(['python3', 'redis/InsultFilterService.py'])
        procs.append(p)
    return procs

def terminate_instances(procs):
    for p in procs:
        p.terminate()
        p.wait()

def wait_until_queue_empty(queue_name):
    r = redis.Redis(host=REDIS_HOST, decode_responses=True)
    while r.llen(queue_name) > 0:
        time.sleep(0.05)


def main():
    print("Static scaling test (InsultFilterService via redis)")
    print(f"Total messages: {TOTAL_MESSAGES} | Sender processes: {NUM_PROCESSES}")
    print("Workers | Time (s) | Speedup")

    base_time = None
    times = []
    speedups = []

    for n_workers in WORKER_COUNTS:
        services = launch_insult_service_instances(n_workers)
        time.sleep(2)  # esperar a que los workers se conecten

        start = time.time()
        run_sender(TOTAL_MESSAGES)
        wait_until_queue_empty(CHANNEL_NAME)
        t = time.time() - start

        if base_time is None:
            base_time = t

        sp = base_time / t
        times.append(t)
        speedups.append(sp)

        print(f"{n_workers:^7} | {t:8.3f} | {sp:7.2f}")
        terminate_instances(services)
        time.sleep(1)


    # Gráfico de speedup
    plt.figure()
    plt.plot(WORKER_COUNTS, speedups, marker='o', linestyle='-')
    plt.xlabel('Number of InsultService nodes')
    plt.ylabel('Speedup (T1 / TN)')
    plt.title('Static Scaling: Speedup of InsultServiceFilter (redis)')
    plt.grid(True)
    plt.xticks(WORKER_COUNTS)
    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    main()
