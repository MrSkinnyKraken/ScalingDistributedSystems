import redis
import multiprocessing
import time
import matplotlib.pyplot as plt

# ── Configuración ─────────────────────────────────────────────────────────
REDIS_HOST = 'localhost'
QUEUE_NAME = 'insult_raw'
NUM_PROCESSES = 10
REQUEST_STEPS = [100, 1000, 10000, 100000, 1000000, 10000000]
# ─────────────────────────────────────────────────────────────────────────

def send_requests(reqs):
    r = redis.Redis(host=REDIS_HOST, decode_responses=True)
    pipe = r.pipeline()
    for i in range(reqs):
        text = f"This is a stupid mistake {i}"
        pipe.lpush(QUEUE_NAME, text)
        if i % 1000 == 0:
            pipe.execute()
    pipe.execute()

def run(total_requests):
    per_process = total_requests // NUM_PROCESSES
    tasks = [per_process] * NUM_PROCESSES
    start = time.time()
    with multiprocessing.Pool(NUM_PROCESSES) as pool:
        pool.map(send_requests, tasks)
    return time.time() - start

def main():
    throughputs = []

    print("Stress test: InsultFilterService via Redis (insult_raw queue)")
    for total in REQUEST_STEPS:
        t = run(total)
        tp = total / t
        throughputs.append(tp)
        print(f"{total:8d} | {t:8.3f} s | {tp:8.1f} req/s")

    plt.plot(REQUEST_STEPS, throughputs, marker='s')
    plt.xscale('log')
    plt.xlabel('Total texts submitted')
    plt.ylabel('Throughput (texts/sec)')
    plt.title('InsultFilterService Throughput (Redis)')
    plt.grid(True)
    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    main()
