import xmlrpc.client
import multiprocessing
import time

# XMLRPC server URL, port 9000 for InsultService
SERVER_URL = "http://localhost:9000"

# Number of requests and concurrent processes
NUM_REQUESTS = 500
NUM_PROCESSES = 10

# Function to send requests
def send_requests(proc_id):
    insult_service = xmlrpc.client.ServerProxy(SERVER_URL, allow_none=True)
    start_time = time.time()
    
    for i in range(NUM_REQUESTS // NUM_PROCESSES):
        insult_service.add_insult(f"Test Insult {i}")

    end_time = time.time()
    return end_time - start_time  #Return time used (irrelevant, we only use the total time of all the processes)


def stress_test_insult_service():
    print(f"Starting stress test with {NUM_PROCESSES} processes and {NUM_REQUESTS} total requests...")

    start = time.time()

    #Run send_requests for NUM_PROCESSES concurrently
    with multiprocessing.Pool(NUM_PROCESSES) as pool:
        results = pool.map(send_requests, range(NUM_PROCESSES))

    end = time.time()

    #Metrics Calculation
    total_time = end - start
    rps = NUM_REQUESTS / total_time

    print(f"Total requests: {NUM_REQUESTS}")
    print(f"Total time: {total_time:.2f} seconds")
    print(f"Requests per second (RPS): {rps:.2f}")

if __name__ == "__main__":
    stress_test_insult_service()
