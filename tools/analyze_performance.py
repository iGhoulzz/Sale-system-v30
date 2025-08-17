"""
Performance Log Analyzer

This script analyzes performance logs to provide insights and trends about
application performance.
"""

import os
import re
import sys
import datetime
import matplotlib.pyplot as plt
from collections import defaultdict

def find_log_files(directory='logs'):
    """Find all performance log files"""
    pattern = re.compile(r'performance_\d{8}\.log')
    log_files = []
    
    for file in os.listdir(directory):
        if pattern.match(file):
            log_files.append(os.path.join(directory, file))
    
    return sorted(log_files)

def parse_log_file(filename):
    """Parse a performance log file and extract metrics"""
    if not os.path.exists(filename):
        print(f"File not found: {filename}")
        return []
        
    reports = []
    current_report = None
    
    with open(filename, 'r') as f:
        lines = f.readlines()
    
    for line in lines:
        line = line.strip()
        
        # Start of a new report
        if line.startswith("=== Performance Report:"):
            if current_report:
                reports.append(current_report)
            
            # Extract timestamp
            match = re.search(r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})', line)
            timestamp = match.group(1) if match else "Unknown"
            
            current_report = {
                'timestamp': timestamp,
                'ui_freezes': 0,
                'longest_ui_freeze_ms': 0,
                'db_operations': 0,
                'avg_db_time_ms': 0,
                'longest_db_ms': 0,
                'background_tasks': 0,
                'avg_bg_time_ms': 0
            }
        
        # Extract metrics
        elif current_report:
            if line.startswith("UI freezes:"):
                current_report['ui_freezes'] = int(line.split(":")[1].strip())
            
            elif line.startswith("Longest UI freeze:"):
                match = re.search(r'([\d.]+)ms', line)
                if match:
                    current_report['longest_ui_freeze_ms'] = float(match.group(1))
            
            elif line.startswith("Database operations:"):
                current_report['db_operations'] = int(line.split(":")[1].strip())
            
            elif line.startswith("Average DB operation time:"):
                match = re.search(r'([\d.]+)ms', line)
                if match:
                    current_report['avg_db_time_ms'] = float(match.group(1))
            
            elif line.startswith("Longest DB operation:"):
                match = re.search(r'([\d.]+)ms', line)
                if match:
                    current_report['longest_db_ms'] = float(match.group(1))
            
            elif line.startswith("Background tasks:"):
                current_report['background_tasks'] = int(line.split(":")[1].strip())
            
            elif line.startswith("Average background task time:"):
                match = re.search(r'([\d.]+)ms', line)
                if match:
                    current_report['avg_bg_time_ms'] = float(match.group(1))
    
    # Add the last report
    if current_report:
        reports.append(current_report)
    
    return reports

def analyze_reports(reports):
    """Analyze performance reports and generate statistics"""
    if not reports:
        return {
            'total_reports': 0,
            'avg_ui_freezes': 0,
            'max_ui_freeze_ms': 0,
            'avg_db_time_ms': 0,
            'max_db_time_ms': 0,
            'avg_bg_time_ms': 0
        }
    
    stats = {
        'total_reports': len(reports),
        'total_ui_freezes': sum(r['ui_freezes'] for r in reports),
        'max_ui_freeze_ms': max(r['longest_ui_freeze_ms'] for r in reports),
        'total_db_operations': sum(r['db_operations'] for r in reports),
        'max_db_time_ms': max(r['longest_db_ms'] for r in reports),
        'total_bg_tasks': sum(r['background_tasks'] for r in reports)
    }
    
    # Calculate averages
    stats['avg_ui_freezes'] = stats['total_ui_freezes'] / stats['total_reports']
    
    if stats['total_db_operations'] > 0:
        total_db_time = sum(r['avg_db_time_ms'] * r['db_operations'] for r in reports)
        stats['avg_db_time_ms'] = total_db_time / stats['total_db_operations']
    else:
        stats['avg_db_time_ms'] = 0
    
    if stats['total_bg_tasks'] > 0:
        total_bg_time = sum(r['avg_bg_time_ms'] * r['background_tasks'] for r in reports)
        stats['avg_bg_time_ms'] = total_bg_time / stats['total_bg_tasks']
    else:
        stats['avg_bg_time_ms'] = 0
    
    return stats

def generate_charts(reports, output_dir='logs'):
    """Generate performance charts from reports"""
    if not reports:
        print("No reports to generate charts from")
        return
    
    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)
    
    # Extract data for plotting
    timestamps = [r['timestamp'] for r in reports]
    ui_freezes = [r['ui_freezes'] for r in reports]
    db_times = [r['avg_db_time_ms'] for r in reports]
    bg_times = [r['avg_bg_time_ms'] for r in reports]
    
    # Create figure
    plt.figure(figsize=(12, 8))
    
    # Plot UI freezes
    plt.subplot(3, 1, 1)
    plt.plot(timestamps, ui_freezes, 'r-', marker='o')
    plt.title('UI Freezes Over Time')
    plt.ylabel('Number of Freezes')
    plt.xticks(rotation=45)
    plt.grid(True)
    
    # Plot DB operation times
    plt.subplot(3, 1, 2)
    plt.plot(timestamps, db_times, 'b-', marker='s')
    plt.title('Average Database Operation Time')
    plt.ylabel('Time (ms)')
    plt.xticks(rotation=45)
    plt.grid(True)
    
    # Plot Background task times
    plt.subplot(3, 1, 3)
    plt.plot(timestamps, bg_times, 'g-', marker='^')
    plt.title('Average Background Task Time')
    plt.ylabel('Time (ms)')
    plt.xticks(rotation=45)
    plt.grid(True)
    
    plt.tight_layout()
    
    # Save the figure
    current_date = datetime.datetime.now().strftime("%Y%m%d")
    plt.savefig(os.path.join(output_dir, f'performance_trend_{current_date}.png'))
    
    print(f"Charts saved to {os.path.join(output_dir, f'performance_trend_{current_date}.png')}")

def print_summary(stats):
    """Print a summary of performance statistics"""
    print("\n=== PERFORMANCE SUMMARY ===")
    print(f"Total Reports: {stats['total_reports']}")
    print(f"UI Freezes: {stats['total_ui_freezes']} (avg: {stats['avg_ui_freezes']:.2f} per report)")
    print(f"Max UI Freeze: {stats['max_ui_freeze_ms']:.2f}ms")
    print(f"Database Operations: {stats['total_db_operations']}")
    print(f"Avg DB Operation Time: {stats['avg_db_time_ms']:.2f}ms")
    print(f"Max DB Operation Time: {stats['max_db_time_ms']:.2f}ms")
    print(f"Background Tasks: {stats['total_bg_tasks']}")
    print(f"Avg Background Task Time: {stats['avg_bg_time_ms']:.2f}ms")
    print("===========================\n")

def print_detailed_report(reports):
    """Print a detailed report of performance metrics"""
    print("\n=== DETAILED PERFORMANCE REPORT ===")
    
    for i, report in enumerate(reports):
        print(f"\nReport {i+1} - {report['timestamp']}")
        print(f"  UI Freezes: {report['ui_freezes']}")
        print(f"  Longest UI Freeze: {report['longest_ui_freeze_ms']:.2f}ms")
        print(f"  DB Operations: {report['db_operations']}")
        print(f"  Avg DB Time: {report['avg_db_time_ms']:.2f}ms")
        print(f"  Longest DB Op: {report['longest_db_ms']:.2f}ms")
        print(f"  Background Tasks: {report['background_tasks']}")
        print(f"  Avg BG Task Time: {report['avg_bg_time_ms']:.2f}ms")
    
    print("\n===================================")

def main():
    """Main function"""
    try:
        print("Performance Log Analyzer")
        print("=======================")
        
        # Find log files
        log_files = find_log_files()
        if not log_files:
            print("No performance log files found.")
            return
        
        print(f"Found {len(log_files)} log files.")
        
        # Parse all log files
        all_reports = []
        for log_file in log_files:
            reports = parse_log_file(log_file)
            all_reports.extend(reports)
            print(f"Parsed {len(reports)} reports from {log_file}")
        
        if not all_reports:
            print("No performance reports found in log files.")
            return
        
        # Analyze reports
        stats = analyze_reports(all_reports)
        
        # Print summary
        print_summary(stats)
        
        # Generate charts
        try:
            import matplotlib
            generate_charts(all_reports)
        except ImportError:
            print("Matplotlib not installed. Skipping chart generation.")
        
        # Ask if user wants detailed report
        answer = input("Print detailed report? (y/n): ")
        if answer.lower() in ['y', 'yes']:
            print_detailed_report(all_reports)
    
    except Exception as e:
        print(f"Error analyzing performance logs: {e}")

if __name__ == "__main__":
    main()
