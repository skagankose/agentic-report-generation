"""
API routes for the report generation application
"""
import os
from flask import Blueprint, render_template, request, jsonify, send_file, session
from flask_socketio import emit

from ..services.report_service import ReportService
from ..utils.document_converter import DocumentConverter
from ..core.config import settings

# Create blueprint
api_bp = Blueprint('api', __name__)

# Global report service instance (will be initialized in create_app)
report_service: ReportService = None


def init_routes(socketio, service: ReportService):
    """Initialize routes with dependencies"""
    global report_service
    report_service = service
    
    @socketio.on('connect')
    def handle_connect():
        print(f'Client connected: {request.sid}')

    @socketio.on('disconnect')
    def handle_disconnect():
        print(f'Client disconnected: {request.sid}')

    @socketio.on('join_session')
    def handle_join_session(data):
        session_id = data.get('session_id')
        if session_id:
            session['room'] = session_id
            print(f'Client {request.sid} joined session {session_id}')


@api_bp.route('/')
def index():
    """Main page with TODO list"""
    todo_list = []
    todo_file_path = 'docs/TODO.txt'
    
    if os.path.exists(todo_file_path):
        with open(todo_file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            # Clean up lines: strip whitespace and remove leading '- '
            for line in lines:
                clean_line = line.strip()
                if clean_line.startswith('- '):
                    clean_line = clean_line[2:].strip()
                elif clean_line.startswith('-'):
                    clean_line = clean_line[1:].strip()
                
                if clean_line:
                    todo_list.append(clean_line)
                    
    return render_template('index.html', todo_list=todo_list)


@api_bp.route('/generate', methods=['POST'])
def generate_report():
    """Start report generation"""
    data = request.get_json()
    topic = data.get('topic', '').strip()
    
    if not topic:
        return jsonify({'error': 'Lütfen bir konu giriniz.'}), 400
    
    # Check API keys
    if not settings.has_llm_key:
        return jsonify({'error': 'LLM API anahtarı yapılandırılmamış.'}), 500
    
    if not settings.has_search_key:
        return jsonify({'error': 'Arama API anahtarı yapılandırılmamış.'}), 500
    
    # Create session and start generation
    session_id = report_service.create_session(topic)
    session['current_session'] = session_id
    
    if report_service.start_generation(session_id):
        return jsonify({
            'session_id': session_id,
            'message': 'Rapor oluşturma süreci başlatıldı...'
        })
    else:
        return jsonify({'error': 'Rapor oluşturma başlatılamadı.'}), 500


@api_bp.route('/report/<session_id>')
def view_report(session_id):
    """View generated report"""
    report = report_service.get_report(session_id)
    if not report:
        return "Rapor bulunamadı.", 404
    
    return render_template('report.html', 
                         report_html=report.report_html,
                         topic=report.topic,
                         generated_at=report.generated_at,
                         citations=report.citations,
                         session_id=session_id)


@api_bp.route('/download/<session_id>/<format>')
def download_report(session_id, format):
    """Download report in specified format"""
    report = report_service.get_report(session_id)
    if not report:
        return "Rapor bulunamadı.", 404
    
    try:
        if format == 'docx':
            temp_docx_path = DocumentConverter.markdown_to_docx(
                report.report_markdown, 
                report.topic
            )
            filename = DocumentConverter.generate_filename(report.topic, 'docx')
            
            return send_file(temp_docx_path, 
                           as_attachment=True, 
                           download_name=filename,
                           mimetype='application/vnd.openxmlformats-officedocument.wordprocessingml.document')
        
        elif format == 'md':
            temp_md_path = DocumentConverter.markdown_to_file(report.report_markdown)
            filename = DocumentConverter.generate_filename(report.topic, 'md')
            
            return send_file(temp_md_path,
                           as_attachment=True,
                           download_name=filename,
                           mimetype='text/markdown')
        
        else:
            return "Desteklenmeyen format.", 400
            
    except Exception as e:
        return f"Dosya oluşturulurken hata oluştu: {str(e)}", 500


@api_bp.route('/status/<session_id>')
def get_status(session_id):
    """Get session status"""
    session_obj = report_service.get_session(session_id)
    if not session_obj:
        return jsonify({'error': 'Session not found'}), 404
    
    return jsonify({
        'session_id': session_obj.session_id,
        'status': session_obj.status,
        'progress': session_obj.progress,
        'current_step': session_obj.current_step,
        'topic': session_obj.topic
    })
