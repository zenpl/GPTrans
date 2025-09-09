#!/usr/bin/env python3
"""
GPTrans Workers
"""
import sys
from pathlib import Path

# Add parent directory to Python path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

if __name__ == "__main__":
    from app.workers.main import *
    
    logger.info("Starting GPTrans workers...")
    
    # Listen to queues
    from redis import Redis
    from rq import Worker, Connection
    import os
    
    redis_conn = Redis(
        host=os.getenv('REDIS_HOST', 'localhost'),
        port=int(os.getenv('REDIS_PORT', '6379')),
        db=int(os.getenv('REDIS_DB', '0'))
    )
    
    # Import queues from main
    from rq import Queue
    
    ocr_queue = Queue('ocr', connection=redis_conn)
    translation_queue = Queue('translation', connection=redis_conn)
    typeset_queue = Queue('typeset', connection=redis_conn)
    export_queue = Queue('export', connection=redis_conn)
    
    with Connection(redis_conn):
        worker = Worker([ocr_queue, translation_queue, typeset_queue, export_queue])
        worker.work()