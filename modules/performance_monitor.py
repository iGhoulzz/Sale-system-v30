"""
Performance monitoring module for the sales system.
This module provides tools to monitor and report on performance metrics.
"""

import time
import threading
import logging
import queue
import os
from datetime import datetime

# Configure logger
logger = logging.getLogger(__name__)

class PerformanceMonitor:
    """
    Performance monitoring class to track UI responsiveness and database operations.
    """
    
    def __init__(self, freeze_threshold_ms=500):
        """Initialize the performance monitor"""
        self.freeze_threshold = freeze_threshold_ms / 1000.0  # Convert to seconds
        self.active = True
        self.metrics_queue = queue.Queue()
        self.metrics = {
            'ui_freezes': 0,
            'longest_freeze_ms': 0,
            'db_operations': 0,
            'total_db_time_ms': 0,
            'longest_db_ms': 0,
            'background_tasks': 0,
            'total_bg_time_ms': 0
        }
        
        # Start monitor thread
        self.monitor_thread = threading.Thread(
            target=self._monitor_ui_thread,
            daemon=True
        )
        self.monitor_thread.start()
        
        # Start metrics processing thread
        self.processing_thread = threading.Thread(
            target=self._process_metrics,
            daemon=True
        )
        self.processing_thread.start()
        
        logger.info("Performance monitoring initialized")
    
    def _monitor_ui_thread(self):
        """Monitor thread to detect UI freezes"""
        last_heartbeat = time.time()
        last_report = time.time()
        
        while self.active:
            # Sleep briefly
            time.sleep(0.1)
            
            # Check if UI thread is responding
            current_time = time.time()
            
            # Report metrics periodically
            if current_time - last_report > 300:  # Report every 5 minutes
                self._report_metrics()
                last_report = current_time
    
    def _process_metrics(self):
        """Process collected metrics"""
        while self.active:
            try:
                # Get metric from queue with timeout
                metric = self.metrics_queue.get(timeout=1.0)
                
                # Process the metric
                metric_type = metric.get('type')
                if metric_type == 'ui_freeze':
                    self.metrics['ui_freezes'] += 1
                    duration_ms = metric.get('duration_ms', 0)
                    if duration_ms > self.metrics['longest_freeze_ms']:
                        self.metrics['longest_freeze_ms'] = duration_ms
                
                elif metric_type == 'db_operation':
                    self.metrics['db_operations'] += 1
                    duration_ms = metric.get('duration_ms', 0)
                    self.metrics['total_db_time_ms'] += duration_ms
                    if duration_ms > self.metrics['longest_db_ms']:
                        self.metrics['longest_db_ms'] = duration_ms
                
                elif metric_type == 'background_task':
                    self.metrics['background_tasks'] += 1
                    duration_ms = metric.get('duration_ms', 0)
                    self.metrics['total_bg_time_ms'] += duration_ms
                
                # Mark as done
                self.metrics_queue.task_done()
                
            except queue.Empty:
                # No metrics to process
                pass
            except Exception as e:
                logger.error(f"Error processing metrics: {e}")
    
    def _report_metrics(self):
        """Report current metrics to log"""
        try:
            # Calculate averages
            avg_db_ms = 0
            if self.metrics['db_operations'] > 0:
                avg_db_ms = self.metrics['total_db_time_ms'] / self.metrics['db_operations']
            
            avg_bg_ms = 0
            if self.metrics['background_tasks'] > 0:
                avg_bg_ms = self.metrics['total_bg_time_ms'] / self.metrics['background_tasks']
            
            # Log the metrics
            logger.info(
                f"Performance metrics: "
                f"UI freezes: {self.metrics['ui_freezes']}, "
                f"longest freeze: {self.metrics['longest_freeze_ms']:.2f}ms, "
                f"DB ops: {self.metrics['db_operations']}, "
                f"avg DB time: {avg_db_ms:.2f}ms, "
                f"longest DB: {self.metrics['longest_db_ms']:.2f}ms, "
                f"BG tasks: {self.metrics['background_tasks']}, "
                f"avg BG time: {avg_bg_ms:.2f}ms"
            )
            
            # Write detailed metrics to file
            self._write_metrics_to_file()
            
        except Exception as e:
            logger.error(f"Error reporting metrics: {e}")
    
    def _write_metrics_to_file(self):
        """Write detailed metrics to a file"""
        try:
            # Ensure logs directory exists
            os.makedirs('logs', exist_ok=True)
            
            # Create filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d")
            filename = f"logs/performance_{timestamp}.log"
            
            # Write metrics to file
            with open(filename, 'a') as f:
                f.write(f"=== Performance Report: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ===\n")
                f.write(f"UI freezes: {self.metrics['ui_freezes']}\n")
                f.write(f"Longest UI freeze: {self.metrics['longest_freeze_ms']:.2f}ms\n")
                f.write(f"Database operations: {self.metrics['db_operations']}\n")
                
                avg_db_ms = 0
                if self.metrics['db_operations'] > 0:
                    avg_db_ms = self.metrics['total_db_time_ms'] / self.metrics['db_operations']
                f.write(f"Average DB operation time: {avg_db_ms:.2f}ms\n")
                f.write(f"Longest DB operation: {self.metrics['longest_db_ms']:.2f}ms\n")
                
                f.write(f"Background tasks: {self.metrics['background_tasks']}\n")
                
                avg_bg_ms = 0
                if self.metrics['background_tasks'] > 0:
                    avg_bg_ms = self.metrics['total_bg_time_ms'] / self.metrics['background_tasks']
                f.write(f"Average background task time: {avg_bg_ms:.2f}ms\n\n")
        
        except Exception as e:
            logger.error(f"Error writing metrics to file: {e}")
    
    def record_ui_freeze(self, duration_ms):
        """Record a UI freeze event"""
        if duration_ms >= self.freeze_threshold * 1000:
            self.metrics_queue.put({
                'type': 'ui_freeze',
                'duration_ms': duration_ms,
                'timestamp': time.time()
            })
    
    def record_db_operation(self, operation_name, duration_ms):
        """Record a database operation"""
        self.metrics_queue.put({
            'type': 'db_operation',
            'name': operation_name,
            'duration_ms': duration_ms,
            'timestamp': time.time()
        })
    
    def record_background_task(self, task_name, duration_ms):
        """Record a background task execution"""
        self.metrics_queue.put({
            'type': 'background_task',
            'name': task_name,
            'duration_ms': duration_ms,
            'timestamp': time.time()
        })
    
    def shutdown(self):
        """Shutdown the monitor"""
        self.active = False
        self._report_metrics()  # Final report
        logger.info("Performance monitoring shut down")


# Create a global instance
performance_monitor = PerformanceMonitor()

def db_operation_timer(func):
    """
    Decorator to time database operations and record metrics
    """
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        duration_ms = (time.time() - start_time) * 1000
        performance_monitor.record_db_operation(func.__name__, duration_ms)
        return result
    return wrapper

def background_task_timer(func):
    """
    Decorator to time background tasks and record metrics
    """
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        duration_ms = (time.time() - start_time) * 1000
        performance_monitor.record_background_task(func.__name__, duration_ms)
        return result
    return wrapper

def shutdown_performance_monitoring():
    """Shutdown performance monitoring"""
    performance_monitor.shutdown()
