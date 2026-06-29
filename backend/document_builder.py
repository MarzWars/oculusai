import os
import uuid
import logging
from docx import Document
from docx.shared import Pt, RGBColor
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet

def _execute_generate_proposal(user_id: str, workspace_id: str, args: dict) -> str:
    import os
    from docx import Document
    from docx.shared import Inches, Pt, RGBColor
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    
    client_name = args.get("client_name", "Unknown_Client").replace("/", "_").replace("\\", "_").replace(" ", "_")
    proposal_title = args.get("proposal_title", "Proposal").replace("/", "_").replace("\\", "_").replace(" ", "_")
    amount = args.get("amount") or "TBD"
    details = args.get("details") or "Details to be finalized."

    # Use AI's full drafted content if available (richer than user's brief input)
    ai_draft = (args.get("ai_draft") or "").strip()
    # Use ai_draft as body if it's meaningfully longer than 'details'
    body_content = ai_draft if len(ai_draft) > len(details) + 50 else details
    
    doc = Document()
    
    # Elegant Color Palette
    PRIMARY_COLOR = RGBColor(41, 128, 185)   # Elegant Blue
    TEXT_COLOR = RGBColor(44, 62, 80)        # Dark Charcoal
    MUTED_COLOR = RGBColor(127, 140, 141)    # Gray
    
    # Title
    p_title = doc.add_paragraph()
    p_title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run_title = p_title.add_run(proposal_title.upper())
    run_title.font.name = "Arial"
    run_title.font.size = Pt(22)
    run_title.font.bold = True
    run_title.font.color.rgb = PRIMARY_COLOR
    
    # Prepared for metadata
    p_meta = doc.add_paragraph()
    p_meta.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run_meta = p_meta.add_run(f"Project Proposal & Scope of Work\n\nPrepared For: {client_name}\nDate: {datetime.now().strftime('%d %B %Y')}")
    run_meta.font.name = "Arial"
    run_meta.font.size = Pt(11)
    run_meta.font.italic = True
    run_meta.font.color.rgb = TEXT_COLOR
    
    doc.add_paragraph("\n") # Spacer
    
    # Section 1: Introduction
    p_s1 = doc.add_paragraph()
    run_s1 = p_s1.add_run("1. Executive Summary")
    run_s1.font.name = "Arial"
    run_s1.font.size = Pt(14)
    run_s1.font.bold = True
    run_s1.font.color.rgb = PRIMARY_COLOR
    
    p_intro = doc.add_paragraph(
        f"This project proposal has been generated dynamically by Oculus AI for {client_name}. "
        "The purpose of this document is to define the scope of deliverables, client requirements, "
        "and pricing breakdown for this engagement."
    )
    p_intro.style.font.name = "Arial"
    p_intro.style.font.size = Pt(11)
    
    # Section 2: Details/Scope
    p_s2 = doc.add_paragraph()
    run_s2 = p_s2.add_run("2. Proposed Scope & Description")
    run_s2.font.name = "Arial"
    run_s2.font.size = Pt(14)
    run_s2.font.bold = True
    run_s2.font.color.rgb = PRIMARY_COLOR
    
    # Render body_content line-by-line into the DOCX preserving structure
    # Handles ## headings, - bullet points, **bold**, and regular paragraphs
    import re as _re
    for raw_line in body_content.split("\n"):
        line = raw_line.rstrip()
        if not line:
            doc.add_paragraph("")  # blank spacer
            continue

        # Section heading: ## Heading or # Heading
        heading_match = _re.match(r"^#{1,3}\s+(.+)", line)
        if heading_match:
            p_h = doc.add_paragraph()
            run_h = p_h.add_run(heading_match.group(1))
            run_h.font.name = "Arial"
            run_h.font.size = Pt(13)
            run_h.font.bold = True
            run_h.font.color.rgb = PRIMARY_COLOR
            continue

        # Bullet point: - item or * item
        bullet_match = _re.match(r"^[-*]\s+(.+)", line)
        if bullet_match:
            p_b = doc.add_paragraph(style="List Bullet")
            run_b = p_b.add_run(bullet_match.group(1))
            run_b.font.name = "Arial"
            run_b.font.size = Pt(11)
            continue

        # Regular paragraph — strip **bold** markers for DOCX bold runs
        p_body = doc.add_paragraph()
        p_body.style.font.name = "Arial"
        p_body.style.font.size = Pt(11)
        # Split on **...** for bold rendering
        parts = _re.split(r"\*\*(.+?)\*\*", line)
        for i, part in enumerate(parts):
            if not part:
                continue
            run = p_body.add_run(part)
            run.font.name = "Arial"
            run.font.size = Pt(11)
            if i % 2 == 1:  # odd parts are bold (between **)
                run.font.bold = True
    
    # Section 3: Investment
    p_s3 = doc.add_paragraph()
    run_s3 = p_s3.add_run("3. Investment & Pricing")
    run_s3.font.name = "Arial"
    run_s3.font.size = Pt(14)
    run_s3.font.bold = True
    run_s3.font.color.rgb = PRIMARY_COLOR
    
    # Investment Table
    table = doc.add_table(rows=2, cols=2)
    table.style = 'Light Shading Accent 1'
    
    hdr_cells = table.rows[0].cells
    hdr_cells[0].text = 'Deliverables & Description'
    hdr_cells[1].text = 'Estimated Cost'
    
    row_cells = table.rows[1].cells
    row_cells[0].text = f"Development & Delivery of: {proposal_title}"
    row_cells[1].text = amount
    
    doc.add_paragraph("\n") # Spacer
    
    # Legal / SLA Footer Notes
    p_footer = doc.add_paragraph()
    run_foot = p_footer.add_run("Disclaimer: This document is a draft proposal. It is subject to formal contract signing and SLA approval.")
    run_foot.font.name = "Arial"
    run_foot.font.size = Pt(9)
    run_foot.font.italic = True
    run_foot.font.color.rgb = MUTED_COLOR
    
    # Directory setup and save locally first
    sandbox_dir = os.path.join("workspaces", workspace_id, "proposals")
    os.makedirs(sandbox_dir, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    file_name = f"proposal_{client_name}_{timestamp}.docx"
    file_path = os.path.join(sandbox_dir, file_name)
    
    doc.save(file_path)
    
    # Upload to Supabase Storage → permanent signed URL
    from backend.docs import upload_to_storage, register_generated_doc, update_memory_after_doc
    storage_sub = f"proposals/{file_name}"
    download_url = upload_to_storage(workspace_id, file_path, storage_sub)

    # Graceful fallback: if Storage upload failed, use local route
    if not download_url:
        download_url = f"/api/sandbox/download?path=proposals/{file_name}"
        print(f"[Actions] Proposal Storage upload failed — using local fallback URL")

    full_storage_path = f"{workspace_id}/{storage_sub}"
    register_generated_doc(
        user_id=user_id,
        workspace_id=workspace_id,
        action_id="",
        doc_type="proposal",
        filename=file_name,
        title=proposal_title.replace("_", " "),
        description=f"Proposal for {client_name.replace('_', ' ')}: {details[:120]}",
        fmt="docx",
        storage_path=full_storage_path,
        download_url=download_url,
        file_size=os.path.getsize(file_path),
    )

    # Update memory in background
    threading.Thread(
        target=update_memory_after_doc,
        args=(user_id, "proposal", proposal_title.replace("_", " "), client_name.replace("_", " "))
    ).start()

    client_display = client_name.replace("_", " ")
    return f"Proposal generated for **{client_display}** — [⬇ Download Proposal DOCX]({download_url})"


def _generate_pdf_reportlab(file_path: str, title: str, content: str):
    from reportlab.lib.pagesizes import letter
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.enums import TA_CENTER
    
    doc = SimpleDocTemplate(file_path, pagesize=letter, rightMargin=72, leftMargin=72, topMargin=72, bottomMargin=72)
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=22,
        leading=26,
        textColor='#1a202c', # Slate 800
        alignment=TA_CENTER,
        spaceAfter=20
    )
    body_style = ParagraphStyle(
        'DocBody',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10.5,
        leading=15,
        textColor='#2d3748', # Slate 700
        spaceAfter=10
    )
    
    story = []
    story.append(Paragraph(title, title_style))
    story.append(Spacer(1, 10))
    
    for line in content.split('\n'):
        line_str = line.strip()
        if line_str:
            story.append(Paragraph(line_str, body_style))
        else:
            story.append(Spacer(1, 5))
            
    doc.build(story)


def _execute_generate_document(user_id: str, workspace_id: str, args: dict) -> str:
    import os
    from datetime import datetime
    
    filename = args.get("filename", "document.docx").strip()
    fmt = args.get("format", "").lower()
    if not fmt:
        ext = filename.split('.')[-1].lower() if '.' in filename else ''
        fmt = ext if ext in ('docx', 'pdf', 'txt') else 'docx'
    
    if not filename.lower().endswith(f".{fmt}"):
        base, _ = os.path.splitext(filename)
        filename = f"{base}.{fmt}"
        
    title = args.get("title", "Document")
    content = args.get("content", "")
    
    sandbox_dir = os.path.join("workspaces", workspace_id, "documents")
    os.makedirs(sandbox_dir, exist_ok=True)
    
    file_path = os.path.join(sandbox_dir, filename)
    
    if fmt == "txt":
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
            
    elif fmt == "docx":
        from docx import Document
        from docx.shared import Pt, RGBColor
        from docx.enum.text import WD_ALIGN_PARAGRAPH
        
        doc = Document()
        PRIMARY_COLOR = RGBColor(99, 102, 241)   # Indigo
        TEXT_COLOR = RGBColor(15, 23, 42)
        
        p_title = doc.add_paragraph()
        run_title = p_title.add_run(title)
        run_title.font.name = "Arial"
        run_title.font.size = Pt(20)
        run_title.font.bold = True
        run_title.font.color.rgb = PRIMARY_COLOR
        
        p_meta = doc.add_paragraph()
        run_meta = p_meta.add_run(f"Generated on {datetime.now().strftime('%d %B %Y')}")
        run_meta.font.name = "Arial"
        run_meta.font.size = Pt(9.5)
        run_meta.font.italic = True
        run_meta.font.color.rgb = RGBColor(100, 116, 139)
        
        doc.add_paragraph("\n")
        
        for block in content.split("\n"):
            block_str = block.strip()
            if block_str:
                p_text = doc.add_paragraph()
                if block_str.startswith("#"):
                    level = len(block_str) - len(block_str.lstrip("#"))
                    header_text = block_str.lstrip("#").strip()
                    run_h = p_text.add_run(header_text)
                    run_h.font.name = "Arial"
                    run_h.font.size = Pt(16 if level == 1 else 13)
                    run_h.font.bold = True
                    run_h.font.color.rgb = PRIMARY_COLOR
                elif block_str.startswith("**") and block_str.endswith("**"):
                    bold_text = block_str.replace("**", "").strip()
                    run_b = p_text.add_run(bold_text)
                    run_b.font.name = "Arial"
                    run_b.font.size = Pt(11)
                    run_b.font.bold = True
                    run_b.font.color.rgb = TEXT_COLOR
                else:
                    run_txt = p_text.add_run(block)
                    run_txt.font.name = "Arial"
                    run_txt.font.size = Pt(11)
                    run_txt.font.color.rgb = TEXT_COLOR
            else:
                doc.add_paragraph()
                
        doc.save(file_path)
        
    elif fmt == "pdf":
        temp_docx_name = f"temp_{filename}.docx"
        temp_docx_path = os.path.join(sandbox_dir, temp_docx_name)
        
        from docx import Document
        from docx.shared import Pt, RGBColor
        
        doc = Document()
        PRIMARY_COLOR = RGBColor(220, 38, 38)   # Crimson for PDF
        TEXT_COLOR = RGBColor(15, 23, 42)
        
        p_title = doc.add_paragraph()
        run_title = p_title.add_run(title)
        run_title.font.name = "Arial"
        run_title.font.size = Pt(20)
        run_title.font.bold = True
        run_title.font.color.rgb = PRIMARY_COLOR
        
        p_meta = doc.add_paragraph()
        run_meta = p_meta.add_run(f"Generated on {datetime.now().strftime('%d %B %Y')}")
        run_meta.font.name = "Arial"
        run_meta.font.size = Pt(9.5)
        run_meta.font.italic = True
        run_meta.font.color.rgb = RGBColor(100, 116, 139)
        
        doc.add_paragraph("\n")
        
        for block in content.split("\n"):
            block_str = block.strip()
            if block_str:
                p_text = doc.add_paragraph()
                if block_str.startswith("#"):
                    level = len(block_str) - len(block_str.lstrip("#"))
                    header_text = block_str.lstrip("#").strip()
                    run_h = p_text.add_run(header_text)
                    run_h.font.name = "Arial"
                    run_h.font.size = Pt(16 if level == 1 else 13)
                    run_h.font.bold = True
                    run_h.font.color.rgb = PRIMARY_COLOR
                elif block_str.startswith("**") and block_str.endswith("**"):
                    bold_text = block_str.replace("**", "").strip()
                    run_b = p_text.add_run(bold_text)
                    run_b.font.name = "Arial"
                    run_b.font.size = Pt(11)
                    run_b.font.bold = True
                    run_b.font.color.rgb = TEXT_COLOR
                else:
                    run_txt = p_text.add_run(block)
                    run_txt.font.name = "Arial"
                    run_txt.font.size = Pt(11)
                    run_txt.font.color.rgb = TEXT_COLOR
            else:
                doc.add_paragraph()
                
        doc.save(temp_docx_path)
        
        try:
            import docx2pdf
            docx2pdf.convert(temp_docx_path, file_path)
        except Exception as pdf_err:
            print("[Actions Engine] docx2pdf failed, falling back to reportlab:", pdf_err)
            try:
                _generate_pdf_reportlab(file_path, title, content)
            except Exception as rl_err:
                print("[Actions Engine] reportlab fallback failed:", rl_err)
                raise Exception(f"PDF generation failed: {pdf_err}. Fallback also failed: {rl_err}")
        finally:
            if os.path.exists(temp_docx_path):
                try:
                    os.remove(temp_docx_path)
                except Exception:
                    pass
                    
    # Upload to Supabase Storage → permanent signed URL
    from backend.docs import upload_to_storage, register_generated_doc, update_memory_after_doc
    storage_sub = f"documents/{filename}"
    download_url = upload_to_storage(workspace_id, file_path, storage_sub)

    if not download_url:
        download_url = f"/api/sandbox/download?path=documents/{filename}"
        print(f"[Actions] Document Storage upload failed — using local fallback URL")

    full_storage_path = f"{workspace_id}/{storage_sub}"
    register_generated_doc(
        user_id=user_id,
        workspace_id=workspace_id,
        action_id="",
        doc_type="document",
        filename=filename,
        title=title,
        description=f"{fmt.upper()} document: {title}",
        fmt=fmt,
        storage_path=full_storage_path,
        download_url=download_url,
        file_size=os.path.getsize(file_path),
    )

    # Update memory in background
    threading.Thread(
        target=update_memory_after_doc,
        args=(user_id, "document", title)
    ).start()

    return f"Document **{title}** generated — [⬇ Download {fmt.upper()}]({download_url})"


