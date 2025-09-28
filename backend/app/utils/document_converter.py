"""
Document conversion utilities for exporting reports
"""
import os
import tempfile
import uuid
import pypandoc
from docx import Document
from docx.shared import Inches, RGBColor
from datetime import datetime


class DocumentConverter:
    """Handles conversion of markdown reports to various formats"""
    
    @staticmethod
    def create_reference_doc() -> str:
        """Create a reference document with proper heading styles for Word conversion"""
        doc = Document()
        styles = doc.styles
        
        # Configure Heading 1 style
        heading1_style = styles['Heading 1']
        heading1_font = heading1_style.font
        heading1_font.name = 'Calibri'
        heading1_font.size = Inches(0.18)  # 14pt
        heading1_font.bold = True
        heading1_font.color.rgb = RGBColor(0x2F, 0x54, 0x96)  # Dark blue
        
        # Configure Heading 2 style (subsections)
        heading2_style = styles['Heading 2']
        heading2_font = heading2_style.font
        heading2_font.name = 'Calibri'
        heading2_font.size = Inches(0.16)  # 12pt
        heading2_font.bold = True
        heading2_font.color.rgb = RGBColor(0x44, 0x72, 0xC4)  # Blue color
        
        # Configure Heading 3 style
        heading3_style = styles['Heading 3']
        heading3_font = heading3_style.font
        heading3_font.name = 'Calibri'
        heading3_font.size = Inches(0.14)  # 11pt
        heading3_font.bold = True
        heading3_font.color.rgb = RGBColor(0x44, 0x72, 0xC4)  # Same blue color
        
        # Save to temp file
        temp_ref_path = os.path.join(tempfile.gettempdir(), f"reference_{uuid.uuid4().hex}.docx")
        doc.save(temp_ref_path)
        return temp_ref_path
    
    @staticmethod
    def markdown_to_docx(markdown_text: str, topic: str) -> str:
        """Convert markdown to Word document"""
        session_id = str(uuid.uuid4())
        
        # Create temporary files
        temp_md_path = os.path.join(tempfile.gettempdir(), f"temp_{session_id}.md")
        temp_docx_path = os.path.join(tempfile.gettempdir(), f"report_{session_id}.docx")
        
        # Save markdown to temp file
        with open(temp_md_path, 'w', encoding='utf-8') as f:
            f.write(markdown_text)
        
        # Create reference document for styling
        reference_doc_path = DocumentConverter.create_reference_doc()
        
        # Convert to Word with proper styling
        pypandoc.convert_file(
            temp_md_path,
            'docx',
            outputfile=temp_docx_path,
            extra_args=[
                f'--reference-doc={reference_doc_path}',
                '--toc',
                '--toc-depth=3'
            ]
        )
        
        # Clean up temporary files
        os.remove(temp_md_path)
        os.remove(reference_doc_path)
        
        return temp_docx_path
    
    @staticmethod
    def markdown_to_file(markdown_text: str) -> str:
        """Save markdown to temporary file"""
        session_id = str(uuid.uuid4())
        temp_md_path = os.path.join(tempfile.gettempdir(), f"report_{session_id}.md")
        
        with open(temp_md_path, 'w', encoding='utf-8') as f:
            f.write(markdown_text)
        
        return temp_md_path
    
    @staticmethod
    def generate_filename(topic: str, format: str) -> str:
        """Generate a safe filename for the report"""
        safe_topic = "".join(c for c in topic[:50] if c.isalnum() or c in (' ', '-', '_')).rstrip()
        timestamp = datetime.now().strftime('%Y%m%d')
        return f"Fizibilite_Raporu_{safe_topic}_{timestamp}.{format}"
