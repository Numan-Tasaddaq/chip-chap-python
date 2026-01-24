"""
Convert DEVELOPER_DOCUMENTATION.md to PDF using reportlab
"""
from reportlab.lib.pagesizes import A4, letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Preformatted
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY
from reportlab.lib.colors import HexColor
from pathlib import Path
import re

# Read markdown file
md_file = Path("DEVELOPER_DOCUMENTATION.md")
md_content = md_file.read_text(encoding='utf-8')

# Create PDF
output_file = Path("ChipCap_Developer_Documentation.pdf")
doc = SimpleDocTemplate(
    str(output_file),
    pagesize=A4,
    leftMargin=0.75*inch,
    rightMargin=0.75*inch,
    topMargin=1*inch,
    bottomMargin=0.75*inch
)

# Define styles
styles = getSampleStyleSheet()

# Custom styles
title_style = ParagraphStyle(
    'CustomTitle',
    parent=styles['Heading1'],
    fontSize=24,
    textColor=HexColor('#2c3e50'),
    spaceAfter=20,
    spaceBefore=20,
    alignment=TA_CENTER
)

heading1_style = ParagraphStyle(
    'CustomHeading1',
    parent=styles['Heading1'],
    fontSize=18,
    textColor=HexColor('#2c3e50'),
    spaceAfter=12,
    spaceBefore=16,
    borderColor=HexColor('#3498db'),
    borderWidth=2,
    borderPadding=6
)

heading2_style = ParagraphStyle(
    'CustomHeading2',
    parent=styles['Heading2'],
    fontSize=14,
    textColor=HexColor('#34495e'),
    spaceAfter=10,
    spaceBefore=12,
)

heading3_style = ParagraphStyle(
    'CustomHeading3',
    parent=styles['Heading3'],
    fontSize=12,
    textColor=HexColor('#555555'),
    spaceAfter=8,
    spaceBefore=10,
)

body_style = ParagraphStyle(
    'CustomBody',
    parent=styles['Normal'],
    fontSize=10,
    textColor=HexColor('#333333'),
    alignment=TA_JUSTIFY,
    spaceAfter=6,
)

code_style = ParagraphStyle(
    'CustomCode',
    parent=styles['Code'],
    fontSize=8,
    textColor=HexColor('#c7254e'),
    backColor=HexColor('#f4f4f4'),
    leftIndent=20,
    rightIndent=20,
)

bullet_style = ParagraphStyle(
    'CustomBullet',
    parent=styles['Normal'],
    fontSize=10,
    leftIndent=20,
    spaceAfter=4,
)

# Build story
story = []

# Parse markdown content
lines = md_content.split('\n')
i = 0
in_code_block = False
code_buffer = []

while i < len(lines):
    line = lines[i]
    
    # Code blocks
    if line.strip().startswith('```'):
        if in_code_block:
            # End code block
            code_text = '\n'.join(code_buffer)
            story.append(Preformatted(code_text, code_style))
            story.append(Spacer(1, 10))
            code_buffer = []
            in_code_block = False
        else:
            # Start code block
            in_code_block = True
        i += 1
        continue
    
    if in_code_block:
        code_buffer.append(line)
        i += 1
        continue
    
    # Skip empty lines
    if not line.strip():
        if story and not isinstance(story[-1], Spacer):
            story.append(Spacer(1, 6))
        i += 1
        continue
    
    # Page breaks
    if line.strip() == '---':
        story.append(PageBreak())
        i += 1
        continue
    
    # Headings
    if line.startswith('# '):
        text = line[2:].strip()
        # Remove markdown links
        text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)
        if i == 0:  # Title
            story.append(Paragraph(text, title_style))
        else:
            story.append(PageBreak())
            story.append(Paragraph(text, heading1_style))
        story.append(Spacer(1, 12))
    
    elif line.startswith('## '):
        text = line[3:].strip()
        text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)
        story.append(Paragraph(text, heading2_style))
        story.append(Spacer(1, 8))
    
    elif line.startswith('### '):
        text = line[4:].strip()
        text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)
        story.append(Paragraph(text, heading3_style))
        story.append(Spacer(1, 6))
    
    elif line.startswith('#### '):
        text = line[5:].strip()
        text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)
        story.append(Paragraph(f"<b>{text}</b>", body_style))
        story.append(Spacer(1, 4))
    
    # Bullet lists
    elif line.strip().startswith('- ') or line.strip().startswith('* '):
        text = line.strip()[2:].strip()
        # Convert markdown formatting
        text = re.sub(r'\*\*([^\*]+)\*\*', r'<b>\1</b>', text)  # Bold
        text = re.sub(r'`([^`]+)`', r'<font color="#c7254e" face="Courier">\1</font>', text)  # Code
        text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'<i>\1</i>', text)  # Links
        story.append(Paragraph(f"• {text}", bullet_style))
    
    # Numbered lists
    elif re.match(r'^\d+\. ', line.strip()):
        text = re.sub(r'^\d+\. ', '', line.strip())
        text = re.sub(r'\*\*([^\*]+)\*\*', r'<b>\1</b>', text)
        text = re.sub(r'`([^`]+)`', r'<font color="#c7254e" face="Courier">\1</font>', text)
        text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'<i>\1</i>', text)
        match = re.match(r'^(\d+)', line.strip())
        num = match.group(1) if match else '1'
        story.append(Paragraph(f"{num}. {text}", bullet_style))
    
    # Regular paragraphs
    else:
        text = line.strip()
        if text:
            # Convert markdown formatting
            text = re.sub(r'\*\*([^\*]+)\*\*', r'<b>\1</b>', text)  # Bold
            text = re.sub(r'`([^`]+)`', r'<font color="#c7254e" face="Courier">\1</font>', text)  # Inline code
            text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'<i>\1</i>', text)  # Links
            story.append(Paragraph(text, body_style))
    
    i += 1

# Build PDF
doc.build(story)

print(f"✅ PDF generated successfully: {output_file}")
print(f"📄 File size: {output_file.stat().st_size / 1024:.2f} KB")

