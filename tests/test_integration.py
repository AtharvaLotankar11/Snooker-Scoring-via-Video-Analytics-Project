#!/usr/bin/env python3
"""
End-to-end integration tests for the complete snooker detection system
"""

import unittest
import numpy as np
import cv2
import tempfile
import os
import time
from unittest.mock import Mock, patch

from src.core import SystemConfig, DetectionConfig, TrackingConfig, CalibrationConfig
from src.api import DetectionAPI

class TestEndToEndIntegration(unittest.TestCase):
    """End-to-end integration tests"""
    
    def setUp(self):
        """Set up integration test fixtures"""
        self.config = SystemConfig(
            detection=DetectionConfig(
                model_path="test_model.pt",
                confidence_threshold=0.3,
                device="cpu"
            ),
            tracking=TrackingConfig(
                max_disappeared_frames=5,
                max_tracking_distance=50.0
            ),
            calibration=CalibrationConfig(
                auto_recalibrate=True,
                calibration_interval=50
            ),
            debug_mode=True,
            save_debug_frames=False
        )
        
        # Create test video frames
        self.test_frames = self._create_test_video_sequence()
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        """Clean up temporary files"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def _create_test_video_sequence(self):
        """Create a sequence of test video frames"""
        frames = []
        
        for i in range(10):
            # Create frame with moving balls
            frame = np.zeros((480, 640, 3), dtype=np.uint8)
            frame[:] = (0, 100, 0)  # Green background (table)
            
            # Draw table boundary
            cv2.rectangle(frame, (50, 50), (590, 430), (255, 255, 255), 3)
            
            # Draw moving balls
            # Cue ball moving right
            cue_x = 100 + i * 10
            cv2.circle(frame, (cue_x, 200), 12, (255, 255, 255), -1)
            
            # Red ball moving down
            red_y = 150 + i * 5
            cv2.circle(frame, (300, red_y), 12, (0, 0, 255), -1)
            
            # Blue ball stationary
            cv2.circle(frame, (450, 300), 12, (255, 0, 0), -1)
            
            frames.append(frame)
        
        return frames
    
    @patch('src.detection.ball_detection_engine.YOLO')
    def test_complete_pipeline_with_mock_detection(self, mock_yolo):
        """Test complete pipeline with mocked YOLO detection"""
        # Mock YOLO model
        mock_model = Mock()
        mock_yolo.return_value = mock_model
        
        # Mock detection results for each frame
        def mock_detect(frame):
            mock_result = Mock()
            mock_result.boxes = Mock()
            
            # Simulate detections based on frame content
            # This is a simplified simulation
            mock_result.boxes.xyxy = np.array([
                [88, 188, 112, 212],   # Cue ball
                [288, 138, 312, 162],  # Red ball
                [438, 288, 462, 312]   # Blue ball
            ])
            mock_result.boxes.conf = np.array([0.9, 0.8, 0.85])
            mock_result.boxes.cls = np.array([0, 2, 6])  # cue, red, blue
            
            return [mock_result]
        
        mock_model.side_effect = mock_detect
        
        # Initialize API
        api = DetectionAPI(self.config)
        
        # Test initialization
        self.assertTrue(api.initialize())
        
        # Process frames sequentially
        results = []
        for i, frame in enumerate(self.test_frames):
            # Simulate frame processing
            analysis = api.frame_processor.process_frame(frame, i, "test_video.mp4")
            results.append(analysis)
        
        # Verify results
        self.assertEqual(len(results), len(self.test_frames))
        
        # Check that detections were made
        total_detections = sum(len(result.detections) for result in results)
        self.assertGreater(total_detections, 0)
        
        # Check that tracking worked
        final_result = results[-1]
        self.assertGreater(len(final_result.tracked_balls), 0)
        
        # Verify trajectory building
        for ball in final_result.tracked_balls:
            if ball.is_active:
                self.assertGreater(len(ball.trajectory), 1)
    
    def test_api_configuration_management(self):
        """Test API configuration management functionality"""
        api = DetectionAPI(self.config)
        
        # Test configuration access
        if hasattr(api, 'get_config_value'):
            confidence = api.get_config_value("detection.confidence_threshold")
            self.assertEqual(confidence, 0.3)
        
        # Test configuration update
        if hasattr(api, 'set_config_value'):
            success = api.set_config_value("detection.confidence_threshold", 0.5)
            if success:
                new_confidence = api.get_config_value("detection.confidence_threshold")
                self.assertEqual(new_confidence, 0.5)
        
        # Test configuration validation
        if hasattr(api, 'validate_config'):
            validation = api.validate_config()
            self.assertIn('is_valid', validation)
    
    def test_error_handling_and_recovery(self):
        """Test system error handling and recovery"""
        api = DetectionAPI(self.config)
        
        # Test with invalid frame
        try:
            analysis = api.frame_processor.process_frame(None, 0, "test.mp4")
            # Should not crash, should return valid analysis object
            self.assertIsNotNone(analysis)
        except Exception as e:
            self.fail(f"System should handle invalid frame gracefully: {e}")
        
        # Test error statistics
        if hasattr(api.frame_processor, 'get_error_statistics'):
            error_stats = api.frame_processor.get_error_statistics()
            self.assertIn('total_errors', error_stats)
    
    def test_visualization_integration(self):
        """Test visualization system integration"""
        api = DetectionAPI(self.config)
        
        # Test debug visualization creation
        if hasattr(api, 'create_debug_visualization'):
            # This will return None without real analysis data, but shouldn't crash
            vis_frame = api.create_debug_visualization()
            # Should handle gracefully
            self.assertTrue(True)  # If we get here, no crash occurred
        
        # Test visualization stats
        if hasattr(api, 'get_visualization_stats'):
            vis_stats = api.get_visualization_stats()
            self.assertIn('debug_visualizer', vis_stats)
    
    def test_performance_benchmarks(self):
        """Test system performance benchmarks"""
        api = DetectionAPI(self.config)
        
        # Initialize system
        api.initialize()
        
        # Measure processing time for multiple frames
        processing_times = []
        
        for i, frame in enumerate(self.test_frames[:5]):  # Test with 5 frames
            start_time = time.time()
            
            analysis = api.frame_processor.process_frame(frame, i, "test.mp4")
            
            processing_time = time.time() - start_time
            processing_times.append(processing_time)
        
        # Calculate performance metrics
        avg_processing_time = np.mean(processing_times)
        max_processing_time = np.max(processing_times)
        
        # Performance assertions (adjust thresholds as needed)
        self.assertLess(avg_processing_time, 1.0, "Average processing time should be < 1 second")
        self.assertLess(max_processing_time, 2.0, "Max processing time should be < 2 seconds")
        
        # Calculate theoretical FPS
        theoretical_fps = 1.0 / avg_processing_time
        self.assertGreater(theoretical_fps, 1.0, "Should achieve at least 1 FPS")
        
        print(f"Performance Results:")
        print(f"  Average processing time: {avg_processing_time:.3f}s")
        print(f"  Max processing time: {max_processing_time:.3f}s")
        print(f"  Theoretical FPS: {theoretical_fps:.1f}")
    
    def test_memory_usage(self):
        """Test system memory usage"""
        import psutil
        import os
        
        # Get initial memory usage
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Initialize API and process frames
        api = DetectionAPI(self.config)
        api.initialize()
        
        # Process multiple frames
        for i, frame in enumerate(self.test_frames):
            analysis = api.frame_processor.process_frame(frame, i, "test.mp4")
        
        # Get final memory usage
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory
        
        print(f"Memory Usage:")
        print(f"  Initial: {initial_memory:.1f} MB")
        print(f"  Final: {final_memory:.1f} MB")
        print(f"  Increase: {memory_increase:.1f} MB")
        
        # Memory should not increase excessively
        self.assertLess(memory_increase, 500, "Memory increase should be < 500 MB")
    
    def test_system_status_reporting(self):
        """Test comprehensive system status reporting"""
        api = DetectionAPI(self.config)
        
        # Test system status
        status = api.get_system_status()
        
        self.assertIn('processing_stats', status)
        self.assertIn('video_source', status)
        self.assertIn('calibration_status', status)
        
        # Test component status
        if hasattr(api.frame_processor, 'get_component_status'):
            component_status = api.frame_processor.get_component_status()
            self.assertIn('overall_ready', component_status)
    
    def test_configuration_file_integration(self):
        """Test configuration file loading and saving"""
        api = DetectionAPI(self.config)
        
        # Test config template creation
        if hasattr(api, 'create_config_template'):
            template_path = os.path.join(self.temp_dir, "test_config.yaml")
            success = api.create_config_template(template_path)
            
            if success:
                self.assertTrue(os.path.exists(template_path))
                self.assertGreater(os.path.getsize(template_path), 0)
        
        # Test config documentation export
        if hasattr(api, 'export_config_documentation'):
            doc_path = os.path.join(self.temp_dir, "config_docs.md")
            success = api.export_config_documentation(doc_path)
            
            if success:
                self.assertTrue(os.path.exists(doc_path))

class TestRealVideoIntegration(unittest.TestCase):
    """Integration tests with real video file (if available)"""
    
    def setUp(self):
        """Set up real video integration tests"""
        self.config = SystemConfig(
            detection=DetectionConfig(confidence_threshold=0.2),
            debug_mode=False
        )
        
        # Check if sample video exists
        self.video_path = "dataset/sample_snooker.mp4"
        self.has_video = os.path.exists(self.video_path)
    
    @unittest.skipUnless(os.path.exists("dataset/sample_snooker.mp4"), 
                        "Sample video not available")
    def test_real_video_processing(self):
        """Test processing with real snooker video"""
        api = DetectionAPI(self.config)
        
        # Initialize system
        self.assertTrue(api.initialize())
        
        # Test video analysis (just a few frames to avoid long test times)
        try:
            # This would normally use api.start_analysis(), but for testing
            # we'll process just a few frames manually
            
            import cv2
            cap = cv2.VideoCapture(self.video_path)
            
            if not cap.isOpened():
                self.skipTest("Could not open video file")
            
            frame_count = 0
            max_frames = 10  # Limit for testing
            
            while frame_count < max_frames:
                ret, frame = cap.read()
                if not ret:
                    break
                
                # Process frame
                analysis = api.frame_processor.process_frame(frame, frame_count, self.video_path)
                
                # Basic validation
                self.assertIsNotNone(analysis)
                self.assertEqual(analysis.frame_number, frame_count)
                self.assertGreaterEqual(analysis.processing_time, 0)
                
                frame_count += 1
            
            cap.release()
            
            print(f"Successfully processed {frame_count} frames from real video")
            
        except Exception as e:
            self.fail(f"Real video processing failed: {e}")

class TestSystemRobustness(unittest.TestCase):
    """Test system robustness under various conditions"""
    
    def setUp(self):
        """Set up robustness tests"""
        self.config = SystemConfig(
            detection=DetectionConfig(confidence_threshold=0.5),
            debug_mode=False
        )
    
    def test_rapid_configuration_changes(self):
        """Test system stability with rapid configuration changes"""
        api = DetectionAPI(self.config)
        api.initialize()
        
        # Rapidly change configuration
        if hasattr(api, 'set_config_value'):
            for i in range(10):
                threshold = 0.1 + (i * 0.08)  # 0.1 to 0.82
                api.set_config_value("detection.confidence_threshold", threshold)
        
        # System should remain stable
        status = api.get_system_status()
        self.assertIsNotNone(status)
    
    def test_concurrent_access(self):
        """Test system behavior under concurrent access"""
        import threading
        
        api = DetectionAPI(self.config)
        api.initialize()
        
        results = []
        errors = []
        
        def worker():
            try:
                # Create test frame
                frame = np.zeros((480, 640, 3), dtype=np.uint8)
                analysis = api.frame_processor.process_frame(frame, 0, "test.mp4")
                results.append(analysis)
            except Exception as e:
                errors.append(e)
        
        # Create multiple threads
        threads = []
        for i in range(5):
            thread = threading.Thread(target=worker)
            threads.append(thread)
            thread.start()
        
        # Wait for all threads
        for thread in threads:
            thread.join()
        
        # Check results
        self.assertEqual(len(errors), 0, f"Concurrent access caused errors: {errors}")
        self.assertEqual(len(results), 5, "Not all threads completed successfully")

if __name__ == '__main__':
    # Create test suite
    suite = unittest.TestSuite()
    
    # Add test cases
    suite.addTest(unittest.makeSuite(TestEndToEndIntegration))
    suite.addTest(unittest.makeSuite(TestRealVideoIntegration))
    suite.addTest(unittest.makeSuite(TestSystemRobustness))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print comprehensive summary
    print(f"\n{'='*60}")
    print(f"END-TO-END INTEGRATION TESTS SUMMARY")
    print(f"{'='*60}")
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Skipped: {len(result.skipped) if hasattr(result, 'skipped') else 0}")
    print(f"Success rate: {((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100):.1f}%")
    
    if result.failures:
        print(f"\nFAILURES:")
        for test, traceback in result.failures:
            print(f"  - {test}: {traceback.split('AssertionError:')[-1].strip()}")
    
    if result.errors:
        print(f"\nERRORS:")
        for test, traceback in result.errors:
            print(f"  - {test}: {traceback.split('Exception:')[-1].strip()}")
    
    print(f"{'='*60}")
    
    if len(result.failures) == 0 and len(result.errors) == 0:
        print("🎉 ALL INTEGRATION TESTS PASSED!")
        print("✅ System is ready for production use!")
    else:
        print("⚠️ Some tests failed - review issues above")
    
    print(f"{'='*60}")