"""
Report generation service
"""
import asyncio
import threading
import uuid
from datetime import datetime
from typing import Dict, Optional
import markdown

from ..models.report import ReportSession, GeneratedReport
from ..utils.progress_tracker import ProgressTracker


class ReportService:
    """Service for managing report generation"""
    
    def __init__(self, socketio):
        self.socketio = socketio
        self.active_sessions: Dict[str, GeneratedReport] = {}
        self.session_status: Dict[str, ReportSession] = {}
    
    def create_session(self, topic: str) -> str:
        """Create a new report generation session"""
        session_id = str(uuid.uuid4())
        session = ReportSession(session_id=session_id, topic=topic)
        self.session_status[session_id] = session
        return session_id
    
    def get_session(self, session_id: str) -> Optional[ReportSession]:
        """Get session by ID"""
        return self.session_status.get(session_id)
    
    def get_report(self, session_id: str) -> Optional[GeneratedReport]:
        """Get completed report by session ID"""
        return self.active_sessions.get(session_id)
    
    def start_generation(self, session_id: str) -> bool:
        """Start report generation in background thread"""
        session = self.get_session(session_id)
        if not session:
            return False
        
        session.status = "generating"
        progress_tracker = ProgressTracker(session_id, self.socketio)
        
        # Start generation in background thread
        thread = threading.Thread(
            target=self._run_async_task,
            args=(session.topic, session_id, progress_tracker)
        )
        thread.daemon = True
        thread.start()
        return True
    
    def _run_async_task(self, topic: str, session_id: str, progress_tracker: ProgressTracker):
        """Run the async report generation in a separate thread"""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(
                self._generate_report_async(topic, session_id, progress_tracker)
            )
        finally:
            loop.close()
    
    async def _generate_report_async(self, topic: str, session_id: str, progress_tracker: ProgressTracker):
        """Generate report asynchronously with progress updates"""
        try:
            # Import here to avoid circular imports
            from ..open_deep_research.improved_report_generator import enhanced_app, ReportState
            
            initial_state = ReportState(topic=topic)
            config = {"recursion_limit": 50}
            
            # Track progress through each step
            final_state_generator = enhanced_app.astream(initial_state, config=config)
            
            final_state = None
            step_count = 0
            async for state_update in final_state_generator:
                final_state = list(state_update.values())[0]
                progress_tracker.update_progress(f"Step {step_count + 1}")
                step_count += 1
            
            # Final progress update
            self.socketio.emit('progress_update', {
                'progress': 100,
                'step': 'Rapor tamamlandı!',
                'step_number': progress_tracker.total_steps,
                'total_steps': progress_tracker.total_steps,
                'completed': True
            }, room=session_id)
            
            # Store the generated report
            report_text = final_state.get('report_text', "Rapor oluşturulamadı.")
            citations_count = len(final_state.get('citations', {}))
            
            report = GeneratedReport(
                session_id=session_id,
                topic=topic,
                report_markdown=report_text,
                report_html=markdown.markdown(report_text, extensions=['tables', 'fenced_code']),
                citations=citations_count,
                generated_at=datetime.now(),
                length=len(report_text)
            )
            
            self.active_sessions[session_id] = report
            
            # Update session status
            if session_id in self.session_status:
                self.session_status[session_id].status = "completed"
                self.session_status[session_id].progress = 100
            
            # Emit completion
            self.socketio.emit('report_complete', {
                'message': 'Rapor başarıyla oluşturuldu!',
                'citations': citations_count,
                'length': len(report_text)
            }, room=session_id)
            
        except Exception as e:
            # Update session status
            if session_id in self.session_status:
                self.session_status[session_id].status = "failed"
            
            self.socketio.emit('error', {
                'message': f'Rapor oluşturulurken hata oluştu: {str(e)}'
            }, room=session_id)
