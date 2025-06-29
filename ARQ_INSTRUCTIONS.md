# ARQ-Based LinkedIn Profile Sourcing

## 🚀 **New Architecture: Scalable & Async**

Your LinkedIn profile sourcing system has been upgraded to use **ARQ (Async Redis Queue)** for true scalability and async processing.

## **Key Benefits:**
- ✅ **True Async**: Non-blocking job processing
- ✅ **Scalable**: Process up to 10 jobs concurrently
- ✅ **Distributed**: Can run workers on multiple servers
- ✅ **Reliable**: Built-in retries and error handling
- ✅ **Fast**: Concurrent profile extraction and outreach generation

## **How to Run:**

### 1. Start Redis (if not running)
```bash
redis-server
```

### 2. Start the ARQ Worker
```bash
python arq_worker.py
```

### 3. Start the FastAPI Server
```bash
python main.py
```

## **API Usage (Same as Before):**

### Submit a Job:
```bash
curl -X POST "http://localhost:8000/api/jobs" \
  -H "Content-Type: application/json" \
  -d '{
    "job_description": "Senior Python Developer with FastAPI experience",
    "search_method": "rapid_api",
    "limit": 5
  }'
```

### Check Job Status:
```bash
curl "http://localhost:8000/api/jobs/{job_id}/status"
```

### Get Results:
```bash
curl "http://localhost:8000/api/jobs/{job_id}/results"
```

## **What Changed:**

### **Before (TaskQueue):**
- Thread-based workers (0-7)
- Blocking job processing
- Limited to single server

### **After (ARQ):**
- Async Redis Queue
- Non-blocking concurrent processing  
- Horizontally scalable

## **Architecture:**

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   FastAPI API   │───▶│   Redis Queue   │───▶│   ARQ Worker    │
│  (Job Submission)│    │  (Job Storage)  │    │ (Job Processing)│
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                                       │
                                                       ▼
                                          ┌─────────────────┐
                                          │  Single Worker  │
                                          │ Handles Complete│
                                          │    Pipeline     │
                                          └─────────────────┘
                                                       │
                                                       ▼
                                     Search → Extract → Score → Outreach
                                     (All async & concurrent)
```

## **Scaling:**

To scale horizontally, simply run more workers on different servers:

```bash
# Server 1
python arq_worker.py

# Server 2 
python arq_worker.py

# Server 3
python arq_worker.py
```

All workers will automatically pull jobs from the same Redis queue! 