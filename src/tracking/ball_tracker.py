#!/usr/bin/env python3
"""
Ball tracking system using Kalman filters and Hungarian algorithm
"""

import logging
from typing import List, Dict, Optional, Tuple
import numpy as np
from scipy.optimize import linear_sum_assignment
import time

from ..core import ITracker, Detection, TrackedBall, BallType, TrackingConfig, Point

logger = logging.getLogger(__name__)

class KalmanFilter:
    """Simple Kalman filter for ball position tracking"""
    
    def __init__(self, initial_position: Point, process_noise: float = 0.1, measurement_noise: float = 0.1):
        # State vector: [x, y, vx, vy]
        self.state = np.array([initial_position.x, initial_position.y, 0.0, 0.0])
        
        # State transition matrix (constant velocity model)
        self.F = np.array([
            [1, 0, 1, 0],
            [0, 1, 0, 1],
            [0, 0, 1, 0],
            [0, 0, 0, 1]
        ])
        
        # Measurement matrix (we observe position only)
        self.H = np.array([
            [1, 0, 0, 0],
            [0, 1, 0, 0]
        ])
        
        # Process noise covariance
        self.Q = np.eye(4) * process_noise
        
        # Measurement noise covariance
        self.R = np.eye(2) * measurement_noise
        
        # Error covariance matrix
        self.P = np.eye(4) * 1000  # High initial uncertainty
        
        self.last_update_time = time.time()
    
    def predict(self) -> Point:
        """Predict next state"""
        # Update time step
        current_time = time.time()
        dt = current_time - self.last_update_time
        
        # Update state transition matrix with actual time step
        self.F[0, 2] = dt
        self.F[1, 3] = dt
        
        # Predict state
        self.state = self.F @ self.state
        
        # Predict error covariance
        self.P = self.F @ self.P @ self.F.T + self.Q
        
        return Point(self.state[0], self.state[1])
    
    def update(self, measurement: Point) -> Point:
        """Update filter with new measurement"""
        current_time = time.time()
        
        # Measurement vector
        z = np.array([measurement.x, measurement.y])
        
        # Innovation
        y = z - self.H @ self.state
        
        # Innovation covariance
        S = self.H @ self.P @ self.H.T + self.R
        
        # Kalman gain
        K = self.P @ self.H.T @ np.linalg.inv(S)
        
        # Update state
        self.state = self.state + K @ y
        
        # Update error covariance
        I = np.eye(4)
        self.P = (I - K @ self.H) @ self.P
        
        self.last_update_time = current_time
        
        return Point(self.state[0], self.state[1])
    
    def get_velocity(self) -> Point:
        """Get current velocity estimate"""
        return Point(self.state[2], self.state[3])
    
    def get_position(self) -> Point:
        """Get current position estimate"""
        return Point(self.state[0], self.state[1])

class BallTracker(ITracker):
    """Multi-object ball tracker using Kalman filters and Hungarian algorithm"""
    
    def __init__(self, config: TrackingConfig):
        self.config = config
        self.tracks: Dict[int, TrackedBall] = {}
        self.next_track_id = 1
        self.kalman_filters: Dict[int, KalmanFilter] = {}
        
        # Tracking statistics
        self.tracking_stats = {
            'total_tracks_created': 0,
            'total_tracks_lost': 0,
            'active_tracks': 0,
            'association_failures': 0
        }
    
    def update(self, detections: List[Detection], frame_number: int) -> List[TrackedBall]:
        """Update tracking with new detections"""
        if not detections:
            # No detections - predict all existing tracks
            self._predict_all_tracks(frame_number)
            self._cleanup_lost_tracks(frame_number)
            return self.get_active_tracks()
        
        # Predict existing tracks
        self._predict_all_tracks(frame_number)
        
        # Associate detections with existing tracks
        associations = self._associate_detections_to_tracks(detections)
        
        # Update associated tracks
        self._update_associated_tracks(associations, detections, frame_number)
        
        # Create new tracks for unassociated detections
        self._create_new_tracks(associations, detections, frame_number)
        
        # Clean up lost tracks
        self._cleanup_lost_tracks(frame_number)
        
        # Update statistics
        self.tracking_stats['active_tracks'] = len([t for t in self.tracks.values() if t.is_active])
        
        return self.get_active_tracks()
    
    def _predict_all_tracks(self, frame_number: int) -> None:
        """Predict positions for all active tracks"""
        for track_id, track in self.tracks.items():
            if track.is_active and track_id in self.kalman_filters:
                predicted_position = self.kalman_filters[track_id].predict()
                # Don't update the track position yet - just the Kalman filter internal state
    
    def _associate_detections_to_tracks(self, detections: List[Detection]) -> Dict[int, int]:
        """Associate detections to tracks using Hungarian algorithm"""
        if not self.tracks or not detections:
            return {}
        
        active_track_ids = [tid for tid, track in self.tracks.items() if track.is_active]
        
        if not active_track_ids:
            return {}
        
        # Create cost matrix
        cost_matrix = np.full((len(active_track_ids), len(detections)), float('inf'))
        
        for i, track_id in enumerate(active_track_ids):
            track = self.tracks[track_id]
            
            for j, detection in enumerate(detections):
                # Only associate same ball types
                if track.ball_type == detection.get_ball_type():
                    detection_center = detection.get_centroid()
                    distance = track.current_position.distance_to(detection_center)
                    
                    # Only consider associations within max distance
                    if distance <= self.config.max_tracking_distance:
                        cost_matrix[i, j] = distance
        
        # Solve assignment problem
        try:
            row_indices, col_indices = linear_sum_assignment(cost_matrix)
            
            associations = {}
            for row, col in zip(row_indices, col_indices):
                if cost_matrix[row, col] < float('inf'):
                    track_id = active_track_ids[row]
                    associations[track_id] = col
                else:
                    self.tracking_stats['association_failures'] += 1
            
            return associations
            
        except Exception as e:
            logger.error(f"Association failed: {e}")
            self.tracking_stats['association_failures'] += 1
            return {}
    
    def _update_associated_tracks(self, associations: Dict[int, int], 
                                detections: List[Detection], frame_number: int) -> None:
        """Update tracks that were associated with detections"""
        for track_id, detection_idx in associations.items():
            if track_id in self.tracks and detection_idx < len(detections):
                detection = detections[detection_idx]
                track = self.tracks[track_id]
                
                # Update Kalman filter
                if track_id in self.kalman_filters:
                    updated_position = self.kalman_filters[track_id].update(detection.get_centroid())
                    
                    # Use Kalman filter position if smoothing is enabled
                    if self.config.trajectory_smoothing:
                        final_position = updated_position
                    else:
                        final_position = detection.get_centroid()
                else:
                    final_position = detection.get_centroid()
                
                # Update track
                track.update_position(final_position, detection.confidence, frame_number)
                
                # Update velocity from Kalman filter
                if track_id in self.kalman_filters:
                    track.velocity = self.kalman_filters[track_id].get_velocity()
    
    def _create_new_tracks(self, associations: Dict[int, int], 
                          detections: List[Detection], frame_number: int) -> None:
        """Create new tracks for unassociated detections"""
        associated_detection_indices = set(associations.values())
        
        for i, detection in enumerate(detections):
            if i not in associated_detection_indices:
                # Create new track
                track_id = self.next_track_id
                self.next_track_id += 1
                
                detection_center = detection.get_centroid()
                
                new_track = TrackedBall(
                    track_id=track_id,
                    ball_type=detection.get_ball_type(),
                    current_position=detection_center,
                    trajectory=[detection_center],
                    confidence_history=[detection.confidence],
                    last_seen_frame=frame_number,
                    is_active=True
                )
                
                self.tracks[track_id] = new_track
                
                # Create Kalman filter for new track
                self.kalman_filters[track_id] = KalmanFilter(
                    detection_center,
                    self.config.kalman_process_noise,
                    self.config.kalman_measurement_noise
                )
                
                self.tracking_stats['total_tracks_created'] += 1
                
                logger.debug(f"Created new track {track_id} for {detection.get_ball_type().name}")
    
    def _cleanup_lost_tracks(self, frame_number: int) -> None:
        """Remove tracks that have been lost for too long"""
        tracks_to_remove = []
        
        for track_id, track in self.tracks.items():
            if track.is_lost(frame_number, self.config.max_disappeared_frames):
                track.is_active = False
                tracks_to_remove.append(track_id)
        
        for track_id in tracks_to_remove:
            if track_id in self.kalman_filters:
                del self.kalman_filters[track_id]
            
            self.tracking_stats['total_tracks_lost'] += 1
            logger.debug(f"Lost track {track_id}")
        
        # Remove inactive tracks after some time to prevent memory buildup
        inactive_threshold = frame_number - (self.config.max_disappeared_frames * 2)
        tracks_to_delete = []
        
        for track_id, track in self.tracks.items():
            if not track.is_active and track.last_seen_frame < inactive_threshold:
                tracks_to_delete.append(track_id)
        
        for track_id in tracks_to_delete:
            del self.tracks[track_id]
    
    def get_active_tracks(self) -> List[TrackedBall]:
        """Get currently active tracks"""
        return [track for track in self.tracks.values() if track.is_active]
    
    def reset_tracking(self) -> None:
        """Reset all tracking data"""
        self.tracks.clear()
        self.kalman_filters.clear()
        self.next_track_id = 1
        
        # Reset statistics
        self.tracking_stats = {
            'total_tracks_created': 0,
            'total_tracks_lost': 0,
            'active_tracks': 0,
            'association_failures': 0
        }
        
        logger.info("Tracking data reset")
    
    def get_track_by_id(self, track_id: int) -> Optional[TrackedBall]:
        """Get specific track by ID"""
        return self.tracks.get(track_id)
    
    def get_tracks_by_ball_type(self, ball_type: BallType) -> List[TrackedBall]:
        """Get all tracks of a specific ball type"""
        return [track for track in self.tracks.values() 
                if track.ball_type == ball_type and track.is_active]
    
    def get_tracking_stats(self) -> Dict:
        """Get tracking performance statistics"""
        return self.tracking_stats.copy()
    
    def predict_ball_positions(self, frames_ahead: int = 1) -> Dict[int, Point]:
        """Predict ball positions for future frames"""
        predictions = {}
        
        for track_id, track in self.tracks.items():
            if track.is_active and track.velocity and track_id in self.kalman_filters:
                # Use Kalman filter for prediction
                current_pos = self.kalman_filters[track_id].get_position()
                velocity = self.kalman_filters[track_id].get_velocity()
                
                # Simple linear prediction
                predicted_x = current_pos.x + velocity.x * frames_ahead
                predicted_y = current_pos.y + velocity.y * frames_ahead
                
                predictions[track_id] = Point(predicted_x, predicted_y)
        
        return predictions
    
    def visualize_tracks(self, frame: np.ndarray) -> np.ndarray:
        """Draw tracking visualization on frame"""
        import cv2
        from ..core import get_ball_color
        
        vis_frame = frame.copy()
        
        for track in self.get_active_tracks():
            color = get_ball_color(track.ball_type)
            
            # Draw current position
            pos = track.current_position
            cv2.circle(vis_frame, (int(pos.x), int(pos.y)), 8, color, -1)
            
            # Draw track ID
            cv2.putText(vis_frame, f"ID:{track.track_id}", 
                       (int(pos.x) + 10, int(pos.y) - 10),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)
            
            # Draw trajectory
            if len(track.trajectory) > 1:
                trajectory_points = [(int(p.x), int(p.y)) for p in track.trajectory[-20:]]  # Last 20 points
                for i in range(1, len(trajectory_points)):
                    cv2.line(vis_frame, trajectory_points[i-1], trajectory_points[i], color, 2)
            
            # Draw velocity vector
            if track.velocity:
                vel_end_x = int(pos.x + track.velocity.x * 10)  # Scale velocity for visualization
                vel_end_y = int(pos.y + track.velocity.y * 10)
                cv2.arrowedLine(vis_frame, (int(pos.x), int(pos.y)), 
                               (vel_end_x, vel_end_y), color, 2)
        
        # Draw tracking statistics
        stats = self.get_tracking_stats()
        cv2.putText(vis_frame, f"Active Tracks: {stats['active_tracks']}", 
                   (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        cv2.putText(vis_frame, f"Total Created: {stats['total_tracks_created']}", 
                   (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        
        return vis_frame