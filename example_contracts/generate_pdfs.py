"""
Generate PDF files from markdown templates for testing.

Requires: uv pip install markdown pdfkit or uv pip install reportlab
"""

import os
from pathlib import Path

try:
    from reportlab.lib.pagesizes import letter
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    HAS_REPORTLAB = True
except ImportError:
    HAS_REPORTLAB = False
    print("Warning: reportlab not installed. Install with: uv pip install reportlab")

def markdown_to_pdf_reportlab(md_file: Path, pdf_file: Path):
    """Convert markdown to PDF using reportlab."""
    # Read markdown
    with open(md_file, 'r') as f:
        content = f.read()
    
    # Create PDF
    doc = SimpleDocTemplate(str(pdf_file), pagesize=letter)
    styles = getSampleStyleSheet()
    story = []
    
    # Parse markdown (simple conversion)
    for line in content.split('\n'):
        if line.startswith('# '):
            # Title
            style = ParagraphStyle('Title', parent=styles['Heading1'], fontSize=24)
            story.append(Paragraph(line[2:], style))
            story.append(Spacer(1, 0.2*inch))
        elif line.startswith('## '):
            # Heading
            story.append(Spacer(1, 0.1*inch))
            story.append(Paragraph(line[3:], styles['Heading2']))
            story.append(Spacer(1, 0.1*inch))
        elif line.startswith('###'):
            # Subheading
            story.append(Paragraph(line[4:], styles['Heading3']))
        elif line.strip():
            # Normal text
            story.append(Paragraph(line, styles['Normal']))
            story.append(Spacer(1, 0.05*inch))
    
    doc.build(story)
    print(f"✓ Generated: {pdf_file.name}")

def main():
    """Generate PDFs from markdown templates."""
    script_dir = Path(__file__).parent
    
    if not HAS_REPORTLAB:
        print("\nPlease install reportlab to generate PDFs:")
        print("  uv pip install reportlab")
        print("\nAlternatively, use online tools to convert the *_template.md files to PDF.")
        return
    
    templates = list(script_dir.glob('*_template.md'))
    
    if not templates:
        print("No template files found")
        return
    
    print(f"\nGenerating {len(templates)} PDF files...\n")
    
    for template in templates:
        pdf_name = template.stem.replace('_template', '') + '.pdf'
        pdf_file = script_dir / pdf_name
        
        try:
            markdown_to_pdf_reportlab(template, pdf_file)
        except Exception as e:
            print(f"✗ Error generating {pdf_name}: {e}")
    
    print("\n✓ PDF generation complete!")

if __name__ == "__main__":
    main()
