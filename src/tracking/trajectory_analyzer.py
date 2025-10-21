#!/usr/bin/env python3
"""
Trajectory analysis and ball state tracking utilities
"""

import logging
from typing import List, Dict, Optional, Tuple
import numpy as np
from enum import Enum

from ..core import TrackedBall, Point, BallType, CalibrationData
from ..calibration import TableGeometry

logger = logging.getLogger(__name__)

class BallState(Enum):
    """Ball state enumeration"""
    STATIONARY = "stationary"
    MOVING = "moving"
    POTTED = "potted"
    LOST = "lost"
    COLLISION = "collision"

class TrajectoryAnalyzer:
    """Analyzes ball trajectories and detects events"""
    
    def __init__(self, calibration_data: Optional[CalibrationData] = None):
        self.calibration_data = calibration_data
        self.table_geometry = TableGeometry(calibration_data) if calibration_data else None
        
        # Analysis parameters
        self.motion_threshold = 5.0  # pixels per frame
        self.stationary_frames = 10  # frames to consider stationary
        self.pocket_threshold = 30.0  # distance to pocket for potting detection
        
        # Event history
        self.detected_events = []
        self.ball_states: Dict[int, BallState] = {}
        
    def analyze_trajectory(self, tracked_ball: TrackedBall) -> Dict:
        """Analyze a single ball's trajectory"""
        analysis = {
            'track_id': tracked_ball.track_id,
            'ball_type': tracked_ball.ball_type.name,
            'current_state': self._determine_ball_state(tracked_ball),
            'trajectory_length': len(tracked_ball.trajectory),
            'total_distance': self._calculate_total_distance(tracked_ball.trajectory),
            'average_speed': self._calculate_average_speed(tracked_ball),
            'direction_changes': self._count_direction_changes(tracked_ball.trajectory),
            'near_pocket': self._is_near_pocket(tracked_ball.current_position),
            'collision_detected': self._detect_collision(tracked_ball)
        }
        
        # Update ball state
        self.ball_states[tracked_ball.track_id] = analysis['current_state']
        
        return analysis
    
    def _determine_ball_state(self, tracked_ball: TrackedBall) -> BallState:
        """Determine current state of the ball"""
        if not tracked_ball.is_active:
            return BallState.LOST
        
        # Check if ball is potted (near pocket and low velocity)
        if self._is_ball_potted(tracked_ball):
            return BallState.POTTED
        
        # Check if ball is moving
        if self._is_ball_moving(tracked_ball):
            # Check for collision
            if self._detect_collision(tracked_ball):
                return BallState.COLLISION
            return BallState.MOVING
        
        return BallState.STATIONARY
    
    def _is_ball_moving(self, tracked_ball: TrackedBall) -> bool:
        """Check if ball is currently moving"""
        if not tracked_ball.velocity:
            return False
        
        speed = np.sqrt(tracked_ball.velocity.x**2 + tracked_ball.velocity.y**2)
        return speed > self.motion_threshold
    
    def _is_ball_potted(self, tracked_ball: TrackedBall) -> bool:
        """Check if ball has been potted"""
        if not self.table_geometry:
            return False
        
        # Check if ball is near a pocket and has low velocity
        near_pocket, pocket_id = self.table_geometry.is_point_near_pocket(
            tracked_ball.current_position, self.pocket_threshold
        )
        
        if near_pocket:
            # Check if ball has been stationary near pocket for several frames
            recent_positions = tracked_ball.trajectory[-5:] if len(tracked_ball.trajectory) >= 5 else tracked_ball.trajectory
            
            if len(recent_positions) >= 3:
                # Check if all recent positions are near the same pocket
                all_near_pocket = all(
                    self.table_geometry.is_point_near_pocket(pos, self.pocket_threshold)[0]
                    for pos in recent_positions
                )
                
                if all_near_pocket and not self._is_ball_moving(tracked_ball):
                    return True
        
        return False
    
    def _is_near_pocket(self, position: Point) -> Tuple[bool, int]:
        """Check if position is near any pocket"""
        if not self.table_geometry:
            return False, -1
        
        return self.table_geometry.is_point_near_pocket(position, self.pocket_threshold)
    
    def _detect_collision(self, tracked_ball: TrackedBall) -> bool:
        """Detect if ball has collided with another object"""
        if len(tracked_ball.trajectory) < 5:
            return False
        
        # Look for sudden direction changes in recent trajectory
        recent_trajectory = tracked_ball.trajectory[-5:]
        
        if len(recent_trajectory) < 3:
            return False
        
        # Calculate direction vectors
        directions = []
        for i in range(1, len(recent_trajectory)):
            dx = recent_trajectory[i].x - recent_trajectory[i-1].x
            dy = recent_trajectory[i].y - recent_trajectory[i-1].y
            
            if dx != 0 or dy != 0:  # Avoid zero vectors
                directions.append(np.array([dx, dy]))
        
        if len(directions) < 2:
            return False
        
        # Check for significant direction change
        for i in range(1, len(directions)):
            prev_dir = directions[i-1]
            curr_dir = directions[i]
            
            # Normalize vectors
            prev_norm = prev_dir / (np.linalg.norm(prev_dir) + 1e-6)
            curr_norm = curr_dir / (np.linalg.norm(curr_dir) + 1e-6)
            
            # Calculate angle between directions
            dot_product = np.dot(prev_norm, curr_norm)
            dot_product = np.clip(dot_product, -1.0, 1.0)  # Ensure valid range
            angle = np.arccos(dot_product)
            
            # If angle is greater than 45 degrees, consider it a collision
            if angle > np.pi / 4:
                return True
        
        return False
    
    def _calculate_total_distance(self, trajectory: List[Point]) -> float:
        """Calculate total distance traveled"""
        if len(trajectory) < 2:
            return 0.0
        
        total_distance = 0.0
        for i in range(1, len(trajectory)):
            total_distance += trajectory[i-1].distance_to(trajectory[i])
        
        return total_distance
    
    def _calculate_average_speed(self, tracked_ball: TrackedBall) -> float:
        """Calculate average speed over trajectory"""
        if len(tracked_ball.trajectory) < 2:
            return 0.0
        
        total_distance = self._calculate_total_distance(tracked_ball.trajectory)
        time_frames = len(tracked_ball.trajectory) - 1
        
        return total_distance / time_frames if time_frames > 0 else 0.0
    
    def _count_direction_changes(self, trajectory: List[Point], threshold: float = np.pi/6) -> int:
        """Count significant direction changes in trajectory"""
        if len(trajectory) < 3:
            return 0
        
        direction_changes = 0
        
        for i in range(2, len(trajectory)):
            # Calculate direction vectors
            dir1 = np.array([trajectory[i-1].x - trajectory[i-2].x, 
                           trajectory[i-1].y - trajectory[i-2].y])
            dir2 = np.array([trajectory[i].x - trajectory[i-1].x, 
                           trajectory[i].y - trajectory[i-1].y])
            
            # Skip if either vector is zero
            if np.linalg.norm(dir1) < 1e-6 or np.linalg.norm(dir2) < 1e-6:
                continue
            
            # Normalize vectors
            dir1_norm = dir1 / np.linalg.norm(dir1)
            dir2_norm = dir2 / np.linalg.norm(dir2)
            
            # Calculate angle between directions
            dot_product = np.dot(dir1_norm, dir2_norm)
            dot_product = np.clip(dot_product, -1.0, 1.0)
            angle = np.arccos(dot_product)
            
            if angle > threshold:
                direction_changes += 1
        
        return direction_changes
    
    def detect_potting_events(self, tracked_balls: List[TrackedBall]) -> List[Dict]:
        """Detect ball potting events"""
        potting_events = []
        
        for ball in tracked_balls:
            analysis = self.analyze_trajectory(ball)
            
            if analysis['current_state'] == BallState.POTTED:
                near_pocket, pocket_id = analysis['near_pocket']
                
                if near_pocket:
                    event = {
                        'event_type': 'ball_potted',
                        'track_id': ball.track_id,
                        'ball_type': ball.ball_type.name,
                        'pocket_id': pocket_id,
                        'position': ball.current_position,
                        'frame': ball.last_seen_frame,
                        'confidence': np.mean(ball.confidence_history[-5:]) if ball.confidence_history else 0.0
                    }
                    
                    potting_events.append(event)
                    self.detected_events.append(event)
        
        return potting_events
    
    def detect_collision_events(self, tracked_balls: List[TrackedBall]) -> List[Dict]:
        """Detect ball collision events"""
        collision_events = []
        
        # Check for ball-to-ball collisions
        for i, ball1 in enumerate(tracked_balls):
            for j, ball2 in enumerate(tracked_balls[i+1:], i+1):
                if self._detect_ball_collision(ball1, ball2):
                    event = {
                        'event_type': 'ball_collision',
                        'ball1_id': ball1.track_id,
                        'ball2_id': ball2.track_id,
                        'ball1_type': ball1.ball_type.name,
                        'ball2_type': ball2.ball_type.name,
                        'collision_point': self._estimate_collision_point(ball1, ball2),
                        'frame': max(ball1.last_seen_frame, ball2.last_seen_frame)
                    }
                    
                    collision_events.append(event)
                    self.detected_events.append(event)
        
        return collision_events
    
    def _detect_ball_collision(self, ball1: TrackedBall, ball2: TrackedBall) -> bool:
        """Detect collision between two balls"""
        # Check if balls are close enough
        distance = ball1.current_position.distance_to(ball2.current_position)
        
        # Typical snooker ball diameter is about 52.5mm, in pixels this might be ~20-30 pixels
        collision_distance = 25.0  # pixels
        
        if distance > collision_distance:
            return False
        
        # Check if both balls show collision indicators in their trajectories
        ball1_collision = self._detect_collision(ball1)
        ball2_collision = self._detect_collision(ball2)
        
        return ball1_collision and ball2_collision
    
    def _estimate_collision_point(self, ball1: TrackedBall, ball2: TrackedBall) -> Point:
        """Estimate collision point between two balls"""
        # Simple midpoint estimation
        x = (ball1.current_position.x + ball2.current_position.x) / 2
        y = (ball1.current_position.y + ball2.current_position.y) / 2
        
        return Point(x, y)
    
    def get_trajectory_summary(self, tracked_balls: List[TrackedBall]) -> Dict:
        """Get summary of all trajectories"""
        summary = {
            'total_balls': len(tracked_balls),
            'active_balls': len([b for b in tracked_balls if b.is_active]),
            'ball_states': {},
            'total_events': len(self.detected_events),
            'average_trajectory_length': 0.0,
            'total_distance_traveled': 0.0
        }
        
        # Count ball states
        for state in BallState:
            summary['ball_states'][state.value] = 0
        
        total_trajectory_length = 0
        total_distance = 0.0
        
        for ball in tracked_balls:
            analysis = self.analyze_trajectory(ball)
            state = analysis['current_state']
            summary['ball_states'][state.value] += 1
            
            total_trajectory_length += analysis['trajectory_length']
            total_distance += analysis['total_distance']
        
        if tracked_balls:
            summary['average_trajectory_length'] = total_trajectory_length / len(tracked_balls)
            summary['total_distance_traveled'] = total_distance
        
        return summary
    
    def reset_analysis(self) -> None:
        """Reset analysis data"""
        self.detected_events.clear()
        self.ball_states.clear()
        logger.info("Trajectory analysis data reset")
    
    def update_calibration_data(self, calibration_data: CalibrationData) -> None:
        """Update calibration data for analysis"""
        self.calibration_data = calibration_data
        self.table_geometry = TableGeometry(calibration_data) if calibration_data else None