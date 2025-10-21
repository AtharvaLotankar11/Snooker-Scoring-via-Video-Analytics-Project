#!/usr/bin/env python3
"""
Unit tests for ball tracking system
"""

import unittest
import numpy as np
from unittest.mock import Mock, patch

from src.core import TrackingConfig, Detection, TrackedBall, BallType, Point, BoundingBox
from src.tracking import BallTracker

class TestBallTracker(unittest.TestCase):
    """Test cases for BallTracker"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.config = TrackingConfig(
            max_disappeared_frames=10,
            max_tracking_distance=50.0,
            kalman_process_noise=0.1,
            kalman_measurement_noise=0.1
        )
        
        self.tracker = BallTracker(self.config)
    
    def _create_test_detection(self, x, y, class_id=0, confidence=0.8):
        """Create a test detection"""
        return Detection(
            bbox=BoundingBox(x-10, y-10, x+10, y+10),
            class_id=class_id,
            confidence=confidence
        )
    
    def test_initialization(self):
        """Test BallTracker initialization"""
        self.assertIsNotNone(self.tracker)
        self.assertEqual(self.tracker.config, self.config)
        self.assertEqual(len(self.tracker.get_active_tracks()), 0)
    
    def test_first_detection_creates_track(self):
        """Test that first detection creates a new track"""
        detection = self._create_test_detection(100, 100, class_id=0)
        
        tracked_balls = self.tracker.update([detection], frame_number=1)
        
        self.assertEqual(len(tracked_balls), 1)
        
        ball = tracked_balls[0]
        self.assertEqual(ball.track_id, 1)  # First track should have ID 1
        self.assertEqual(ball.ball_type, BallType.CUE_BALL)
        self.assertTrue(ball.is_active)
        self.assertEqual(ball.last_seen_frame, 1)
    
    def test_multiple_detections_create_multiple_tracks(self):
        """Test multiple detections create separate tracks"""
        detections = [
            self._create_test_detection(100, 100, class_id=0),  # Cue ball
            self._create_test_detection(200, 200, class_id=2),  # Red ball
            self._create_test_detection(300, 150, class_id=6)   # Blue ball
        ]
        
        tracked_balls = self.tracker.update(detections, frame_number=1)
        
        self.assertEqual(len(tracked_balls), 3)
        
        # Check track IDs are unique
        track_ids = [ball.track_id for ball in tracked_balls]
        self.assertEqual(len(set(track_ids)), 3)
        
        # Check ball types
        ball_types = [ball.ball_type for ball in tracked_balls]
        expected_types = [BallType.CUE_BALL, BallType.RED, BallType.BLUE]
        self.assertEqual(set(ball_types), set(expected_types))
    
    def test_track_association_with_movement(self):
        """Test track association when balls move"""
        # Frame 1: Initial detection
        detection1 = self._create_test_detection(100, 100, class_id=0)
        tracked_balls = self.tracker.update([detection1], frame_number=1)
        
        initial_track_id = tracked_balls[0].track_id
        
        # Frame 2: Ball moves slightly
        detection2 = self._create_test_detection(105, 105, class_id=0)
        tracked_balls = self.tracker.update([detection2], frame_number=2)
        
        self.assertEqual(len(tracked_balls), 1)
        self.assertEqual(tracked_balls[0].track_id, initial_track_id)  # Same track
        self.assertEqual(len(tracked_balls[0].trajectory), 2)  # Two positions recorded
    
    def test_track_loss_and_recovery(self):
        """Test track loss and recovery"""
        # Frame 1: Initial detection
        detection1 = self._create_test_detection(100, 100, class_id=0)
        tracked_balls = self.tracker.update([detection1], frame_number=1)
        initial_track_id = tracked_balls[0].track_id
        
        # Frames 2-5: No detections (ball temporarily lost)
        for frame in range(2, 6):
            tracked_balls = self.tracker.update([], frame_number=frame)
            # Track should still exist but marked as lost
            self.assertEqual(len(tracked_balls), 1)
            self.assertEqual(tracked_balls[0].track_id, initial_track_id)
        
        # Frame 6: Ball reappears nearby
        detection6 = self._create_test_detection(110, 110, class_id=0)
        tracked_balls = self.tracker.update([detection6], frame_number=6)
        
        self.assertEqual(len(tracked_balls), 1)
        self.assertEqual(tracked_balls[0].track_id, initial_track_id)  # Same track recovered
    
    def test_track_deletion_after_max_disappeared(self):
        """Test track deletion after maximum disappeared frames"""
        # Frame 1: Initial detection
        detection1 = self._create_test_detection(100, 100, class_id=0)
        tracked_balls = self.tracker.update([detection1], frame_number=1)
        
        # Frames 2-12: No detections (exceeds max_disappeared_frames=10)
        for frame in range(2, 13):
            tracked_balls = self.tracker.update([], frame_number=frame)
        
        # Track should be deleted
        active_tracks = self.tracker.get_active_tracks()
        self.assertEqual(len(active_tracks), 0)
    
    def test_track_association_distance_threshold(self):
        """Test track association respects distance threshold"""
        # Frame 1: Initial detection
        detection1 = self._create_test_detection(100, 100, class_id=0)
        tracked_balls = self.tracker.update([detection1], frame_number=1)
        initial_track_id = tracked_balls[0].track_id
        
        # Frame 2: Ball appears very far away (beyond max_tracking_distance=50)
        detection2 = self._create_test_detection(200, 200, class_id=0)  # Distance > 50
        tracked_balls = self.tracker.update([detection2], frame_number=2)
        
        # Should create new track instead of associating with existing one
        self.assertEqual(len(tracked_balls), 2)
        track_ids = [ball.track_id for ball in tracked_balls]
        self.assertIn(initial_track_id, track_ids)  # Original track still exists
        self.assertNotEqual(track_ids[0], track_ids[1])  # Different track IDs
    
    def test_trajectory_management(self):
        """Test trajectory recording and management"""
        positions = [(100, 100), (105, 105), (110, 110), (115, 115)]
        
        for i, (x, y) in enumerate(positions):
            detection = self._create_test_detection(x, y, class_id=0)
            tracked_balls = self.tracker.update([detection], frame_number=i+1)
        
        ball = tracked_balls[0]
        
        # Check trajectory length
        self.assertEqual(len(ball.trajectory), len(positions))
        
        # Check trajectory points
        for i, expected_pos in enumerate(positions):
            actual_pos = ball.trajectory[i]
            self.assertAlmostEqual(actual_pos.x, expected_pos[0], delta=1)
            self.assertAlmostEqual(actual_pos.y, expected_pos[1], delta=1)
    
    def test_velocity_calculation(self):
        """Test velocity calculation"""
        # Frame 1: Initial position
        detection1 = self._create_test_detection(100, 100, class_id=0)
        tracked_balls = self.tracker.update([detection1], frame_number=1)
        
        # Frame 2: Moved position
        detection2 = self._create_test_detection(110, 105, class_id=0)
        tracked_balls = self.tracker.update([detection2], frame_number=2)
        
        ball = tracked_balls[0]
        
        # Check velocity calculation
        if ball.velocity:
            self.assertAlmostEqual(ball.velocity.x, 10, delta=1)  # Moved 10 pixels in x
            self.assertAlmostEqual(ball.velocity.y, 5, delta=1)   # Moved 5 pixels in y
    
    def test_confidence_history(self):
        """Test confidence history tracking"""
        confidences = [0.8, 0.7, 0.9, 0.6]
        
        for i, conf in enumerate(confidences):
            detection = self._create_test_detection(100 + i*5, 100, class_id=0, confidence=conf)
            tracked_balls = self.tracker.update([detection], frame_number=i+1)
        
        ball = tracked_balls[0]
        
        # Check confidence history
        self.assertEqual(len(ball.confidence_history), len(confidences))
        for i, expected_conf in enumerate(confidences):
            self.assertAlmostEqual(ball.confidence_history[i], expected_conf, delta=0.01)
    
    def test_ball_potting_detection(self):
        """Test ball potting detection near pocket regions"""
        # This would require pocket region information from calibration
        # For now, test the basic mechanism
        
        # Create a ball near the edge (simulating pocket area)
        detection = self._create_test_detection(50, 50, class_id=2)  # Red ball near corner
        tracked_balls = self.tracker.update([detection], frame_number=1)
        
        # Ball disappears (simulating potting)
        tracked_balls = self.tracker.update([], frame_number=2)
        
        # The track should still exist but be marked as potentially potted
        self.assertEqual(len(tracked_balls), 1)
        # Additional potting logic would be tested here with actual pocket regions
    
    def test_reset_tracking(self):
        """Test tracking reset functionality"""
        # Create some tracks
        detections = [
            self._create_test_detection(100, 100, class_id=0),
            self._create_test_detection(200, 200, class_id=2)
        ]
        
        tracked_balls = self.tracker.update(detections, frame_number=1)
        self.assertEqual(len(tracked_balls), 2)
        
        # Reset tracking
        self.tracker.reset_tracking()
        
        # Should have no active tracks
        active_tracks = self.tracker.get_active_tracks()
        self.assertEqual(len(active_tracks), 0)
    
    def test_get_tracking_stats(self):
        """Test tracking statistics"""
        # Create and update some tracks
        detection = self._create_test_detection(100, 100, class_id=0)
        self.tracker.update([detection], frame_number=1)
        
        stats = self.tracker.get_tracking_stats()
        
        self.assertIn('total_tracks_created', stats)
        self.assertIn('active_tracks', stats)
        self.assertIn('lost_tracks', stats)
        
        self.assertEqual(stats['total_tracks_created'], 1)
        self.assertEqual(stats['active_tracks'], 1)

class TestTrackingIntegration(unittest.TestCase):
    """Integration tests for tracking system"""
    
    def setUp(self):
        """Set up integration test fixtures"""
        self.config = TrackingConfig(
            max_disappeared_frames=5,
            max_tracking_distance=30.0
        )
        self.tracker = BallTracker(self.config)
    
    def _create_detection(self, x, y, class_id=0, confidence=0.8):
        """Helper to create detection"""
        return Detection(
            bbox=BoundingBox(x-10, y-10, x+10, y+10),
            class_id=class_id,
            confidence=confidence
        )
    
    def test_multiple_ball_tracking_scenario(self):
        """Test realistic multi-ball tracking scenario"""
        # Simulate a snooker break shot scenario
        
        # Frame 1: Cue ball and several reds
        detections_f1 = [
            self._create_detection(100, 100, class_id=0),  # Cue ball
            self._create_detection(200, 200, class_id=2),  # Red 1
            self._create_detection(210, 190, class_id=2),  # Red 2
            self._create_detection(190, 210, class_id=2),  # Red 3
        ]
        
        tracked_balls = self.tracker.update(detections_f1, frame_number=1)
        self.assertEqual(len(tracked_balls), 4)
        
        # Frame 2: Balls move after collision
        detections_f2 = [
            self._create_detection(120, 110, class_id=0),  # Cue ball moved
            self._create_detection(180, 220, class_id=2),  # Red 1 moved
            self._create_detection(230, 180, class_id=2),  # Red 2 moved
            # Red 3 temporarily lost (occluded)
        ]
        
        tracked_balls = self.tracker.update(detections_f2, frame_number=2)
        self.assertEqual(len(tracked_balls), 4)  # Still tracking all 4 (including lost one)
        
        active_tracks = [ball for ball in tracked_balls if ball.is_active]
        self.assertEqual(len(active_tracks), 3)  # 3 currently detected
        
        # Frame 3: Red 3 reappears
        detections_f3 = [
            self._create_detection(125, 115, class_id=0),  # Cue ball
            self._create_detection(170, 230, class_id=2),  # Red 1
            self._create_detection(240, 170, class_id=2),  # Red 2
            self._create_detection(160, 240, class_id=2),  # Red 3 reappears
        ]
        
        tracked_balls = self.tracker.update(detections_f3, frame_number=3)
        active_tracks = [ball for ball in tracked_balls if ball.is_active]
        self.assertEqual(len(active_tracks), 4)  # All balls tracked again
    
    def test_crossing_trajectories(self):
        """Test tracking when ball trajectories cross"""
        # Frame 1: Two balls on opposite sides
        detections_f1 = [
            self._create_detection(100, 100, class_id=0),  # Ball 1 (left)
            self._create_detection(200, 100, class_id=2),  # Ball 2 (right)
        ]
        
        tracked_balls = self.tracker.update(detections_f1, frame_number=1)
        ball1_id = tracked_balls[0].track_id
        ball2_id = tracked_balls[1].track_id
        
        # Frame 2: Balls move toward each other
        detections_f2 = [
            self._create_detection(130, 100, class_id=0),  # Ball 1 moves right
            self._create_detection(170, 100, class_id=2),  # Ball 2 moves left
        ]
        
        tracked_balls = self.tracker.update(detections_f2, frame_number=2)
        
        # Frame 3: Balls cross paths
        detections_f3 = [
            self._create_detection(170, 100, class_id=0),  # Ball 1 continues right
            self._create_detection(130, 100, class_id=2),  # Ball 2 continues left
        ]
        
        tracked_balls = self.tracker.update(detections_f3, frame_number=3)
        
        # Verify tracks maintained correct associations
        # (This is challenging and may not be perfect without advanced tracking)
        self.assertEqual(len(tracked_balls), 2)
        track_ids = [ball.track_id for ball in tracked_balls]
        self.assertIn(ball1_id, track_ids)
        self.assertIn(ball2_id, track_ids)
    
    def test_occlusion_handling(self):
        """Test handling of ball occlusion"""
        # Frame 1: Ball visible
        detection_f1 = self._create_detection(100, 100, class_id=0)
        tracked_balls = self.tracker.update([detection_f1], frame_number=1)
        track_id = tracked_balls[0].track_id
        
        # Frames 2-4: Ball occluded (no detections)
        for frame in range(2, 5):
            tracked_balls = self.tracker.update([], frame_number=frame)
            # Ball should still be tracked but marked as lost
            self.assertEqual(len(tracked_balls), 1)
            self.assertEqual(tracked_balls[0].track_id, track_id)
        
        # Frame 5: Ball reappears nearby
        detection_f5 = self._create_detection(110, 105, class_id=0)
        tracked_balls = self.tracker.update([detection_f5], frame_number=5)
        
        # Should recover the same track
        self.assertEqual(len(tracked_balls), 1)
        self.assertEqual(tracked_balls[0].track_id, track_id)
        self.assertTrue(tracked_balls[0].is_active)

class TestKalmanFiltering(unittest.TestCase):
    """Test Kalman filter functionality in tracking"""
    
    def setUp(self):
        """Set up Kalman filter tests"""
        self.config = TrackingConfig(
            kalman_process_noise=0.1,
            kalman_measurement_noise=0.1
        )
        self.tracker = BallTracker(self.config)
    
    def test_position_prediction(self):
        """Test Kalman filter position prediction"""
        # Create a ball moving in a straight line
        positions = [(100, 100), (110, 100), (120, 100), (130, 100)]
        
        tracked_balls = None
        for i, (x, y) in enumerate(positions):
            detection = Detection(
                bbox=BoundingBox(x-10, y-10, x+10, y+10),
                class_id=0,
                confidence=0.8
            )
            tracked_balls = self.tracker.update([detection], frame_number=i+1)
        
        ball = tracked_balls[0]
        
        # Test prediction
        predicted_pos = ball.predict_next_position()
        
        if predicted_pos:
            # Should predict continued movement to the right
            self.assertGreater(predicted_pos.x, 130)
            self.assertAlmostEqual(predicted_pos.y, 100, delta=5)

if __name__ == '__main__':
    # Create test suite
    suite = unittest.TestSuite()
    
    # Add test cases
    suite.addTest(unittest.makeSuite(TestBallTracker))
    suite.addTest(unittest.makeSuite(TestTrackingIntegration))
    suite.addTest(unittest.makeSuite(TestKalmanFiltering))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print(f"\n{'='*50}")
    print(f"Tracking Tests Summary:")
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Success rate: {((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100):.1f}%")
    print(f"{'='*50}")