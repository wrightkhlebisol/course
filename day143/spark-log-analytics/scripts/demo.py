import requests
import time
import json

API_URL = "http://localhost:8000"

def wait_for_api():
    """Wait for API to be ready"""
    print("Waiting for API to be ready...")
    for i in range(30):
        try:
            response = requests.get(f"{API_URL}/health")
            if response.status_code == 200:
                print("✓ API is ready!")
                return True
        except:
            pass
        time.sleep(1)
    return False

def run_demo():
    """Run demonstration of Spark log analytics"""
    print("\n🎬 Spark Log Analytics Demonstration")
    print("=" * 50)
    
    if not wait_for_api():
        print("❌ API not available")
        return
    
    # Get cluster info
    print("\n1️⃣  Checking Spark cluster status...")
    response = requests.get(f"{API_URL}/cluster/info")
    cluster_info = response.json()
    print(f"   Status: {cluster_info['status']}")
    print(f"   App: {cluster_info.get('app_name', 'N/A')}")
    print(f"   Parallelism: {cluster_info.get('default_parallelism', 'N/A')}")
    
    # Run analysis
    print("\n2️⃣  Running log analysis...")
    response = requests.post(
        f"{API_URL}/analyze",
        json={"input_path": "data/input/*.json"}
    )
    
    if response.status_code == 200:
        result = response.json()
        summary = result['summary']
        
        print(f"   ✓ Analysis complete!")
        print(f"   Records processed: {summary['total_records_processed']:,}")
        print(f"   Duration: {summary['duration_seconds']}s")
        print(f"   Throughput: {summary['records_per_second']:,.0f} records/sec")
        print(f"   Anomalies detected: {summary['anomaly_count']}")
        
        if 'correlation' in summary:
            corr = summary['correlation']
            print(f"   Correlation: {corr['correlation_coefficient']} ({corr['interpretation']})")
    else:
        print(f"   ❌ Analysis failed: {response.text}")
    
    # Get job history
    print("\n3️⃣  Fetching job history...")
    response = requests.get(f"{API_URL}/jobs/history?limit=5")
    jobs = response.json()['jobs']
    
    for i, job in enumerate(jobs, 1):
        status_icon = "✓" if job['status'] == 'success' else "✗"
        print(f"   {status_icon} {job['job_name']}: {job['records_processed']:,} records")
    
    # Get results
    print("\n4️⃣  Fetching analysis results...")
    result_types = ['error_rates', 'performance_metrics', 'top_users']
    
    for result_type in result_types:
        response = requests.get(f"{API_URL}/results/{result_type}?limit=3")
        if response.status_code == 200:
            data = response.json()
            print(f"   {result_type}: {data['count']} records available")
    
    print("\n" + "=" * 50)
    print("✓ Demonstration complete!")
    print("\n📊 View dashboard: src/dashboard/index.html")
    print("🔍 Spark UI: http://localhost:4040")
    print("📡 API docs: http://localhost:8000/docs")

if __name__ == '__main__':
    run_demo()
