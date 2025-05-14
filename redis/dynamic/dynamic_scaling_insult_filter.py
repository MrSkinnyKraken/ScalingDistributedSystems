# dynamic_scaling_redis.py
import redis
import subprocess
import time
import math

# ── Configuración ─────────────────────────────────────────────────────────
REDIS_HOST = 'localhost'
QUEUE_NAME = 'insult_raw'      # cola de trabajo
T_PROCESS = 0.005              # tiempo medio de procesar un mensaje (s/msg)
C_WORKER = 1 / T_PROCESS       # capacidad: mensajes/s que un worker puede procesar
T_RESPONSE = 1.0               # objetivo de tiempo de respuesta (s)
MAX_WORKERS = 100
MIN_WORKERS = 1
SCALE_INTERVAL = 2             # cada cuántos segundos re-evaluar
# ─────────────────────────────────────────────────────────────────────────

def start_filter():
    return subprocess.Popen(
        ['python3', 'redis/InsultFilterService.py'],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )

def terminate(p):
    p.terminate()
    p.wait()

def get_backlog(r):
    """Lee longitud de la cola de trabajo"""
    return r.llen(QUEUE_NAME)

def dynamic_scale():
    r = redis.Redis(host=REDIS_HOST, decode_responses=True)
    workers = []

    try:
        while True:
            B = get_backlog(r)
            # Arrival rate = (cantidad nueva en intervalo) / intervalo
            # Aquí aproximamos ArrivalRate ≈ B / SCALE_INTERVAL
            ArrivalRate = B / SCALE_INTERVAL

            # Número requerido con backlog+respuesta objetivo:
            N_req = math.ceil((B + ArrivalRate * T_RESPONSE) / C_WORKER)
            N_req = min(max(N_req, MIN_WORKERS), MAX_WORKERS)

            delta = N_req - len(workers)
            if delta > 0:
                for _ in range(delta):
                    workers.append(start_filter())
                print(f"[Scale-Up] Launched {delta} workers (total {len(workers)})")
            elif delta < 0:
                for _ in range(-delta):
                    terminate(workers.pop())
                print(f"[Scale-Down] Terminated {-delta} workers (total {len(workers)})")

            print(f"[Monitor] Backlog={B}, ArrivalRate≈{ArrivalRate:.1f}/s, Workers={len(workers)}")
            time.sleep(SCALE_INTERVAL)

    finally:
        # Shutdown all
        for p in workers:
            terminate(p)

if __name__ == "__main__":
    dynamic_scale()
