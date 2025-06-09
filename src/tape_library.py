#!/usr/bin/env python3
"""
Tape Library Management - Advanced tape library optimization and management.
"""

import os
import json
import csv
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Optional, Tuple

logger = logging.getLogger(__name__)

class TapeLibrary:
    """Advanced tape library management and optimization."""
    
    def __init__(self, db_manager):
        self.db_manager = db_manager
        self.MAX_TAPE_CAPACITY = 6_000_000_000_000  # 6TB for LTO-7
        self.TAPE_EFFICIENCY_THRESHOLD = 0.85  # 85% full considered efficient
        
    def suggest_best_tape(self, estimated_size_bytes: int) -> Optional[Dict]:
        """Find the best tape for a new archive based on available space and efficiency."""
        try:
            tapes = self.db_manager.get_all_tapes()
            
            suitable_tapes = []
            for tape in tapes:
                if tape['tape_status'] != 'active':
                    continue
                    
                used_space = tape.get('total_size_bytes', 0) or 0
                remaining_space = self.MAX_TAPE_CAPACITY - used_space
                
                if remaining_space >= estimated_size_bytes:
                    tape['remaining_space'] = remaining_space
                    tape['utilization'] = used_space / self.MAX_TAPE_CAPACITY
                    tape['efficiency_score'] = self._calculate_efficiency_score(
                        used_space, estimated_size_bytes
                    )
                    suitable_tapes.append(tape)
            
            if not suitable_tapes:
                return None
            
            # Sort by efficiency score (best packing efficiency)
            suitable_tapes.sort(key=lambda x: x['efficiency_score'], reverse=True)
            
            best_tape = suitable_tapes[0]
            logger.info(
                f"Suggested tape: {best_tape['tape_label']} "
                f"(efficiency: {best_tape['efficiency_score']:.2f}, "
                f"remaining: {best_tape['remaining_space']/1024/1024/1024:.1f} GB)"
            )
            
            return best_tape
            
        except Exception as e:
            logger.error(f"Failed to suggest best tape: {e}")
            return None
    
    def _calculate_efficiency_score(self, used_space: int, new_archive_size: int) -> float:
        """Calculate efficiency score for tape packing."""
        future_utilization = (used_space + new_archive_size) / self.MAX_TAPE_CAPACITY
        
        # Prefer tapes that will be efficiently packed (close to threshold)
        if future_utilization <= self.TAPE_EFFICIENCY_THRESHOLD:
            # Higher score for better packing without exceeding threshold
            return future_utilization
        else:
            # Lower score if it would exceed efficiency threshold
            return future_utilization * 0.5
    
    def detect_duplicate_archives(self) -> List[Dict]:
        """Detect potential duplicate archives across tapes."""
        try:
            duplicates = []
            archives = self.db_manager.get_all_archives()
            
            # Group archives by source folder
            folder_groups = {}
            for archive in archives:
                folder = archive['source_folder']
                if folder not in folder_groups:
                    folder_groups[folder] = []
                folder_groups[folder].append(archive)
            
            # Find folders with multiple archives
            for folder, archive_list in folder_groups.items():
                if len(archive_list) > 1:
                    # Sort by date to identify potential duplicates
                    archive_list.sort(key=lambda x: x['archive_date'])
                    
                    # Check for archives created within short time windows
                    for i in range(len(archive_list) - 1):
                        current = archive_list[i]
                        next_archive = archive_list[i + 1]
                        
                        # Parse dates
                        current_date = datetime.fromisoformat(current['archive_date'])
                        next_date = datetime.fromisoformat(next_archive['archive_date'])
                        
                        # If archives are within 7 days, consider as potential duplicate
                        if (next_date - current_date).days <= 7:
                            duplicates.append({
                                'folder': folder,
                                'archives': [current, next_archive],
                                'time_diff_days': (next_date - current_date).days,
                                'size_diff_bytes': abs(
                                    current['archive_size_bytes'] - 
                                    next_archive['archive_size_bytes']
                                )
                            })
            
            logger.info(f"Found {len(duplicates)} potential duplicate groups")
            return duplicates
            
        except Exception as e:
            logger.error(f"Failed to detect duplicate archives: {e}")
            return []
    
    def optimize_tape_usage(self) -> Dict:
        """Analyze tape usage and suggest optimizations."""
        try:
            tapes = self.db_manager.get_all_tapes()
            optimization_report = {
                'underutilized_tapes': [],
                'full_tapes': [],
                'fragmented_tapes': [],
                'consolidation_suggestions': [],
                'total_wasted_space_gb': 0
            }
            
            total_wasted_space = 0
            
            for tape in tapes:
                if tape['tape_status'] != 'active':
                    continue
                    
                used_space = tape.get('total_size_bytes', 0) or 0
                utilization = used_space / self.MAX_TAPE_CAPACITY
                remaining_space = self.MAX_TAPE_CAPACITY - used_space
                
                if utilization < 0.3:  # Less than 30% used
                    optimization_report['underutilized_tapes'].append({
                        'tape_label': tape['tape_label'],
                        'utilization_percent': utilization * 100,
                        'wasted_space_gb': remaining_space / (1024**3)
                    })
                    total_wasted_space += remaining_space
                    
                elif utilization > 0.95:  # More than 95% used
                    optimization_report['full_tapes'].append({
                        'tape_label': tape['tape_label'],
                        'utilization_percent': utilization * 100,
                        'remaining_space_gb': remaining_space / (1024**3)
                    })
                    
                # Check for fragmentation (many small archives)
                archives = self.db_manager.get_tape_contents(tape['tape_id'])
                if len(archives) > 50:  # Many archives might indicate fragmentation
                    avg_archive_size = used_space / len(archives) if archives else 0
                    if avg_archive_size < 100_000_000:  # Less than 100MB average
                        optimization_report['fragmented_tapes'].append({
                            'tape_label': tape['tape_label'],
                            'archive_count': len(archives),
                            'avg_archive_size_mb': avg_archive_size / (1024**2)
                        })
            
            # Generate consolidation suggestions
            underutilized = optimization_report['underutilized_tapes']
            if len(underutilized) >= 2:
                # Sort by utilization
                underutilized.sort(key=lambda x: x['utilization_percent'])
                
                # Suggest consolidating lowest utilized tapes
                for i in range(0, len(underutilized) - 1, 2):
                    tape1 = underutilized[i]
                    tape2 = underutilized[i + 1]
                    
                    combined_utilization = (
                        tape1['utilization_percent'] + tape2['utilization_percent']
                    )
                    
                    if combined_utilization < 90:  # Would fit on one tape
                        optimization_report['consolidation_suggestions'].append({
                            'source_tapes': [tape1['tape_label'], tape2['tape_label']],
                            'combined_utilization': combined_utilization,
                            'space_savings_gb': (
                                tape1['wasted_space_gb'] + tape2['wasted_space_gb']
                            ) - (100 - combined_utilization) * self.MAX_TAPE_CAPACITY / (1024**3) / 100
                        })
            
            optimization_report['total_wasted_space_gb'] = total_wasted_space / (1024**3)
            
            logger.info(
                f"Optimization analysis complete: "
                f"{len(optimization_report['underutilized_tapes'])} underutilized, "
                f"{len(optimization_report['consolidation_suggestions'])} consolidation opportunities"
            )
            
            return optimization_report
            
        except Exception as e:
            logger.error(f"Failed to optimize tape usage: {e}")
            return {}
    
    def generate_tape_reports(self) -> Dict:
        """Generate comprehensive tape usage and statistics reports."""
        try:
            tapes = self.db_manager.get_all_tapes()
            archives = self.db_manager.get_all_archives()
            
            # Basic statistics
            total_tapes = len(tapes)
            active_tapes = len([t for t in tapes if t['tape_status'] == 'active'])
            total_archives = len(archives)
            
            # Calculate total storage statistics
            total_used_space = sum(t.get('total_size_bytes', 0) or 0 for t in tapes)
            total_capacity = total_tapes * self.MAX_TAPE_CAPACITY
            avg_utilization = (total_used_space / total_capacity * 100) if total_capacity > 0 else 0
            
            # Archive statistics
            archive_sizes = [a['archive_size_bytes'] for a in archives if a.get('archive_size_bytes')]
            avg_archive_size = sum(archive_sizes) / len(archive_sizes) if archive_sizes else 0
            
            # File type analysis
            file_types = {}
            for archive in archives:
                files = self.db_manager.get_archive_files(archive['archive_id'])
                for file_info in files:
                    file_type = file_info.get('file_type', 'unknown')
                    if file_type not in file_types:
                        file_types[file_type] = {'count': 0, 'size_bytes': 0}
                    file_types[file_type]['count'] += 1
                    file_types[file_type]['size_bytes'] += file_info.get('file_size_bytes', 0) or 0
            
            # Sort file types by size
            sorted_file_types = sorted(
                file_types.items(),
                key=lambda x: x[1]['size_bytes'],
                reverse=True
            )[:10]  # Top 10 file types
            
            # Monthly archive trends (last 12 months)
            monthly_trends = self._calculate_monthly_trends(archives)
            
            # Tape health analysis
            tape_health = self._analyze_tape_health(tapes)
            
            report = {
                'summary': {
                    'total_tapes': total_tapes,
                    'active_tapes': active_tapes,
                    'total_archives': total_archives,
                    'total_used_space_gb': total_used_space / (1024**3),
                    'total_capacity_gb': total_capacity / (1024**3),
                    'avg_utilization_percent': avg_utilization,
                    'avg_archive_size_gb': avg_archive_size / (1024**3)
                },
                'file_type_analysis': [
                    {
                        'type': ft[0],
                        'count': ft[1]['count'],
                        'size_gb': ft[1]['size_bytes'] / (1024**3),
                        'percentage': ft[1]['size_bytes'] / total_used_space * 100 if total_used_space > 0 else 0
                    }
                    for ft in sorted_file_types
                ],
                'monthly_trends': monthly_trends,
                'tape_health': tape_health,
                'efficiency_metrics': {
                    'space_efficiency': avg_utilization,
                    'archive_density': total_archives / total_tapes if total_tapes > 0 else 0,
                    'avg_archives_per_tape': total_archives / active_tapes if active_tapes > 0 else 0
                }
            }
            
            logger.info("Generated comprehensive tape usage report")
            return report
            
        except Exception as e:
            logger.error(f"Failed to generate tape reports: {e}")
            return {}
    
    def _calculate_monthly_trends(self, archives: List[Dict]) -> List[Dict]:
        """Calculate monthly archiving trends for the last 12 months."""
        monthly_data = {}
        
        # Initialize last 12 months
        current_date = datetime.now()
        for i in range(12):
            month_date = current_date.replace(day=1) - timedelta(days=30 * i)
            month_key = month_date.strftime('%Y-%m')
            monthly_data[month_key] = {'count': 0, 'size_bytes': 0}
        
        # Aggregate archive data by month
        for archive in archives:
            try:
                archive_date = datetime.fromisoformat(archive['archive_date'])
                month_key = archive_date.strftime('%Y-%m')
                
                if month_key in monthly_data:
                    monthly_data[month_key]['count'] += 1
                    monthly_data[month_key]['size_bytes'] += archive.get('archive_size_bytes', 0) or 0
            except (ValueError, TypeError):
                continue
        
        # Convert to sorted list
        return [
            {
                'month': month,
                'archive_count': data['count'],
                'total_size_gb': data['size_bytes'] / (1024**3)
            }
            for month, data in sorted(monthly_data.items())
        ]
    
    def _analyze_tape_health(self, tapes: List[Dict]) -> Dict:
        """Analyze tape health based on age, usage, and status."""
        health_analysis = {
            'healthy': 0,
            'warning': 0,
            'critical': 0,
            'details': []
        }
        
        current_date = datetime.now()
        
        for tape in tapes:
            health_score = 100  # Start with perfect health
            issues = []
            
            # Age analysis
            try:
                created_date = datetime.fromisoformat(tape['created_date'])
                age_days = (current_date - created_date).days
                
                if age_days > 1825:  # More than 5 years
                    health_score -= 30
                    issues.append(f"Tape is {age_days // 365} years old")
                elif age_days > 1095:  # More than 3 years
                    health_score -= 15
                    issues.append(f"Tape is {age_days // 365} years old")
            except (ValueError, TypeError):
                pass
            
            # Status analysis
            if tape['tape_status'] == 'damaged':
                health_score = 0
                issues.append("Tape marked as damaged")
            elif tape['tape_status'] == 'retired':
                health_score = 10
                issues.append("Tape is retired")
            
            # Usage analysis
            used_space = tape.get('total_size_bytes', 0) or 0
            utilization = used_space / self.MAX_TAPE_CAPACITY
            
            if utilization > 0.98:  # Very full
                health_score -= 10
                issues.append("Tape is nearly full")
            
            # Determine health category
            if health_score >= 80:
                category = 'healthy'
            elif health_score >= 50:
                category = 'warning'
            else:
                category = 'critical'
            
            health_analysis[category] += 1
            health_analysis['details'].append({
                'tape_label': tape['tape_label'],
                'health_score': health_score,
                'category': category,
                'issues': issues
            })
        
        return health_analysis
    
    def export_library_report(self, output_path: str, format_type: str = 'json') -> bool:
        """Export comprehensive library report to file."""
        try:
            report = self.generate_tape_reports()
            optimization = self.optimize_tape_usage()
            duplicates = self.detect_duplicate_archives()
            
            full_report = {
                'generated_date': datetime.now().isoformat(),
                'library_statistics': report,
                'optimization_analysis': optimization,
                'duplicate_detection': duplicates,
                'metadata': {
                    'version': '2.0',
                    'generator': 'LTO Tape Archive Tool - Professional Edition'
                }
            }
            
            if format_type.lower() == 'json':
                with open(output_path, 'w') as f:
                    json.dump(full_report, f, indent=2, default=str)
            else:
                # CSV format - flatten the data
                self._export_csv_report(full_report, output_path)
            
            logger.info(f"Library report exported to: {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to export library report: {e}")
            return False
    
    def _export_csv_report(self, report_data: Dict, output_path: str):
        """Export report data in CSV format."""
        # Create multiple CSV files in a directory
        output_dir = Path(output_path).parent / f"{Path(output_path).stem}_report"
        output_dir.mkdir(exist_ok=True)
        
        # Export summary statistics
        summary_path = output_dir / 'summary.csv'
        with open(summary_path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['Metric', 'Value'])
            for key, value in report_data['library_statistics']['summary'].items():
                writer.writerow([key.replace('_', ' ').title(), value])
        
        # Export file type analysis
        if 'file_type_analysis' in report_data['library_statistics']:
            filetype_path = output_dir / 'file_types.csv'
            with open(filetype_path, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['File Type', 'Count', 'Size (GB)', 'Percentage'])
                for ft in report_data['library_statistics']['file_type_analysis']:
                    writer.writerow([ft['type'], ft['count'], f"{ft['size_gb']:.2f}", f"{ft['percentage']:.1f}%"])
        
        # Export optimization suggestions
        if 'optimization_analysis' in report_data and 'consolidation_suggestions' in report_data['optimization_analysis']:
            optimization_path = output_dir / 'optimization.csv'
            with open(optimization_path, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['Source Tapes', 'Combined Utilization %', 'Space Savings (GB)'])
                for suggestion in report_data['optimization_analysis']['consolidation_suggestions']:
                    writer.writerow([
                        ', '.join(suggestion['source_tapes']),
                        f"{suggestion['combined_utilization']:.1f}%",
                        f"{suggestion['space_savings_gb']:.2f}"
                    ])
        
        logger.info(f"CSV report exported to directory: {output_dir}")
    
    def schedule_maintenance_tasks(self) -> Dict:
        """Suggest scheduled maintenance tasks based on library analysis."""
        try:
            maintenance_tasks = {
                'immediate': [],
                'weekly': [],
                'monthly': [],
                'annual': []
            }
            
            # Analyze current state
            optimization = self.optimize_tape_usage()
            duplicates = self.detect_duplicate_archives()
            report = self.generate_tape_reports()
            
            # Immediate tasks
            if optimization.get('total_wasted_space_gb', 0) > 500:  # More than 500GB wasted
                maintenance_tasks['immediate'].append({
                    'task': 'Tape Consolidation',
                    'description': f"Consolidate underutilized tapes to reclaim {optimization['total_wasted_space_gb']:.1f} GB",
                    'priority': 'high'
                })
            
            if len(duplicates) > 5:
                maintenance_tasks['immediate'].append({
                    'task': 'Duplicate Cleanup',
                    'description': f"Review and remove {len(duplicates)} duplicate archive groups",
                    'priority': 'medium'
                })
            
            # Critical health issues
            if 'tape_health' in report:
                critical_tapes = report['tape_health'].get('critical', 0)
                if critical_tapes > 0:
                    maintenance_tasks['immediate'].append({
                        'task': 'Tape Health Check',
                        'description': f"Inspect {critical_tapes} tapes with critical health issues",
                        'priority': 'high'
                    })
            
            # Weekly tasks
            maintenance_tasks['weekly'].extend([
                {
                    'task': 'Database Backup',
                    'description': 'Create backup of tape index database',
                    'priority': 'medium'
                },
                {
                    'task': 'Usage Report',
                    'description': 'Generate weekly usage and efficiency report',
                    'priority': 'low'
                }
            ])
            
            # Monthly tasks
            maintenance_tasks['monthly'].extend([
                {
                    'task': 'Full Library Audit',
                    'description': 'Complete audit of all tapes and archives',
                    'priority': 'medium'
                },
                {
                    'task': 'Optimization Analysis',
                    'description': 'Analyze library for consolidation opportunities',
                    'priority': 'medium'
                }
            ])
            
            # Annual tasks
            maintenance_tasks['annual'].extend([
                {
                    'task': 'Tape Lifecycle Review',
                    'description': 'Review tape ages and plan replacements',
                    'priority': 'high'
                },
                {
                    'task': 'Disaster Recovery Test',
                    'description': 'Test complete disaster recovery procedures',
                    'priority': 'high'
                }
            ])
            
            logger.info("Generated maintenance task schedule")
            return maintenance_tasks
            
        except Exception as e:
            logger.error(f"Failed to schedule maintenance tasks: {e}")
            return {}

