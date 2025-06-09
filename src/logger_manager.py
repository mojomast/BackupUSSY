#!/usr/bin/env python3
"""
Logger Manager - Handles job logging and CSV output for Phase 5.
"""

import os
import csv
import logging
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

class LoggerManager:
    """Manages logging for archive jobs and cumulative logs."""
    
    def __init__(self, log_dir="../logs"):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        
        self.cumulative_log = self.log_dir / "archive_log.csv"
        self.current_job_log = None
        
        # Initialize cumulative CSV if it doesn't exist
        self._initialize_cumulative_log()
    
    def _initialize_cumulative_log(self):
        """Initialize the cumulative CSV log file with headers."""
        if not self.cumulative_log.exists():
            with open(self.cumulative_log, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow([
                    'timestamp',
                    'archive_name',
                    'folder_path',
                    'tape_device',
                    'mode',
                    'compression',
                    'copies',
                    'file_count',
                    'total_size_bytes',
                    'archive_size_bytes',
                    'checksum',
                    'duration_seconds',
                    'status',
                    'error_message'
                ])
            logger.info(f"Created cumulative log: {self.cumulative_log}")
    
    def start_job_log(self, folder_path, archive_name=None):
        """Start a new job log file."""
        if archive_name is None:
            folder_name = os.path.basename(os.path.abspath(folder_path))
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            archive_name = f"{folder_name}_{timestamp}"
        
        log_filename = f"job_{archive_name}.log"
        self.current_job_log = self.log_dir / log_filename
        
        # Create job-specific logger
        job_logger = logging.getLogger(f"job_{archive_name}")
        job_logger.setLevel(logging.INFO)
        
        # Remove existing handlers to avoid duplicates
        for handler in job_logger.handlers[:]:
            job_logger.removeHandler(handler)
        
        # Add file handler for this job
        file_handler = logging.FileHandler(self.current_job_log, encoding='utf-8')
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        job_logger.addHandler(file_handler)
        
        # Log job start
        job_logger.info(f"Archive job started for folder: {folder_path}")
        job_logger.info(f"Archive name: {archive_name}")
        
        logger.info(f"Started job log: {self.current_job_log}")
        return job_logger
    
    def log_job_details(self, job_logger, **details):
        """Log job configuration details."""
        job_logger.info("Job Configuration:")
        for key, value in details.items():
            job_logger.info(f"  {key}: {value}")
    
    def log_progress(self, job_logger, message):
        """Log progress message."""
        job_logger.info(f"PROGRESS: {message}")
    
    def log_error(self, job_logger, error_message, exception=None):
        """Log error message."""
        job_logger.error(f"ERROR: {error_message}")
        if exception:
            job_logger.exception("Exception details:", exc_info=exception)
    
    def finish_job_log(self, job_logger, status, **summary):
        """Finish the job log and add entry to cumulative log."""
        job_logger.info(f"Job completed with status: {status}")
        
        # Log summary
        if summary:
            job_logger.info("Job Summary:")
            for key, value in summary.items():
                job_logger.info(f"  {key}: {value}")
        
        # Add to cumulative log
        self._add_to_cumulative_log(status, **summary)
        
        # Close handlers
        for handler in job_logger.handlers[:]:
            handler.close()
            job_logger.removeHandler(handler)
        
        logger.info(f"Finished job log: {self.current_job_log}")
    
    def _add_to_cumulative_log(self, status, **summary):
        """Add job summary to cumulative CSV log."""
        try:
            with open(self.cumulative_log, 'a', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                
                row = [
                    datetime.now().isoformat(),
                    summary.get('archive_name', ''),
                    summary.get('folder_path', ''),
                    summary.get('tape_device', ''),
                    summary.get('mode', ''),
                    summary.get('compression', False),
                    summary.get('copies', 1),
                    summary.get('file_count', 0),
                    summary.get('total_size_bytes', 0),
                    summary.get('archive_size_bytes', 0),
                    summary.get('checksum', ''),
                    summary.get('duration_seconds', 0),
                    status,
                    summary.get('error_message', '')
                ]
                
                writer.writerow(row)
                
            logger.info(f"Added entry to cumulative log: {status}")
            
        except Exception as e:
            logger.error(f"Failed to update cumulative log: {e}")
    
    def get_recent_jobs(self, limit=10):
        """Get recent job entries from cumulative log."""
        jobs = []
        
        try:
            if not self.cumulative_log.exists():
                return jobs
            
            with open(self.cumulative_log, 'r', newline='', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                all_jobs = list(reader)
                
                # Return most recent jobs (last N entries)
                jobs = all_jobs[-limit:] if len(all_jobs) > limit else all_jobs
                jobs.reverse()  # Most recent first
                
        except Exception as e:
            logger.error(f"Failed to read cumulative log: {e}")
        
        return jobs
    
    def get_job_statistics(self):
        """Get statistics from all logged jobs."""
        stats = {
            'total_jobs': 0,
            'successful_jobs': 0,
            'failed_jobs': 0,
            'total_data_archived_bytes': 0,
            'total_files_archived': 0
        }
        
        try:
            if not self.cumulative_log.exists():
                return stats
            
            with open(self.cumulative_log, 'r', newline='', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                
                for row in reader:
                    stats['total_jobs'] += 1
                    
                    if row['status'].lower() == 'success':
                        stats['successful_jobs'] += 1
                    else:
                        stats['failed_jobs'] += 1
                    
                    try:
                        stats['total_data_archived_bytes'] += int(row['total_size_bytes'] or 0)
                        stats['total_files_archived'] += int(row['file_count'] or 0)
                    except (ValueError, TypeError):
                        pass
                        
        except Exception as e:
            logger.error(f"Failed to calculate statistics: {e}")
        
        return stats
    
    def export_log_summary(self, output_file=None, start_date=None, end_date=None):
        """Export a filtered summary of the log to a new CSV file."""
        if output_file is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = self.log_dir / f"archive_summary_{timestamp}.csv"
        
        try:
            filtered_rows = []
            
            with open(self.cumulative_log, 'r', newline='', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                
                for row in reader:
                    # Apply date filters if specified
                    if start_date or end_date:
                        try:
                            row_date = datetime.fromisoformat(row['timestamp']).date()
                            
                            if start_date and row_date < start_date:
                                continue
                            if end_date and row_date > end_date:
                                continue
                        except (ValueError, KeyError):
                            continue
                    
                    filtered_rows.append(row)
            
            # Write filtered results
            with open(output_file, 'w', newline='', encoding='utf-8') as f:
                if filtered_rows:
                    writer = csv.DictWriter(f, fieldnames=filtered_rows[0].keys())
                    writer.writeheader()
                    writer.writerows(filtered_rows)
            
            logger.info(f"Exported {len(filtered_rows)} records to {output_file}")
            return output_file, len(filtered_rows)
            
        except Exception as e:
            logger.error(f"Failed to export log summary: {e}")
            return None, 0
    
    def cleanup_old_logs(self, days_to_keep=30):
        """Remove job log files older than specified days."""
        if days_to_keep <= 0:
            return
        
        cutoff_time = datetime.now().timestamp() - (days_to_keep * 24 * 60 * 60)
        cleaned_count = 0
        
        try:
            for log_file in self.log_dir.glob("job_*.log"):
                if log_file.stat().st_mtime < cutoff_time:
                    log_file.unlink()
                    cleaned_count += 1
            
            if cleaned_count > 0:
                logger.info(f"Cleaned up {cleaned_count} old log files")
                
        except Exception as e:
            logger.error(f"Failed to cleanup old logs: {e}")
        
        return cleaned_count

