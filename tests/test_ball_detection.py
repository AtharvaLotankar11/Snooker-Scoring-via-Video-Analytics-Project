#!/usr/bin/env python3
"""
Unit tests for ball detection engine
"""

import unittest
import numpy as np
import cv2
import tempfile
import os
from unittest.mock import Mock, patch, MagicMock

# Import the modules to test
from src.core import DetectionConfig, BallType, Detection, BoundingBox
from src.detection import BallDetectionEngine

class TestBallDetectionEngine(unittest.TestCase):
    """Test cases for BallDetectionEngine"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.config = DetectionConfig(
            model_path="test_model.pt",
            confidence_threshold=0.5,
            nms_threshold=0.4,
            device="cpu"
        )
        
        # Create synthetic test images
        self.test_frame = self._create_test_frame()
        self.test_frame_with_balls = self._create_test_frame_with_balls()
    
    def _create_test_frame(self):
        """Create a basic test frame"""
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        # Add some texture to make it more realistic
        frame[:] = (50, 100, 50)  # Dark green background
        return frame
    
    def _create_test_frame_with_balls(self):
        """Create test frame with synthetic ball-like objects"""
        frame = self._create_test_frame()
        
        # Draw synthetic balls
        # White cue ball
        cv2.circle(frame, (100, 100), 15, (255, 255, 255), -1)
        # Red ball
        cv2.circle(frame, (200, 150), 15, (0, 0, 255), -1)
        # Blue ball
        cv2.circle(frame, (300, 200), 15, (255, 0, 0), -1)
        
        return frame
    
    def test_initialization(self):
        """Test BallDetectionEngine initialization"""
        engine = BallDetectionEngine(self.config)
        
        self.assertIsNotNone(engine)
        self.assertEqual(engine.config, self.config)
        self.assertFalse(engine.is_model_loaded())
    
    @patch('src.detection.ball_detection_engine.YOLO')
    def test_model_loading_success(self, mock_yolo):
        """Test successful model loading"""
        # Mock YOLO model
        mock_model = Mock()
        mock_yolo.return_value = mock_model
        
        engine = BallDetectionEngine(self.config)
        success = engine.load_model("test_model.pt")
        
        self.assertTrue(success)
        self.assertTrue(engine.is_model_loaded())
        mock_yolo.assert_called_once_with("test_model.pt")
    
    @patch('src.detection.ball_detection_engine.YOLO')
    def test_model_loading_failure_with_fallback(self, mock_yolo):
        """Test model loading failure with fallback"""
        # First call fails, second succeeds (fallback)
        mock_model = Mock()
        mock_yolo.side_effect = [Exception("Model not found"), mock_model]
        
        engine = BallDetectionEngine(self.config)
        success = engine.load_model("nonexistent_model.pt")
        
        self.assertTrue(success)  # Should succeed with fallback
        self.assertTrue(engine.is_model_loaded())
        self.assertEqual(mock_yolo.call_count, 2)
    
    @patch('src.detection.ball_detection_engine.YOLO')
    def test_detect_balls_no_model(self, mock_yolo):
        """Test detection without loaded model"""
        engine = BallDetectionEngine(self.config)
        
        detections = engine.detect_balls(self.test_frame)
        
        self.assertEqual(len(detections), 0)
    
    @patch('src.detection.ball_detection_engine.YOLO')
    def test_detect_balls_with_results(self, mock_yolo):
        """Test ball detection with mock results"""
        # Mock YOLO model and results
        mock_model = Mock()
        mock_result = Mock()
        
        # Mock detection boxes and confidences
        mock_result.boxes = Mock()
        mock_result.boxes.xyxy = np.array([[100, 100, 130, 130], [200, 150, 230, 180]])
        mock_result.boxes.conf = np.array([0.8, 0.6])
        mock_result.boxes.cls = np.array([0, 2])  # cue ball, red ball
        
        mock_model.return_value = [mock_result]
        mock_yolo.return_value = mock_model
        
        engine = BallDetectionEngine(self.config)
        engine.load_model("test_model.pt")
        
        detections = engine.detect_balls(self.test_frame_with_balls)
        
        self.assertEqual(len(detections), 2)
        
        # Check first detection (cue ball)
        det1 = detections[0]
        self.assertEqual(det1.class_id, 0)
        self.assertEqual(det1.confidence, 0.8)
        self.assertEqual(det1.bbox.x1, 100)
        self.assertEqual(det1.bbox.y1, 100)
        
        # Check second detection (red ball)
        det2 = detections[1]
        self.assertEqual(det2.class_id, 2)
        self.assertEqual(det2.confidence, 0.6)
    
    @patch('src.detection.ball_detection_engine.YOLO')
    def test_confidence_threshold_filtering(self, mock_yolo):
        """Test confidence threshold filtering"""
        # Mock YOLO model with low confidence detections
        mock_model = Mock()
        mock_result = Mock()
        
        mock_result.boxes = Mock()
        mock_result.boxes.xyxy = np.array([[100, 100, 130, 130], [200, 150, 230, 180]])
        mock_result.boxes.conf = np.array([0.8, 0.3])  # Second detection below threshold
        mock_result.boxes.cls = np.array([0, 2])
        
        mock_model.return_value = [mock_result]
        mock_yolo.return_value = mock_model
        
        engine = BallDetectionEngine(self.config)
        engine.load_model("test_model.pt")
        
        detections = engine.detect_balls(self.test_frame_with_balls)
        
        # Should only return detection above threshold (0.5)
        self.assertEqual(len(detections), 1)
        self.assertEqual(detections[0].confidence, 0.8)
    
    @patch('src.detection.ball_detection_engine.YOLO')
    def test_set_confidence_threshold(self, mock_yolo):
        """Test setting confidence threshold"""
        mock_model = Mock()
        mock_yolo.return_value = mock_model
        
        engine = BallDetectionEngine(self.config)
        
        # Test setting new threshold
        engine.set_confidence_threshold(0.7)
        self.assertEqual(engine.confidence_threshold, 0.7)
        
        # Test invalid threshold (should not change)
        engine.set_confidence_threshold(1.5)
        self.assertEqual(engine.confidence_threshold, 0.7)  # Should remain unchanged
    
    def test_detection_validation(self):
        """Test detection validation logic"""
        engine = BallDetectionEngine(self.config)
        
        # Valid detection
        valid_detection = Detection(
            bbox=BoundingBox(100, 100, 130, 130),
            class_id=0,
            confidence=0.8
        )
        
        self.assertTrue(engine._validate_detection(valid_detection))
        
        # Invalid detection (confidence too low)
        invalid_detection = Detection(
            bbox=BoundingBox(100, 100, 130, 130),
            class_id=0,
            confidence=0.1
        )
        
        self.assertFalse(engine._validate_detection(invalid_detection))
    
    def test_get_detection_stats(self):
        """Test detection statistics"""
        engine = BallDetectionEngine(self.config)
        
        stats = engine.get_detection_stats()
        
        self.assertIn('total_detections', stats)
        self.assertIn('avg_confidence', stats)
        self.assertIn('detection_counts_by_class', stats)
        self.assertEqual(stats['total_detections'], 0)  # No detections yet
    
    def test_reset_stats(self):
        """Test statistics reset"""
        engine = BallDetectionEngine(self.config)
        
        # Simulate some detections
        engine.detection_stats['total_detections'] = 10
        engine.detection_stats['avg_confidence'] = 0.75
        
        engine.reset_stats()
        
        stats = engine.get_detection_stats()
        self.assertEqual(stats['total_detections'], 0)
        self.assertEqual(stats['avg_confidence'], 0.0)
    
    @patch('src.detection.ball_detection_engine.YOLO')
    def test_detection_consistency(self, mock_yolo):
        """Test detection consistency across multiple frames"""
        # Mock consistent detections
        mock_model = Mock()
        mock_result = Mock()
        
        mock_result.boxes = Mock()
        mock_result.boxes.xyxy = np.array([[100, 100, 130, 130]])
        mock_result.boxes.conf = np.array([0.8])
        mock_result.boxes.cls = np.array([0])
        
        mock_model.return_value = [mock_result]
        mock_yolo.return_value = mock_model
        
        engine = BallDetectionEngine(self.config)
        engine.load_model("test_model.pt")
        
        # Run detection multiple times
        detections1 = engine.detect_balls(self.test_frame_with_balls)
        detections2 = engine.detect_balls(self.test_frame_with_balls)
        
        # Should get consistent results
        self.assertEqual(len(detections1), len(detections2))
        self.assertEqual(detections1[0].class_id, detections2[0].class_id)
        self.assertEqual(detections1[0].confidence, detections2[0].confidence)
    
    def test_ball_type_conversion(self):
        """Test ball type conversion from class ID"""
        engine = BallDetectionEngine(self.config)
        
        # Test valid conversions
        self.assertEqual(engine._get_ball_type(0), BallType.CUE_BALL)
        self.assertEqual(engine._get_ball_type(2), BallType.RED)
        self.assertEqual(engine._get_ball_type(6), BallType.BLUE)
        
        # Test invalid class ID
        with self.assertRaises(ValueError):
            engine._get_ball_type(99)

class TestDetectionIntegration(unittest.TestCase):
    """Integration tests for detection with different scenarios"""
    
    def setUp(self):
        """Set up integration test fixtures"""
        self.config = DetectionConfig(
            confidence_threshold=0.3,
            device="cpu"
        )
    
    def test_detection_with_different_lighting(self):
        """Test detection robustness under different lighting conditions"""
        engine = BallDetectionEngine(self.config)
        
        # Create frames with different brightness levels
        dark_frame = np.full((480, 640, 3), 30, dtype=np.uint8)
        normal_frame = np.full((480, 640, 3), 128, dtype=np.uint8)
        bright_frame = np.full((480, 640, 3), 220, dtype=np.uint8)
        
        frames = [dark_frame, normal_frame, bright_frame]
        
        # Without a real model, we can't test actual detection
        # But we can test that the engine handles different inputs
        for frame in frames:
            detections = engine.detect_balls(frame)
            self.assertIsInstance(detections, list)
    
    def test_detection_with_empty_frame(self):
        """Test detection with empty/black frame"""
        engine = BallDetectionEngine(self.config)
        
        empty_frame = np.zeros((480, 640, 3), dtype=np.uint8)
        detections = engine.detect_balls(empty_frame)
        
        self.assertEqual(len(detections), 0)
    
    def test_detection_with_invalid_frame(self):
        """Test detection with invalid frame data"""
        engine = BallDetectionEngine(self.config)
        
        # Test with None
        detections = engine.detect_balls(None)
        self.assertEqual(len(detections), 0)
        
        # Test with wrong dimensions
        invalid_frame = np.zeros((100,), dtype=np.uint8)
        detections = engine.detect_balls(invalid_frame)
        self.assertEqual(len(detections), 0)

if __name__ == '__main__':
    # Create test suite
    suite = unittest.TestSuite()
    
    # Add test cases
    suite.addTest(unittest.makeSuite(TestBallDetectionEngine))
    suite.addTest(unittest.makeSuite(TestDetectionIntegration))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print(f"\n{'='*50}")
    print(f"Ball Detection Tests Summary:")
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Success rate: {((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100):.1f}%")
    print(f"{'='*50}")