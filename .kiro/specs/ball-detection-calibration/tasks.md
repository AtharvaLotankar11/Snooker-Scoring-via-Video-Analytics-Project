# Implementation Plan

- [x] 1. Set up core data structures and interfaces

  - Create data models for Point, BoundingBox, Detection, TrackedBall, and CalibrationData classes
  - Implement configuration dataclasses for DetectionConfig, TrackingConfig, and CalibrationConfig
  - Define base interfaces and abstract classes for detection and tracking components
  - _Requirements: 4.1, 4.2, 4.3_

- [x] 2. Implement Ball Detection Engine


  - [x] 2.1 Create BallDetectionEngine class with YOLO integration

    - Implement model loading with fallback to pre-trained YOLOv8
    - Add detection method that processes frames and returns Detection objects
    - Integrate with existing BALL_CLASSES configuration from config.py
    - _Requirements: 1.1, 1.2, 1.3, 1.4_

  - [x] 2.2 Add confidence-based filtering and validation

    - Implement confidence threshold filtering for detections
    - Add detection validation logic for ball classification accuracy
    - Create detection result formatting for API consumption
    - _Requirements: 1.5, 4.4_

  - [x]\* 2.3 Write unit tests for ball detection


    - Create test cases for detection accuracy with synthetic images
    - Test confidence threshold behavior and classification correctness
    - Validate detection consistency across different lighting conditions
    - _Requirements: 1.1, 1.2, 1.5_

- [x] 3. Implement Table Calibration Engine


  - [x] 3.1 Create TableCalibrationEngine with corner detection

    - Implement Canny edge detection and Hough line transform for table boundary detection
    - Add corner detection logic using line intersections
    - Create table geometry validation methods
    - _Requirements: 2.1, 2.2_

  - [x] 3.2 Add homography calculation and coordinate transformation

    - Implement homography matrix calculation from detected corners
    - Create CoordinateTransformer class for pixel-to-table coordinate conversion
    - Add calibration validation using known table dimensions
    - _Requirements: 2.3, 2.4_

  - [x] 3.3 Implement calibration persistence and recovery

    - Add calibration data caching and persistence mechanisms
    - Implement automatic recalibration when camera angle changes
    - Create fallback logic using previous calibration data
    - _Requirements: 2.4, 2.5_

  - [x]\* 3.4 Write unit tests for calibration engine


    - Test corner detection accuracy with synthetic table images
    - Validate homography calculation precision and coordinate transformation
    - Test calibration recovery and persistence mechanisms
    - _Requirements: 2.1, 2.2, 2.3_

- [x] 4. Implement Ball Tracking System


  - [x] 4.1 Create BallTracker class with multi-object tracking

    - Implement Hungarian algorithm for detection-to-track association
    - Add Kalman filter for ball position prediction and tracking
    - Create track management for creation, update, and deletion
    - _Requirements: 3.1, 3.2, 3.3_

  - [x] 4.2 Add trajectory management and ball state tracking

    - Implement trajectory storage and analysis for each tracked ball
    - Add ball potting detection when balls disappear near pocket regions
    - Create track recovery mechanisms for temporarily lost balls
    - _Requirements: 3.4, 3.5_

  - [x]\* 4.3 Write unit tests for tracking system


    - Test track association accuracy with simulated ball movements
    - Validate trajectory prediction and track recovery after occlusion
    - Test ball potting detection and track management
    - _Requirements: 3.1, 3.2, 3.3, 3.4_

- [x] 5. Create integrated frame processing pipeline


  - [x] 5.1 Implement FrameProcessor class

    - Create main processing pipeline that coordinates detection, calibration, and tracking
    - Add frame-by-frame analysis with timestamp management
    - Implement processing result aggregation and formatting
    - _Requirements: 4.1, 4.2, 4.3, 5.1, 5.2_

  - [x] 5.2 Add video input handling for live and recorded sources

    - Implement VideoInputHandler for different video source types (files, streams)
    - Add frame rate management and processing optimization
    - Create input validation and error handling for video sources
    - _Requirements: 5.1, 5.2, 5.3_

  - [x] 5.3 Integrate error handling and recovery mechanisms

    - Add comprehensive error handling for detection, calibration, and tracking failures
    - Implement graceful degradation when components fail
    - Create diagnostic logging and error reporting
    - _Requirements: 5.4, 5.5_

- [x] 6. Implement Detection API and interfaces


  - [x] 6.1 Create DetectionAPI class for external integration

    - Implement standardized API methods for accessing detection results
    - Add real-time result streaming and batch processing capabilities
    - Create result formatting for both pixel and table coordinates
    - _Requirements: 4.1, 4.2, 4.3, 4.4_

  - [x] 6.2 Add debugging and visualization capabilities

    - Implement debug mode with detection overlay visualization
    - Add calibration visualization showing table corners and boundaries
    - Create trajectory visualization and tracking ID display
    - _Requirements: 6.1, 6.2, 6.3, 6.4_

  - [x] 6.3 Create configuration management system


    - Implement configuration loading and validation from config files
    - Add runtime configuration updates and parameter tuning
    - Create configuration export and import functionality
    - _Requirements: 4.5, 6.5_

- [x] 7. Integration with existing codebase



  - [x] 7.1 Refactor existing SnookerAnalyzer to use new detection system

    - Update snooker_analyzer.py to integrate with new BallDetectionEngine
    - Replace existing detection logic with new modular components
    - Maintain backward compatibility with existing analysis features
    - _Requirements: 1.1, 1.2, 4.1_

  - [x] 7.2 Update configuration and model management

    - Integrate new configuration classes with existing config.py
    - Update model loading to use new BallDetectionEngine
    - Add configuration validation and migration support
    - _Requirements: 4.2, 4.3_

  - [x] 7.3 Enhance existing analysis and reporting features

    - Update trajectory plotting to use new tracking data structures
    - Enhance potting detection using new calibration and tracking systems
    - Improve analysis reporting with new coordinate transformation capabilities
    - _Requirements: 3.4, 4.1, 6.5_

- [x]\* 8. End-to-end integration testing



  - Create comprehensive integration tests using existing sample video
  - Test complete pipeline from video input to detection results
  - Validate performance benchmarks for real-time processing requirements
  - _Requirements: 5.1, 5.2, 5.3_
