from fpdf import FPDF
from typing import List, Dict


def generate_pdf_from_knowledge(entries: List[Dict], destination: str) -> str:
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    for entry in entries:
        pdf.add_page()
        pdf.set_font("Arial", 'B', 16)
        pdf.cell(0, 10, entry.get('filename', 'Unknown File'), ln=True)
        pdf.set_font("Arial", '', 12)
        pdf.multi_cell(0, 10, entry.get('high_level_summary', 'No summary available.'))
        pdf.ln(5)
        for key in ['key_points', 'learning_objectives', 'important_quotes', 'definitions', 'themes', 'topic_tags', 'inferred_insights']:
            values = entry.get(key, [])
            if not values:
                continue
            pdf.set_font("Arial", 'B', 12)
            pdf.cell(0, 10, key.replace('_', ' ').title(), ln=True)
            pdf.set_font("Arial", '', 11)
            if isinstance(values, list):
                for item in values:
                    pdf.multi_cell(0, 8, f"- {item}")
            else:
                pdf.multi_cell(0, 8, str(values))
            pdf.ln(2)
    pdf.output(destination)
    return destination
