import redis
import subprocess
import time
import multiprocessing
import matplotlib.pyplot as plt

# ── Configuración ─────────────────────────────────────────────────────────
REDIS_HOST = 'localhost'
CHANNEL_NAME = 'new_insults'
NUM_PROCESSES = 10
TOTAL_MESSAGES = 10000
WORKER_COUNTS = [1, 2, 3]
# ─────────────────────────────────────────────────────────────────────────

def send_requests(reqs):
    r = redis.Redis(host=REDIS_HOST, decode_responses=True)
    for i in range(reqs):
        msg = f"test_insult_{i}"
        r.publish(CHANNEL_NAME, msg)


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
        p = subprocess.Popen(['python3', 'redis/InsultService.py'])
        procs.append(p)
    return procs

def terminate_instances(procs):
    for p in procs:
        p.terminate()
        p.wait()

def main():
    print("Static scaling test (InsultService via redis)")
    print(f"Total messages: {TOTAL_MESSAGES} | Sender processes: {NUM_PROCESSES}")
    print("Workers | Time (s) | Speedup")

    base_time = None
    times = []
    speedups = []

    for n_workers in WORKER_COUNTS:
        services = launch_insult_service_instances(n_workers)
        time.sleep(5)  # Esperar a que se conecten

        t = run_sender(TOTAL_MESSAGES)

        if base_time is None:
            base_time = t

        sp = base_time / t
        times.append(t)
        speedups.append(sp)

        print(f"{n_workers:^7} | {t:8.3f} | {sp:7.2f}")

        terminate_instances(services)
        time.sleep(2)

    # Gráfico de speedup
    plt.figure()
    plt.plot(WORKER_COUNTS, speedups, marker='o', linestyle='-')
    plt.xlabel('Number of InsultService nodes')
    plt.ylabel('Speedup (T1 / TN)')
    plt.title('Static Scaling: Speedup of InsultService (redis)')
    plt.grid(True)
    plt.xticks(WORKER_COUNTS)
    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    main()
