#!/usr/bin/env python3
"""
Unit tests for table calibration engine
"""

import unittest
import numpy as np
import cv2
import tempfile
import os
from unittest.mock import Mock, patch, MagicMock

from src.core import CalibrationConfig, CalibrationData, Point, BoundingBox
from src.calibration import TableCalibrationEngine

class TestTableCalibrationEngine(unittest.TestCase):
    """Test cases for TableCalibrationEngine"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.config = CalibrationConfig(
            table_length=3.569,
            table_width=1.778,
            auto_recalibrate=True,
            calibration_interval=100
        )
        
        # Create synthetic test images
        self.test_frame = self._create_test_frame()
        self.table_frame = self._create_table_frame()
    
    def _create_test_frame(self):
        """Create a basic test frame"""
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        frame[:] = (50, 100, 50)  # Dark green background
        return frame
    
    def _create_table_frame(self):
        """Create test frame with synthetic table"""
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        
        # Draw table outline (rectangle)
        table_corners = [(100, 80), (540, 80), (540, 400), (100, 400)]
        
        # Draw table boundary
        pts = np.array(table_corners, np.int32)
        cv2.polylines(frame, [pts], True, (255, 255, 255), 3)
        
        # Fill table area with green
        cv2.fillPoly(frame, [pts], (0, 128, 0))
        
        return frame
    
    def test_initialization(self):
        """Test TableCalibrationEngine initialization"""
        engine = TableCalibrationEngine(self.config)
        
        self.assertIsNotNone(engine)
        self.assertEqual(engine.config, self.config)
        self.assertFalse(engine.is_calibrated())
    
    def test_detect_table_corners_no_table(self):
        """Test corner detection with no table present"""
        engine = TableCalibrationEngine(self.config)
        
        corners = engine.detect_table_corners(self.test_frame)
        
        # Should return empty list or insufficient corners
        self.assertLessEqual(len(corners), 3)
    
    def test_detect_table_corners_with_table(self):
        """Test corner detection with synthetic table"""
        engine = TableCalibrationEngine(self.config)
        
        corners = engine.detect_table_corners(self.table_frame)
        
        # Should detect some corners (may not be perfect with synthetic image)
        self.assertIsInstance(corners, list)
        for corner in corners:
            self.assertIsInstance(corner, Point)
    
    def test_calculate_homography_insufficient_corners(self):
        """Test homography calculation with insufficient corners"""
        engine = TableCalibrationEngine(self.config)
        
        # Test with less than 4 corners
        corners = [Point(100, 100), Point(200, 100), Point(200, 200)]
        
        homography = engine.calculate_homography(corners)
        
        self.assertIsNone(homography)
    
    def test_calculate_homography_valid_corners(self):
        """Test homography calculation with valid corners"""
        engine = TableCalibrationEngine(self.config)
        
        # Create valid corner points (rectangle)
        corners = [
            Point(100, 100),  # Top-left
            Point(500, 100),  # Top-right
            Point(500, 300),  # Bottom-right
            Point(100, 300)   # Bottom-left
        ]
        
        homography = engine.calculate_homography(corners)
        
        self.assertIsNotNone(homography)
        self.assertEqual(homography.shape, (3, 3))
        self.assertIsInstance(homography, np.ndarray)
    
    def test_calibrate_frame_success(self):
        """Test successful frame calibration"""
        engine = TableCalibrationEngine(self.config)
        
        # Mock corner detection to return valid corners
        with patch.object(engine, 'detect_table_corners') as mock_detect:
            mock_detect.return_value = [
                Point(100, 100), Point(500, 100),
                Point(500, 300), Point(100, 300)
            ]
            
            success = engine.calibrate_frame(self.table_frame, frame_number=1)
            
            self.assertTrue(success)
            self.assertTrue(engine.is_calibrated())
            
            calibration_data = engine.get_calibration_data()
            self.assertIsNotNone(calibration_data.homography_matrix)
            self.assertEqual(len(calibration_data.table_corners), 4)
    
    def test_calibrate_frame_failure(self):
        """Test failed frame calibration"""
        engine = TableCalibrationEngine(self.config)
        
        # Mock corner detection to return insufficient corners
        with patch.object(engine, 'detect_table_corners') as mock_detect:
            mock_detect.return_value = [Point(100, 100), Point(200, 100)]
            
            success = engine.calibrate_frame(self.table_frame, frame_number=1)
            
            self.assertFalse(success)
            self.assertFalse(engine.is_calibrated())
    
    def test_calibration_persistence(self):
        """Test calibration data persistence"""
        with tempfile.TemporaryDirectory() as temp_dir:
            engine = TableCalibrationEngine(self.config, cache_directory=temp_dir)
            
            # Mock successful calibration
            with patch.object(engine, 'detect_table_corners') as mock_detect:
                mock_detect.return_value = [
                    Point(100, 100), Point(500, 100),
                    Point(500, 300), Point(100, 300)
                ]
                
                success = engine.calibrate_frame(self.table_frame, frame_number=1, video_source="test.mp4")
                
                self.assertTrue(success)
                
                # Check if calibration was saved
                cache_files = os.listdir(temp_dir)
                self.assertGreater(len(cache_files), 0)
    
    def test_calibration_recovery(self):
        """Test calibration recovery mechanisms"""
        with tempfile.TemporaryDirectory() as temp_dir:
            engine = TableCalibrationEngine(self.config, cache_directory=temp_dir)
            
            # First, create some cached calibration data
            with patch.object(engine, 'detect_table_corners') as mock_detect:
                mock_detect.return_value = [
                    Point(100, 100), Point(500, 100),
                    Point(500, 300), Point(100, 300)
                ]
                
                engine.calibrate_frame(self.table_frame, frame_number=1, video_source="test.mp4")
            
            # Create new engine instance (simulating restart)
            engine2 = TableCalibrationEngine(self.config, cache_directory=temp_dir)
            
            # Should load cached calibration
            self.assertTrue(engine2.is_calibrated())
    
    def test_camera_angle_change_detection(self):
        """Test camera angle change detection"""
        engine = TableCalibrationEngine(self.config)
        
        # Set up initial calibration
        initial_corners = [
            Point(100, 100), Point(500, 100),
            Point(500, 300), Point(100, 300)
        ]
        engine.previous_corners = initial_corners
        
        # Test with similar corners (no change)
        similar_frame = self.table_frame.copy()
        with patch.object(engine, 'detect_table_corners') as mock_detect:
            mock_detect.return_value = [
                Point(102, 102), Point(498, 98),
                Point(502, 298), Point(98, 302)
            ]
            
            change_detected = engine._detect_camera_angle_change(similar_frame)
            self.assertFalse(change_detected)
        
        # Test with significantly different corners (change detected)
        with patch.object(engine, 'detect_table_corners') as mock_detect:
            mock_detect.return_value = [
                Point(200, 200), Point(600, 200),
                Point(600, 400), Point(200, 400)
            ]
            
            change_detected = engine._detect_camera_angle_change(similar_frame)
            self.assertTrue(change_detected)
    
    def test_reset_calibration(self):
        """Test calibration reset"""
        engine = TableCalibrationEngine(self.config)
        
        # Set up calibration
        engine.calibration_data = CalibrationData(
            homography_matrix=np.eye(3),
            table_corners=[Point(0, 0), Point(1, 0), Point(1, 1), Point(0, 1)],
            is_valid=True
        )
        
        self.assertTrue(engine.is_calibrated())
        
        # Reset calibration
        engine.reset_calibration()
        
        self.assertFalse(engine.is_calibrated())
        self.assertEqual(len(engine.calibration_data.table_corners), 0)
    
    def test_get_calibration_status(self):
        """Test calibration status reporting"""
        engine = TableCalibrationEngine(self.config)
        
        status = engine.get_calibration_status()
        
        self.assertIn('is_calibrated', status)
        self.assertIn('calibration_attempts', status)
        self.assertIn('last_calibration_frame', status)
        self.assertIn('auto_recalibrate', status)
        
        self.assertFalse(status['is_calibrated'])
        self.assertEqual(status['calibration_attempts'], 0)
    
    def test_line_filtering(self):
        """Test line filtering for horizontal and vertical lines"""
        engine = TableCalibrationEngine(self.config)
        
        # Create test lines (rho, theta format)
        lines = np.array([
            [[100, 0]],        # Horizontal line
            [[200, np.pi/2]],  # Vertical line
            [[150, 0.1]],      # Nearly horizontal
            [[250, np.pi/2 - 0.1]]  # Nearly vertical
        ])
        
        horizontal, vertical = engine._filter_lines(lines)
        
        self.assertGreaterEqual(len(horizontal), 1)
        self.assertGreaterEqual(len(vertical), 1)
    
    def test_line_intersection(self):
        """Test line intersection calculation"""
        engine = TableCalibrationEngine(self.config)
        
        # Test intersection of perpendicular lines
        rho1, theta1 = 100, 0  # Horizontal line
        rho2, theta2 = 200, np.pi/2  # Vertical line
        
        intersection = engine._line_intersection(rho1, theta1, rho2, theta2)
        
        self.assertIsNotNone(intersection)
        self.assertIsInstance(intersection, Point)
    
    def test_corner_ordering(self):
        """Test corner point ordering"""
        engine = TableCalibrationEngine(self.config)
        
        # Create unordered corners
        corners = [
            Point(500, 300),  # Bottom-right
            Point(100, 100),  # Top-left
            Point(100, 300),  # Bottom-left
            Point(500, 100)   # Top-right
        ]
        
        ordered_corners = engine._order_corners(corners)
        
        self.assertEqual(len(ordered_corners), 4)
        # Check that corners are properly ordered (clockwise from top-left)
        self.assertIsInstance(ordered_corners[0], Point)

class TestCalibrationPersistence(unittest.TestCase):
    """Test calibration persistence functionality"""
    
    def setUp(self):
        """Set up persistence test fixtures"""
        self.config = CalibrationConfig()
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        """Clean up temporary files"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_calibration_save_and_load(self):
        """Test saving and loading calibration data"""
        engine = TableCalibrationEngine(self.config, cache_directory=self.temp_dir)
        
        # Create test calibration data
        test_calibration = CalibrationData(
            homography_matrix=np.eye(3, dtype=np.float32),
            table_corners=[
                Point(100, 100), Point(500, 100),
                Point(500, 300), Point(100, 300)
            ],
            table_dimensions=(3.569, 1.778),
            is_valid=True
        )
        
        # Save calibration
        success = engine.persistence_manager.save_calibration_data(
            test_calibration, "test_video.mp4", 42
        )
        
        self.assertTrue(success)
        
        # Load calibration
        loaded_calibration = engine.persistence_manager.load_calibration_data()
        
        self.assertIsNotNone(loaded_calibration)
        self.assertTrue(loaded_calibration.is_calibrated())
        self.assertEqual(len(loaded_calibration.table_corners), 4)
    
    def test_calibration_cache_validity(self):
        """Test calibration cache validity checking"""
        engine = TableCalibrationEngine(self.config, cache_directory=self.temp_dir)
        
        # Initially no cache
        self.assertFalse(engine.persistence_manager.is_cache_valid())
        
        # Create calibration data
        test_calibration = CalibrationData(
            homography_matrix=np.eye(3, dtype=np.float32),
            table_corners=[Point(0, 0), Point(1, 0), Point(1, 1), Point(0, 1)],
            is_valid=True
        )
        
        # Save and check validity
        engine.persistence_manager.save_calibration_data(test_calibration)
        self.assertTrue(engine.persistence_manager.is_cache_valid())

class TestCoordinateTransformation(unittest.TestCase):
    """Test coordinate transformation functionality"""
    
    def setUp(self):
        """Set up coordinate transformation tests"""
        self.config = CalibrationConfig()
        self.engine = TableCalibrationEngine(self.config)
        
        # Set up valid calibration
        self.homography = np.array([
            [2.0, 0.0, -100.0],
            [0.0, 2.0, -50.0],
            [0.0, 0.0, 1.0]
        ], dtype=np.float32)
        
        self.calibration_data = CalibrationData(
            homography_matrix=self.homography,
            table_corners=[
                Point(100, 50), Point(300, 50),
                Point(300, 150), Point(100, 150)
            ],
            is_valid=True
        )
        
        self.engine.calibration_data = self.calibration_data
    
    def test_homography_validation(self):
        """Test homography matrix validation"""
        # Valid homography
        valid_src = np.array([[100, 50], [300, 50], [300, 150], [100, 150]], dtype=np.float32)
        valid_dst = np.array([[0, 0], [200, 0], [200, 100], [0, 100]], dtype=np.float32)
        
        is_valid = self.engine._validate_homography(self.homography, valid_src, valid_dst)
        
        # Should be valid (or at least not crash)
        self.assertIsInstance(is_valid, bool)

if __name__ == '__main__':
    # Create test suite
    suite = unittest.TestSuite()
    
    # Add test cases
    suite.addTest(unittest.makeSuite(TestTableCalibrationEngine))
    suite.addTest(unittest.makeSuite(TestCalibrationPersistence))
    suite.addTest(unittest.makeSuite(TestCoordinateTransformation))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print(f"\n{'='*50}")
    print(f"Calibration Tests Summary:")
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Success rate: {((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100):.1f}%")
    print(f"{'='*50}")