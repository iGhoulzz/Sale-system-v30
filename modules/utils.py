"""
Utility functions for the application, including thread management 
and UI performance optimization.
"""
import threading
import queue
import time
from typing import Callable, Any, Dict, Optional, Tuple

class BackgroundTask:
    """
    A class to run tasks in the background without freezing the UI.
    
    This class handles running operations in a separate thread and then
    calling callbacks on the main thread using Tkinter's after() method.
    """
    
    def __init__(self):
        """Initialize with task and result queues and callback storage."""
        self.task_queue = queue.Queue()
        self.result_queue = queue.Queue()
        self.running = False
        self.worker_thread = None
        self._callbacks = {}  # Store callbacks by task_id
        
    def start(self):
        """Start the background worker thread."""
        if not self.running:
            self.running = True
            self.worker_thread = threading.Thread(target=self._worker, daemon=True)
            self.worker_thread.start()
            
    def stop(self):
        """Stop the background worker thread."""
        self.running = False
        if self.worker_thread and self.worker_thread.is_alive():
            self.worker_thread.join(timeout=1.0)
            
    def _worker(self):
        """Worker thread function to process tasks."""
        while self.running:
            try:
                # Get task with a timeout to allow thread to check if it should stop
                task, args, kwargs, task_id = self.task_queue.get(timeout=0.5)
                
                try:
                    # Execute the task
                    result = task(*args, **kwargs)
                    # Put result in result queue
                    self.result_queue.put((task_id, result, None))
                except Exception as e:
                    # Put error in result queue
                    self.result_queue.put((task_id, None, e))
                finally:
                    # Mark task as done
                    self.task_queue.task_done()
            except queue.Empty:
                # No tasks in queue, just continue
                continue
    
    def add_task(self, task: Callable, *args, on_complete: Optional[Callable] = None, 
                on_error: Optional[Callable] = None, **kwargs) -> str:
        """
        Add a task to be executed in the background.
        
        Args:
            task: The function to execute
            *args: Arguments to pass to the task
            on_complete: Callback when task completes successfully
            on_error: Callback when task fails
            **kwargs: Keyword arguments to pass to the task
            
        Returns:
            Task ID for tracking
        """
        # Generate a unique task ID
        task_id = str(time.time()) + str(id(task))
        
        # Store callbacks
        if on_complete or on_error:
            # Store callback info with task_id
            self._callbacks[task_id] = (on_complete, on_error)
            
        # Add task to queue
        self.task_queue.put((task, args, kwargs, task_id))
        
        return task_id
    
    def process_results(self, widget):
        """
        Process completed tasks and call their callbacks.
        Should be called periodically from the main thread.
        
        Args:
            widget: A Tkinter widget to use for after() calls
            
        Returns:
            bool: True if any results were processed, False otherwise
        """
        processed_any = False
        
        try:
            while True:
                # Get result without blocking
                task_id, result, error = self.result_queue.get_nowait()
                processed_any = True
                
                # Get callbacks
                on_complete, on_error = self._callbacks.get(task_id, (None, None))
                
                # Call appropriate callback
                if error and on_error:
                    # Schedule error callback on main thread
                    widget.after_idle(lambda e=error, cb=on_error: cb(e))
                elif not error and on_complete:
                    # Schedule completion callback on main thread
                    widget.after_idle(lambda r=result, cb=on_complete: cb(r))
                    
                # Mark result as processed
                self.result_queue.task_done()
                
                # Remove callbacks
                if task_id in self._callbacks:
                    del self._callbacks[task_id]
                    
        except queue.Empty:
            # No more results to process
            pass
            
        return processed_any


# Create a global background task manager
background_task_manager = BackgroundTask()

def init_background_tasks():
    """Initialize the background task system."""
    background_task_manager.start()

def shutdown_background_tasks():
    """Shutdown the background task system."""
    background_task_manager.stop()

def run_in_background(task: Callable, *args, on_complete: Optional[Callable] = None, 
                     on_error: Optional[Callable] = None, **kwargs) -> str:
    """
    Run a task in the background and call a callback when it's done.
    
    Args:
        task: The function to execute
        *args: Arguments to pass to the task
        on_complete: Callback when task completes successfully
        on_error: Callback when task fails
        **kwargs: Keyword arguments to pass to the task
        
    Returns:
        Task ID for tracking
    """
    return background_task_manager.add_task(task, *args, 
                                          on_complete=on_complete, 
                                          on_error=on_error, 
                                          **kwargs)

def chunk_process(widget, items, process_func, chunk_size=25, 
                 on_progress=None, on_complete=None):
    """
    Process a large number of items in chunks to keep the UI responsive.
    
    Args:
        widget: A Tkinter widget to use for after() calls
        items: The items to process
        process_func: Function to process a chunk of items
        chunk_size: Number of items to process in each chunk (default: 25)
        on_progress: Callback for progress updates
        on_complete: Callback when all processing is complete
    """
    # Store the after IDs so they can be cancelled if needed
    job_ids = []
    
    def process_chunk(start_idx):
        # Check if widget still exists
        if not widget.winfo_exists():
            return
            
        # Get the current chunk
        end_idx = min(start_idx + chunk_size, len(items))
        chunk = items[start_idx:end_idx]
        
        # Process this chunk
        process_func(chunk)
        
        # Report progress if needed
        if on_progress:
            progress = end_idx / len(items)
            on_progress(progress, end_idx, len(items))
        
        # If there are more items, schedule the next chunk
        if end_idx < len(items):
            after_id = widget.after(1, lambda: process_chunk(end_idx))
            job_ids.append(after_id)
        elif on_complete:
            # All done, call the completion callback
            on_complete()
    
    # Start processing with the first chunk
    process_chunk(0) 