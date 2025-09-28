"""
Report data models and schemas
"""
from datetime import datetime
from typing import Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class ReportSession:
    """Represents a report generation session"""
    session_id: str
    topic: str
    status: str = "pending"  # pending, generating, completed, failed
    created_at: datetime = None
    completed_at: Optional[datetime] = None
    progress: int = 0
    current_step: str = ""
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()


@dataclass
class GeneratedReport:
    """Represents a completed report"""
    session_id: str
    topic: str
    report_markdown: str
    report_html: str
    citations: int
    generated_at: datetime
    length: int
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            'session_id': self.session_id,
            'topic': self.topic,
            'report_markdown': self.report_markdown,
            'report_html': self.report_html,
            'citations': self.citations,
            'generated_at': self.generated_at.isoformat(),
            'length': self.length
        }
