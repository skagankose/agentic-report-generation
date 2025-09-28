"""
Progress tracking utility for report generation
"""


class ProgressTracker:
    """Tracks and emits progress updates during report generation"""
    
    def __init__(self, session_id: str, socketio):
        self.session_id = session_id
        self.socketio = socketio
        self.current_step = 0
        self.total_steps = 8
        self.steps = [
            "Genel bölüm hazırlanıyor...",
            "Teknik analiz yapılıyor...",
            "Pazar analizi gerçekleştiriliyor...",
            "Maliyet analizi hesaplanıyor...",
            "Finansal analiz yapılıyor...",
            "Risk analizi değerlendiriliyor...",
            "Sonuçlar derleniyor...",
            "Rapor formatlanıyor..."
        ]
    
    def update_progress(self, step_name: str):
        """Update progress and emit to client"""
        if self.current_step < len(self.steps):
            progress = int((self.current_step / self.total_steps) * 100)
            self.socketio.emit('progress_update', {
                'progress': progress,
                'step': self.steps[self.current_step],
                'step_number': self.current_step + 1,
                'total_steps': self.total_steps
            }, room=self.session_id)
            self.current_step += 1
