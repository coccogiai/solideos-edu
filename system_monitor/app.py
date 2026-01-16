"""
시스템 리소스 실시간 모니터링 서버
Flask + SocketIO를 사용한 실시간 웹 대시보드
"""

import os
import time
import threading
from datetime import datetime
from flask import Flask, render_template, jsonify, send_file, request
from flask_socketio import SocketIO, emit

from monitor import SystemMonitor
from pdf_generator import PDFReportGenerator

# Flask 앱 초기화
app = Flask(__name__)
app.config['SECRET_KEY'] = 'system-monitor-secret-key'
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# 시스템 모니터 인스턴스
monitor = SystemMonitor()

# 추적 데이터 저장
tracking_data = []
is_tracking = False
tracking_start_time = None
tracking_duration = 300  # 5분 = 300초


@app.route('/')
def index():
    """메인 대시보드 페이지"""
    return render_template('index.html')


@app.route('/api/stats')
def get_stats():
    """현재 시스템 상태 API"""
    return jsonify(monitor.get_all_stats())


@app.route('/api/start-tracking', methods=['POST'])
def start_tracking():
    """5분 추적 시작"""
    global is_tracking, tracking_data, tracking_start_time
    
    if is_tracking:
        return jsonify({"status": "error", "message": "이미 추적 중입니다."})
    
    tracking_data = []
    is_tracking = True
    tracking_start_time = time.time()
    
    return jsonify({
        "status": "started",
        "message": "5분(300초) 추적을 시작합니다.",
        "duration": tracking_duration
    })


@app.route('/api/stop-tracking', methods=['POST'])
def stop_tracking():
    """추적 중지"""
    global is_tracking
    
    is_tracking = False
    
    return jsonify({
        "status": "stopped",
        "message": "추적이 중지되었습니다.",
        "data_points": len(tracking_data)
    })


@app.route('/api/tracking-status')
def tracking_status():
    """추적 상태 확인"""
    global is_tracking, tracking_start_time
    
    if is_tracking and tracking_start_time:
        elapsed = time.time() - tracking_start_time
        remaining = max(0, tracking_duration - elapsed)
        progress = min(100, (elapsed / tracking_duration) * 100)
    else:
        elapsed = 0
        remaining = 0
        progress = 0
    
    return jsonify({
        "is_tracking": is_tracking,
        "elapsed_seconds": int(elapsed),
        "remaining_seconds": int(remaining),
        "progress_percent": round(progress, 1),
        "data_points": len(tracking_data)
    })


@app.route('/api/generate-pdf', methods=['POST'])
def generate_pdf():
    """PDF 리포트 생성"""
    global tracking_data
    
    if len(tracking_data) < 10:
        return jsonify({
            "status": "error",
            "message": f"데이터가 부족합니다. (현재: {len(tracking_data)}개, 최소: 10개 필요)"
        })
    
    # PDF 파일 경로
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    pdf_filename = f"system_report_{timestamp}.pdf"
    pdf_path = os.path.join(os.path.dirname(__file__), pdf_filename)
    
    try:
        generator = PDFReportGenerator(tracking_data, pdf_path)
        generator.generate()
        
        return jsonify({
            "status": "success",
            "message": "PDF 리포트가 생성되었습니다.",
            "filename": pdf_filename,
            "data_points": len(tracking_data)
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"PDF 생성 실패: {str(e)}"
        })


@app.route('/api/download-pdf/<filename>')
def download_pdf(filename):
    """PDF 파일 다운로드"""
    pdf_path = os.path.join(os.path.dirname(__file__), filename)
    
    if os.path.exists(pdf_path):
        return send_file(pdf_path, as_attachment=True)
    else:
        return jsonify({"status": "error", "message": "파일을 찾을 수 없습니다."}), 404


# SocketIO 이벤트
@socketio.on('connect')
def handle_connect():
    """클라이언트 연결"""
    print(f"Client connected: {request.sid}")
    emit('connected', {'message': 'Connected to server'})


@socketio.on('disconnect')
def handle_disconnect():
    """클라이언트 연결 해제"""
    print(f"Client disconnected: {request.sid}")


def background_monitor():
    """백그라운드에서 시스템 모니터링"""
    global is_tracking, tracking_data, tracking_start_time
    
    while True:
        try:
            stats = monitor.get_all_stats()
            
            # 추적 중이면 데이터 저장
            if is_tracking:
                tracking_data.append(stats)
                
                # 5분 경과 확인
                if tracking_start_time and (time.time() - tracking_start_time) >= tracking_duration:
                    is_tracking = False
                    socketio.emit('tracking_complete', {
                        'message': '5분 추적이 완료되었습니다.',
                        'data_points': len(tracking_data)
                    })
            
            # 추적 상태 정보 추가
            stats['tracking'] = {
                'is_tracking': is_tracking,
                'data_points': len(tracking_data),
                'progress': min(100, (len(tracking_data) / tracking_duration) * 100) if is_tracking else 0
            }
            
            # 모든 클라이언트에 데이터 전송
            socketio.emit('stats_update', stats)
            
        except Exception as e:
            print(f"Monitor error: {e}")
        
        time.sleep(1)  # 1초마다 업데이트


if __name__ == '__main__':
    print("=" * 60)
    print("  시스템 리소스 실시간 모니터링 시스템")
    print("  System Resource Real-time Monitoring System")
    print("=" * 60)
    print()
    print("  서버 시작 중...")
    print("  브라우저에서 http://localhost:5000 으로 접속하세요.")
    print()
    print("=" * 60)
    
    # 백그라운드 모니터링 스레드 시작
    monitor_thread = threading.Thread(target=background_monitor, daemon=True)
    monitor_thread.start()
    
    # Flask 서버 시작
    socketio.run(app, host='0.0.0.0', port=5000, debug=False, allow_unsafe_werkzeug=True)
