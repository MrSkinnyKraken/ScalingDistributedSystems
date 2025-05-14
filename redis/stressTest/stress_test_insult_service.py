import redis
import multiprocessing
import time
import matplotlib.pyplot as plt

# ── Configuración ─────────────────────────────────────────────────────────
REDIS_HOST = 'localhost'
CHANNEL_NAME = 'new_insults'
NUM_PROCESSES = 10
REQUEST_STEPS = [100, 1000, 10000, 100000, 1000000]
# ─────────────────────────────────────────────────────────────────────────

def send_requests(reqs):
    r = redis.Redis(host=REDIS_HOST, decode_responses=True)
    for i in range(reqs):
        msg = f"stress_insult_{i}"
        r.publish(CHANNEL_NAME, msg)


def run(total_requests):
    per_process = total_requests // NUM_PROCESSES
    tasks = [per_process] * NUM_PROCESSES
    start = time.time()
    with multiprocessing.Pool(NUM_PROCESSES) as pool:
        pool.map(send_requests, tasks)
    return time.time() - start

def main():
    throughputs = []

    print("Stress test: InsultService via Redis (new_insults queue)")
    for total in REQUEST_STEPS:
        t = run(total)
        tp = total / t
        throughputs.append(tp)
        print(f"{total:8d} | {t:8.3f} s | {tp:8.1f} req/s")

    plt.plot(REQUEST_STEPS, throughputs, marker='o')
    plt.xscale('log')
    plt.xlabel('Total insults submitted')
    plt.ylabel('Throughput (messages/sec)')
    plt.title('InsultService Throughput (Redis)')
    plt.grid(True)
    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    main()
