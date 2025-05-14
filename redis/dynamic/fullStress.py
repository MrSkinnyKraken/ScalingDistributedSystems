#fullStress.py
import random
import redis
import multiprocessing
import time

# ── Configuración ─────────────────────────────────────────────────────────
REDIS_HOST = 'localhost'
QUEUE_NAME = 'insult_raw'  
NUM_PROCESSES = 10
REQUEST_STEPS = [100,1000, 10000, 100000]  # Total de mensajes a enviar
# ──────────────────────────────────────────────────────────────────────────

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
    connection = redis.Redis(host=REDIS_HOST, decode_responses=True)
    connection.ltrim(QUEUE_NAME, 1, 0)  # deja la lista vacía sin eliminarla
    print("Single-node throughput test (InsultFilterService via RabbitMQ)")
    print(f"Concurrency (processes): {NUM_PROCESSES}")
    print("Press Cntrl+C or click the trash to kill the test.")
    print("TotalReq | Time (s) | Throughput (req/s)")
    print("---------|----------|--------------------")
    while True:
        # Check if the Redis queue is empty

        message_count = connection.llen(QUEUE_NAME)
        if message_count == 0:
            reqs = random.choice(REQUEST_STEPS)
            t = run(reqs)
            tp = reqs / t
            throughputs.append(tp)
            print(f"{reqs:8d} | {t:8.3f} | {tp:15.1f}")


if __name__ == "__main__":
    main()

