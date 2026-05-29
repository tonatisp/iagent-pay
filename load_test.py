import requests
import concurrent.futures
import time

URL = "https://iagent-pay.com/api/transactions"
TOTAL_REQUESTS = 1000
CONCURRENT_THREADS = 100

def fetch_url(url):
    try:
        start_time = time.time()
        response = requests.get(url, timeout=5)
        end_time = time.time()
        return response.status_code, end_time - start_time
    except Exception as e:
        return str(e), 0

def run_stress_test():
    print(f"Starting load test on {URL}")
    print(f"Total Requests: {TOTAL_REQUESTS} with {CONCURRENT_THREADS} concurrent threads")
    
    start_total = time.time()
    
    success_count = 0
    failure_count = 0
    latencies = []
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=CONCURRENT_THREADS) as executor:
        futures = [executor.submit(fetch_url, URL) for _ in range(TOTAL_REQUESTS)]
        
        for future in concurrent.futures.as_completed(futures):
            status, latency = future.result()
            if status == 200:
                success_count += 1
                latencies.append(latency)
            else:
                failure_count += 1

    end_total = time.time()
    
    if latencies:
        avg_latency = sum(latencies) / len(latencies)
        max_latency = max(latencies)
    else:
        avg_latency = 0
        max_latency = 0
        
    print("\n--- RESULTS ---")
    print(f"Total Time Taken: {end_total - start_total:.2f} seconds")
    print(f"Successful Requests: {success_count}")
    print(f"Failed Requests (or rate limited): {failure_count}")
    print(f"Average Latency: {avg_latency*1000:.2f} ms")
    print(f"Max Latency: {max_latency*1000:.2f} ms")
    print(f"Requests per second (RPS): {TOTAL_REQUESTS / (end_total - start_total):.2f}")

if __name__ == "__main__":
    run_stress_test()
