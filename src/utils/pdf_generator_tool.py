"""
PDF Generation Tool for ARK Agent AGI
Create PDFs from data and text
"""

import os
from typing import Any, Dict, List, Optional

from utils.logging_utils import log_event

try:
    from fpdf import FPDF

    FPDF_AVAILABLE = True
except ImportError:
    FPDF_AVAILABLE = False


class PDFGeneratorTool:
    """
    Generate PDF documents from text and data
    """

    def __init__(self, output_dir: str = "data/pdfs"):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        self.fpdf_available = FPDF_AVAILABLE

        log_event(
            "PDFGeneratorTool",
            {"event": "initialized", "fpdf_available": FPDF_AVAILABLE, "output_dir": output_dir},
        )

    def create_pdf(self, title: str, content: str, filename: Optional[str] = None) -> Dict[str, Any]:
        """
        Create a simple PDF document

        Args:
            title: Document title
            content: Document content
            filename: Output filename (optional)

        Returns:
            Generation result
        """
        if not self.fpdf_available:
            return {
                "success": False,
                "error": "fpdf library not installed. Install with: pip install fpdf2",
            }

        try:
            pdf = FPDF()
            pdf.add_page()

            # Title
            pdf.set_font("Arial", "B", 16)
            pdf.cell(0, 10, title, ln=True, align="C")
            pdf.ln(10)

            # Content
            pdf.set_font("Arial", "", 12)
            pdf.multi_cell(0, 10, content)

            if not filename:
                filename = f"{title.replace(' ', '_').lower()}.pdf"

            output_path = os.path.join(self.output_dir, filename)
            pdf.output(output_path)

            file_size = os.path.getsize(output_path)

            log_event(
                "PDFGeneratorTool",
                {"event": "pdf_created", "filename": filename, "size": file_size},
            )

            return {
                "success": True,
                "message": "PDF created successfully",
                "path": output_path,
                "filename": filename,
                "size_bytes": file_size,
            }

        except Exception as e:
            log_event("PDFGeneratorTool", {"event": "pdf_error", "error": str(e)})
            return {"success": False, "error": str(e), "error_type": type(e).__name__}

    def create_table_pdf(
        self, title: str, headers: List[str], data: List[List[str]], filename: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create a PDF with a table"""
        if not self.fpdf_available:
            return {
                "success": False,
                "error": "fpdf library not installed. Install with: pip install fpdf2",
            }

        try:
            pdf = FPDF()
            pdf.add_page()

            pdf.set_font("Arial", "B", 16)
            pdf.cell(0, 10, title, ln=True, align="C")
            pdf.ln(10)

            # Table
            pdf.set_font("Arial", "B", 12)
            col_width = pdf.w / (len(headers) + 1)

            # Headers
            for header in headers:
                pdf.cell(col_width, 10, header, border=1)
            pdf.ln()

            # Data
            pdf.set_font("Arial", "", 11)
            for row in data:
                for item in row:
                    pdf.cell(col_width, 10, str(item), border=1)
                pdf.ln()

            if not filename:
                filename = f"{title.replace(' ', '_').lower()}_table.pdf"

            output_path = os.path.join(self.output_dir, filename)
            pdf.output(output_path)

            return {"success": True, "path": output_path, "filename": filename}
        except Exception as e:
            return {"success": False, "error": str(e)}


pdf_generator = PDFGeneratorTool()
