#!/usr/bin/env python3
"""
Analysis plotting and charting for snooker detection system
"""

import logging
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.animation import FuncAnimation

# Optional seaborn import
try:
    import seaborn as sns
    HAS_SEABORN = True
except ImportError:
    HAS_SEABORN = False

from ..core import Detection, TrackedBall, FrameAnalysis, BallType, get_ball_name

logger = logging.getLogger(__name__)

class AnalysisPlotter:
    """Generate analysis plots and charts for detection system"""
    
    def __init__(self, style: str = "default", figsize: Tuple[int, int] = (12, 8)):
        self.style = style
        self.figsize = figsize
        
        # Set matplotlib style
        try:
            if HAS_SEABORN and style == "seaborn":
                sns.set_style("whitegrid")
            elif style != "default":
                plt.style.use(self.style)
        except:
            logger.warning(f"Style '{self.style}' not available, using default")
        
        # Color palette for different ball types
        self.ball_colors = {
            BallType.CUE_BALL: '#FFFFFF',
            BallType.YELLOW: '#FFFF00', 
            BallType.RED: '#FF0000',
            BallType.BROWN: '#8B4513',
            BallType.GREEN: '#008000',
            BallType.PINK: '#FFC0CB',
            BallType.BLUE: '#0000FF',
            BallType.BLACK: '#000000'
        }
    
    def plot_detection_statistics(self, analysis_history: List[FrameAnalysis],
                                save_path: Optional[str] = None) -> plt.Figure:
        """Plot detection statistics over time"""
        fig, axes = plt.subplots(2, 2, figsize=self.figsize)
        fig.suptitle('Detection Statistics Analysis', fontsize=16)
        
        # Extract data
        frame_numbers = [a.frame_number for a in analysis_history]
        detection_counts = [len(a.detections) for a in analysis_history]
        processing_times = [a.processing_time for a in analysis_history]
        
        # Ball type counts over time
        ball_type_counts = {ball_type: [] for ball_type in BallType}
        for analysis in analysis_history:
            type_count = {ball_type: 0 for ball_type in BallType}
            for detection in analysis.detections:
                ball_type = BallType(detection.class_id)
                type_count[ball_type] += 1
            
            for ball_type in BallType:
                ball_type_counts[ball_type].append(type_count[ball_type])
        
        # Plot 1: Detection count over time
        axes[0, 0].plot(frame_numbers, detection_counts, 'b-', linewidth=2)
        axes[0, 0].set_title('Detections per Frame')
        axes[0, 0].set_xlabel('Frame Number')
        axes[0, 0].set_ylabel('Detection Count')
        axes[0, 0].grid(True, alpha=0.3)
        
        # Plot 2: Processing time over time
        axes[0, 1].plot(frame_numbers, processing_times, 'r-', linewidth=2)
        axes[0, 1].set_title('Processing Time per Frame')
        axes[0, 1].set_xlabel('Frame Number')
        axes[0, 1].set_ylabel('Processing Time (s)')
        axes[0, 1].grid(True, alpha=0.3)
        
        # Plot 3: Ball type distribution
        ball_type_names = [get_ball_name(bt) for bt in BallType]
        total_detections = [sum(ball_type_counts[bt]) for bt in BallType]
        
        colors = [self.ball_colors[bt] for bt in BallType]
        axes[1, 0].bar(ball_type_names, total_detections, color=colors, edgecolor='black')
        axes[1, 0].set_title('Total Detections by Ball Type')
        axes[1, 0].set_xlabel('Ball Type')
        axes[1, 0].set_ylabel('Total Detections')
        axes[1, 0].tick_params(axis='x', rotation=45)
        
        # Plot 4: Detection confidence distribution
        all_confidences = []
        for analysis in analysis_history:
            all_confidences.extend([d.confidence for d in analysis.detections])
        
        if all_confidences:
            axes[1, 1].hist(all_confidences, bins=20, alpha=0.7, color='green', edgecolor='black')
            axes[1, 1].set_title('Detection Confidence Distribution')
            axes[1, 1].set_xlabel('Confidence Score')
            axes[1, 1].set_ylabel('Frequency')
            axes[1, 1].axvline(np.mean(all_confidences), color='red', linestyle='--', 
                              label=f'Mean: {np.mean(all_confidences):.3f}')
            axes[1, 1].legend()
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            logger.info(f"Detection statistics plot saved to {save_path}")
        
        return fig 
   
    def plot_trajectory_analysis(self, tracked_balls: List[TrackedBall],
                               table_dimensions: Tuple[float, float] = (3.569, 1.778),
                               save_path: Optional[str] = None) -> plt.Figure:
        """Plot ball trajectories and movement analysis"""
        fig, axes = plt.subplots(2, 2, figsize=self.figsize)
        fig.suptitle('Trajectory Analysis', fontsize=16)
        
        # Plot 1: 2D trajectory plot
        axes[0, 0].set_title('Ball Trajectories')
        axes[0, 0].set_xlabel('X Position')
        axes[0, 0].set_ylabel('Y Position')
        
        for ball in tracked_balls:
            if len(ball.trajectory) > 1:
                x_coords = [p.x for p in ball.trajectory]
                y_coords = [p.y for p in ball.trajectory]
                
                color = self.ball_colors.get(ball.ball_type, '#888888')
                axes[0, 0].plot(x_coords, y_coords, color=color, linewidth=2, 
                               label=f'{get_ball_name(ball.ball_type)} (ID:{ball.track_id})')
                
                # Mark start and end points
                axes[0, 0].scatter(x_coords[0], y_coords[0], color=color, s=100, 
                                  marker='o', edgecolor='green', linewidth=2)
                axes[0, 0].scatter(x_coords[-1], y_coords[-1], color=color, s=100, 
                                  marker='s', edgecolor='red', linewidth=2)
        
        axes[0, 0].legend(bbox_to_anchor=(1.05, 1), loc='upper left')
        axes[0, 0].grid(True, alpha=0.3)
        
        # Plot 2: Speed analysis
        axes[0, 1].set_title('Ball Speed Over Time')
        axes[0, 1].set_xlabel('Time Steps')
        axes[0, 1].set_ylabel('Speed (pixels/frame)')
        
        for ball in tracked_balls:
            if len(ball.trajectory) > 1:
                speeds = []
                for i in range(1, len(ball.trajectory)):
                    prev_pos = ball.trajectory[i-1]
                    curr_pos = ball.trajectory[i]
                    speed = np.sqrt((curr_pos.x - prev_pos.x)**2 + (curr_pos.y - prev_pos.y)**2)
                    speeds.append(speed)
                
                if speeds:
                    color = self.ball_colors.get(ball.ball_type, '#888888')
                    axes[0, 1].plot(speeds, color=color, linewidth=2, 
                                   label=f'{get_ball_name(ball.ball_type)}')
        
        axes[0, 1].legend()
        axes[0, 1].grid(True, alpha=0.3)
        
        # Plot 3: Distance traveled
        axes[1, 0].set_title('Total Distance Traveled')
        axes[1, 0].set_xlabel('Ball Type')
        axes[1, 0].set_ylabel('Distance (pixels)')
        
        ball_distances = {}
        for ball in tracked_balls:
            ball_name = get_ball_name(ball.ball_type)
            if ball_name not in ball_distances:
                ball_distances[ball_name] = 0
            
            # Calculate total distance
            total_distance = 0
            for i in range(1, len(ball.trajectory)):
                prev_pos = ball.trajectory[i-1]
                curr_pos = ball.trajectory[i]
                distance = np.sqrt((curr_pos.x - prev_pos.x)**2 + (curr_pos.y - prev_pos.y)**2)
                total_distance += distance
            
            ball_distances[ball_name] += total_distance
        
        if ball_distances:
            names = list(ball_distances.keys())
            distances = list(ball_distances.values())
            colors = [self.ball_colors.get(bt, '#888888') for bt in BallType 
                     if get_ball_name(bt) in names]
            
            axes[1, 0].bar(names, distances, color=colors[:len(names)], edgecolor='black')
            axes[1, 0].tick_params(axis='x', rotation=45)
        
        # Plot 4: Trajectory heatmap
        axes[1, 1].set_title('Position Heatmap')
        
        # Collect all positions
        all_x = []
        all_y = []
        for ball in tracked_balls:
            all_x.extend([p.x for p in ball.trajectory])
            all_y.extend([p.y for p in ball.trajectory])
        
        if all_x and all_y:
            # Create 2D histogram
            heatmap, xedges, yedges = np.histogram2d(all_x, all_y, bins=20)
            extent = [xedges[0], xedges[-1], yedges[0], yedges[-1]]
            
            im = axes[1, 1].imshow(heatmap.T, extent=extent, origin='lower', 
                                  cmap='hot', interpolation='bilinear')
            plt.colorbar(im, ax=axes[1, 1])
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            logger.info(f"Trajectory analysis plot saved to {save_path}")
        
        return fig
    
    def plot_system_performance(self, analysis_history: List[FrameAnalysis],
                              error_statistics: Dict[str, Any],
                              save_path: Optional[str] = None) -> plt.Figure:
        """Plot system performance metrics"""
        fig, axes = plt.subplots(2, 3, figsize=(15, 10))
        fig.suptitle('System Performance Analysis', fontsize=16)
        
        # Extract performance data
        frame_numbers = [a.frame_number for a in analysis_history]
        processing_times = [a.processing_time for a in analysis_history]
        
        # Plot 1: Processing time trend
        axes[0, 0].plot(frame_numbers, processing_times, 'b-', alpha=0.7)
        axes[0, 0].set_title('Processing Time Trend')
        axes[0, 0].set_xlabel('Frame Number')
        axes[0, 0].set_ylabel('Processing Time (s)')
        
        # Add moving average
        if len(processing_times) > 10:
            window_size = min(50, len(processing_times) // 10)
            moving_avg = np.convolve(processing_times, np.ones(window_size)/window_size, mode='valid')
            axes[0, 0].plot(frame_numbers[window_size-1:], moving_avg, 'r-', linewidth=2, 
                           label=f'Moving Average ({window_size} frames)')
            axes[0, 0].legend()
        
        axes[0, 0].grid(True, alpha=0.3)
        
        # Plot 2: FPS calculation
        if len(processing_times) > 1:
            fps_values = [1.0 / max(pt, 0.001) for pt in processing_times]
            axes[0, 1].plot(frame_numbers, fps_values, 'g-', alpha=0.7)
            axes[0, 1].set_title('Frames Per Second')
            axes[0, 1].set_xlabel('Frame Number')
            axes[0, 1].set_ylabel('FPS')
            axes[0, 1].axhline(y=30, color='r', linestyle='--', label='Target: 30 FPS')
            axes[0, 1].legend()
            axes[0, 1].grid(True, alpha=0.3)
        
        # Plot 3: Error distribution by category
        error_counts = error_statistics.get('error_counts_by_category', {})
        if error_counts:
            categories = list(error_counts.keys())
            counts = list(error_counts.values())
            
            axes[0, 2].pie(counts, labels=categories, autopct='%1.1f%%', startangle=90)
            axes[0, 2].set_title('Error Distribution by Category')
        
        # Plot 4: System health over time (simulated)
        axes[1, 0].set_title('System Health Status')
        # This would need actual health data over time
        health_status = error_statistics.get('system_health', {}).get('overall_status', 'healthy')
        health_color = 'green' if health_status == 'healthy' else 'orange' if health_status == 'degraded' else 'red'
        axes[1, 0].bar(['Current Status'], [1], color=health_color)
        axes[1, 0].set_ylabel('Health Level')
        axes[1, 0].text(0, 0.5, health_status.upper(), ha='center', va='center', fontsize=12, fontweight='bold')
        
        # Plot 5: Processing time distribution
        axes[1, 1].hist(processing_times, bins=20, alpha=0.7, color='blue', edgecolor='black')
        axes[1, 1].set_title('Processing Time Distribution')
        axes[1, 1].set_xlabel('Processing Time (s)')
        axes[1, 1].set_ylabel('Frequency')
        axes[1, 1].axvline(np.mean(processing_times), color='red', linestyle='--', 
                          label=f'Mean: {np.mean(processing_times):.3f}s')
        axes[1, 1].legend()
        
        # Plot 6: Recovery success rate
        recovery_rate = error_statistics.get('recovery_success_rate', 0.0)
        axes[1, 2].pie([recovery_rate, 1-recovery_rate], 
                      labels=['Successful', 'Failed'],
                      colors=['green', 'red'],
                      autopct='%1.1f%%',
                      startangle=90)
        axes[1, 2].set_title('Error Recovery Success Rate')
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            logger.info(f"System performance plot saved to {save_path}")
        
        return fig
    
    def create_detection_summary_report(self, analysis_history: List[FrameAnalysis],
                                      save_path: Optional[str] = None) -> Dict[str, Any]:
        """Create comprehensive detection summary report"""
        if not analysis_history:
            return {}
        
        # Calculate summary statistics
        total_frames = len(analysis_history)
        total_detections = sum(len(a.detections) for a in analysis_history)
        avg_detections_per_frame = total_detections / total_frames if total_frames > 0 else 0
        
        # Processing performance
        processing_times = [a.processing_time for a in analysis_history]
        avg_processing_time = np.mean(processing_times)
        max_processing_time = np.max(processing_times)
        min_processing_time = np.min(processing_times)
        
        # Ball type statistics
        ball_type_stats = {ball_type: 0 for ball_type in BallType}
        confidence_scores = []
        
        for analysis in analysis_history:
            for detection in analysis.detections:
                ball_type = BallType(detection.class_id)
                ball_type_stats[ball_type] += 1
                confidence_scores.append(detection.confidence)
        
        # Confidence statistics
        avg_confidence = np.mean(confidence_scores) if confidence_scores else 0
        min_confidence = np.min(confidence_scores) if confidence_scores else 0
        max_confidence = np.max(confidence_scores) if confidence_scores else 0
        
        summary = {
            'total_frames_analyzed': total_frames,
            'total_detections': total_detections,
            'avg_detections_per_frame': avg_detections_per_frame,
            'processing_performance': {
                'avg_processing_time': avg_processing_time,
                'max_processing_time': max_processing_time,
                'min_processing_time': min_processing_time,
                'avg_fps': 1.0 / avg_processing_time if avg_processing_time > 0 else 0
            },
            'detection_quality': {
                'avg_confidence': avg_confidence,
                'min_confidence': min_confidence,
                'max_confidence': max_confidence,
                'confidence_std': np.std(confidence_scores) if confidence_scores else 0
            },
            'ball_type_distribution': {
                get_ball_name(bt): count for bt, count in ball_type_stats.items()
            }
        }
        
        if save_path:
            import json
            with open(save_path, 'w') as f:
                json.dump(summary, f, indent=2, default=str)
            logger.info(f"Detection summary report saved to {save_path}")
        
        return summary