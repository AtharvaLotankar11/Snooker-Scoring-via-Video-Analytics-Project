"""
Snooker Ball Detection Web Application
A Flask-based web interface for the snooker detection system
"""

import os
import json
import time
from datetime import datetime
from flask import Flask, render_template, request, jsonify, send_file, flash, redirect, url_for, send_from_directory
from werkzeug.utils import secure_filename
import cv2
import numpy as np
from pathlib import Path

# Import our detection system
from src.api.detection_api import DetectionAPI
from src.config.config_manager import ConfigManager
from src.core.data_models import Point

app = Flask(__name__, static_url_path='/static', static_folder='static')
app.secret_key = 'snooker_detection_secret_key_2024'

# Add cache-busting filter and global
@app.template_filter('cache_bust')
def cache_bust_filter(filename):
    """Add cache-busting parameter to static files"""
    return f"{filename}?v={int(time.time())}"

@app.template_global()
def cache_version():
    """Provide a cache-busting version number"""
    return int(time.time())

# Configuration
UPLOAD_FOLDER = 'web_uploads'
RESULTS_FOLDER = 'web_results'
ALLOWED_EXTENSIONS = {'mp4', 'avi', 'mov', 'mkv', 'webm'}

# Ensure directories exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(RESULTS_FOLDER, exist_ok=True)
os.makedirs('static/css', exist_ok=True)
os.makedirs('static/js', exist_ok=True)
os.makedirs('templates', exist_ok=True)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['RESULTS_FOLDER'] = RESULTS_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024  # 500MB max file size

# Initialize detection system
config_manager = ConfigManager()
config = config_manager.get_system_config()  # Get SystemConfig object
detection_api = DetectionAPI(config)

@app.before_request
def before_request():
    """Ensure consistent behavior across different host access methods"""
    # Force consistent headers for all requests
    from flask import g
    g.host_consistent = True

@app.after_request
def after_request(response):
    """Ensure consistent response headers for all requests"""
    # Add CORS headers to prevent any cross-origin issues
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
    
    # Ensure consistent content delivery
    if request.endpoint and 'static' not in request.endpoint:
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
    
    return response

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    """Main dashboard page"""
    # Force browser to clear cache and reload everything fresh
    response = app.make_response(render_template('index.html'))
    
    # Strong cache-busting headers
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    response.headers['Last-Modified'] = datetime.now().strftime('%a, %d %b %Y %H:%M:%S GMT')
    response.headers['ETag'] = f'"{int(time.time())}"'
    
    return response

@app.route('/upload')
def upload_page():
    """Video upload page"""
    return render_template('upload.html')

@app.route('/team')
def team():
    """Team page"""
    return render_template('team.html')

@app.route('/analyze', methods=['POST'])
def analyze_video():
    """Handle video upload and analysis"""
    if 'video' not in request.files:
        flash('No video file selected')
        return redirect(request.url)
    
    file = request.files['video']
    if file.filename == '':
        flash('No video file selected')
        return redirect(request.url)
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{timestamp}_{filename}"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        # Start analysis
        try:
            results = process_video_analysis(filepath, filename)
            return render_template('results.html', 
                                 results=results, 
                                 video_filename=filename)
        except Exception as e:
            flash(f'Analysis failed: {str(e)}')
            return redirect(url_for('upload_page'))
    
    flash('Invalid file type. Please upload MP4, AVI, MOV, MKV, or WEBM files.')
    return redirect(url_for('upload_page'))

@app.route('/api/analyze', methods=['POST'])
def api_analyze():
    """API endpoint for video analysis"""
    if 'video' not in request.files:
        return jsonify({'error': 'No video file provided'}), 400
    
    file = request.files['video']
    if not allowed_file(file.filename):
        return jsonify({'error': 'Invalid file type'}), 400
    
    filename = secure_filename(file.filename)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{timestamp}_{filename}"
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(filepath)
    
    try:
        results = process_video_analysis(filepath, filename)
        return jsonify(results)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/status')
def api_status():
    """Get system status"""
    try:
        status = detection_api.get_system_status()
        return jsonify(status)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/health')
def health_check():
    """Health check endpoint to verify server is running correctly"""
    return jsonify({
        'status': 'healthy',
        'host': request.host,
        'url': request.url,
        'remote_addr': request.remote_addr,
        'timestamp': datetime.now().isoformat()
    })

@app.route('/debug')
def debug_info():
    """Debug endpoint to check request details"""
    return jsonify({
        'host': request.host,
        'url': request.url,
        'base_url': request.base_url,
        'url_root': request.url_root,
        'remote_addr': request.remote_addr,
        'user_agent': str(request.user_agent),
        'headers': dict(request.headers),
        'timestamp': datetime.now().isoformat()
    })

@app.route('/api/config')
def api_config():
    """Get current configuration"""
    try:
        config_dict = {
            'detection': {
                'confidence_threshold': config.detection.confidence_threshold,
                'model_path': config.detection.model_path
            },
            'tracking': {
                'max_disappeared_frames': config.tracking.max_disappeared_frames,
                'max_tracking_distance': config.tracking.max_tracking_distance
            },
            'calibration': {
                'table_length': config.calibration.table_length,
                'table_width': config.calibration.table_width,
                'auto_recalibrate': config.calibration.auto_recalibrate
            }
        }
        return jsonify(config_dict)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/results/<filename>')
def view_results(filename):
    """View analysis results for a specific video"""
    results_file = os.path.join(app.config['RESULTS_FOLDER'], f"{filename}_results.json")
    if os.path.exists(results_file):
        with open(results_file, 'r') as f:
            results = json.load(f)
        return render_template('results.html', results=results, video_filename=filename)
    else:
        flash('Results not found')
        return redirect(url_for('index'))

@app.route('/download/<filename>')
def download_results(filename):
    """Download analysis results as JSON"""
    results_file = os.path.join(app.config['RESULTS_FOLDER'], f"{filename}_results.json")
    if os.path.exists(results_file):
        return send_file(results_file, as_attachment=True)
    else:
        flash('Results file not found')
        return redirect(url_for('index'))

def process_video_analysis(video_path, filename):
    """Process video and return analysis results"""
    print(f"Starting analysis of {video_path}")
    
    # Initialize video capture
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise Exception("Could not open video file")
    
    # Get video properties
    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    duration = total_frames / fps if fps > 0 else 0
    
    # Initialize detection API
    if not detection_api.initialize():
        raise Exception("Failed to initialize detection system")
    
    # Process video
    results = {
        'video_info': {
            'filename': filename,
            'fps': fps,
            'total_frames': total_frames,
            'duration': duration,
            'analysis_timestamp': datetime.now().isoformat()
        },
        'detection_summary': {
            'total_detections': 0,
            'frames_processed': 0,
            'avg_balls_per_frame': 0,
            'processing_time': 0
        },
        'ball_statistics': {},
        'tracking_data': [],
        'calibration_info': {},
        'frame_analyses': []
    }
    
    start_time = time.time()
    frame_count = 0
    total_detections = 0
    
    # Process frames (sample every 5th frame for performance)
    frame_skip = max(1, total_frames // 100)  # Process max 100 frames
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        if frame_count % frame_skip == 0:
            try:
                # Process frame
                analysis = detection_api.frame_processor.process_frame(
                    frame, frame_count, video_path
                )
                
                # Convert analysis to serializable format
                frame_data = {
                    'frame_number': analysis.frame_number,
                    'timestamp': analysis.timestamp,
                    'detections_count': len(analysis.detections),
                    'tracked_balls_count': len(analysis.tracked_balls),
                    'processing_time': analysis.processing_time,
                    'detections': [
                        {
                            'bbox': {
                                'x1': det.bbox.x1, 'y1': det.bbox.y1,
                                'x2': det.bbox.x2, 'y2': det.bbox.y2
                            },
                            'class_id': det.class_id,
                            'confidence': det.confidence,
                            'ball_type': get_ball_type_name(det.class_id)
                        }
                        for det in analysis.detections
                    ],
                    'tracked_balls': [
                        {
                            'track_id': ball.track_id,
                            'ball_type': ball.ball_type,
                            'position': {'x': ball.current_position.x, 'y': ball.current_position.y},
                            'is_active': ball.is_active,
                            'trajectory_length': len(ball.trajectory)
                        }
                        for ball in analysis.tracked_balls
                    ]
                }
                
                results['frame_analyses'].append(frame_data)
                total_detections += len(analysis.detections)
                results['detection_summary']['frames_processed'] += 1
                
            except Exception as e:
                print(f"Error processing frame {frame_count}: {e}")
        
        frame_count += 1
        
        # Progress update (could be sent via websocket in real implementation)
        if frame_count % 100 == 0:
            print(f"Processed {frame_count}/{total_frames} frames")
    
    cap.release()
    
    # Finalize results
    processing_time = time.time() - start_time
    results['detection_summary']['total_detections'] = total_detections
    results['detection_summary']['processing_time'] = processing_time
    
    if results['detection_summary']['frames_processed'] > 0:
        results['detection_summary']['avg_balls_per_frame'] = (
            total_detections / results['detection_summary']['frames_processed']
        )
    
    # Calculate ball statistics
    ball_type_counts = {}
    for frame_analysis in results['frame_analyses']:
        for detection in frame_analysis['detections']:
            ball_type = detection['ball_type']
            ball_type_counts[ball_type] = ball_type_counts.get(ball_type, 0) + 1
    
    results['ball_statistics'] = ball_type_counts
    
    # Get calibration info
    if detection_api.frame_processor.calibration_engine.is_calibrated():
        calibration_data = detection_api.frame_processor.calibration_engine.get_calibration_data()
        results['calibration_info'] = {
            'is_calibrated': True,
            'table_corners': [
                {'x': corner.x, 'y': corner.y} 
                for corner in calibration_data.table_corners
            ] if calibration_data.table_corners else [],
            'table_dimensions': {
                'length': calibration_data.table_dimensions[0],
                'width': calibration_data.table_dimensions[1]
            }
        }
    else:
        results['calibration_info'] = {'is_calibrated': False}
    
    # Save results
    results_file = os.path.join(app.config['RESULTS_FOLDER'], f"{filename}_results.json")
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"Analysis complete. Processed {results['detection_summary']['frames_processed']} frames in {processing_time:.2f}s")
    
    return results

@app.route('/common_logo/<filename>')
def serve_logo(filename):
    """Serve logo files from common_logo directory"""
    return send_from_directory('common_logo', filename)

@app.route('/team-members/<filename>')
def serve_team_member_image(filename):
    """Serve team member images from team-members directory"""
    return send_from_directory('team-members', filename)

@app.route('/static/<path:filename>')
def serve_static(filename):
    """Explicitly serve static files to ensure consistency"""
    response = send_from_directory('static', filename)
    # Add appropriate headers for static files
    if filename.endswith('.css'):
        response.headers['Content-Type'] = 'text/css'
    elif filename.endswith('.js'):
        response.headers['Content-Type'] = 'application/javascript'
    return response

def get_ball_type_name(class_id):
    """Convert class ID to ball type name"""
    ball_types = {
        0: "Cue Ball",
        1: "Yellow",
        2: "Red",
        3: "Green", 
        4: "Brown",
        5: "Blue",
        6: "Pink",
        7: "Black"
    }
    return ball_types.get(class_id, f"Unknown ({class_id})")

if __name__ == '__main__':
    print("🎱 Starting Snooker Detection Web Application...")
    print("📊 System Status:", detection_api.get_system_status())
    print("🌐 Access the application at:")
    print("   • http://localhost:5000")
    print("   • http://127.0.0.1:5000")
    print("   • http://0.0.0.0:5000")
    app.run(debug=True, host='0.0.0.0', port=5000, threaded=True)