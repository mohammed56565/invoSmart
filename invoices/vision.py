import os
import re
import tempfile
from google.cloud import vision
from pdf2image import convert_from_path
from django.conf import settings
from datetime import datetime

os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    'google-credentials.json'
)


def extract_text_from_file(file_path):
    client = vision.ImageAnnotatorClient()

    if file_path.lower().endswith('.pdf'):
        pages = convert_from_path(
            file_path,
            poppler_path=settings.POPPLER_PATH
        )
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp:
            pages[0].save(tmp.name, 'JPEG')
            tmp_path = tmp.name

        with open(tmp_path, 'rb') as f:
            content = f.read()
        os.unlink(tmp_path)
    else:
        with open(file_path, 'rb') as f:
            content = f.read()

    image = vision.Image(content=content)
    response = client.document_text_detection(image=image)

    if response.error.message:
        raise Exception(f'Vision API error: {response.error.message}')

    return response.full_text_annotation


def extract_invoice_data(file_path):
    annotation = extract_text_from_file(file_path)

    if not annotation:
        return None

    words = []
    for page in annotation.pages:
        for block in page.blocks:
            for paragraph in block.paragraphs:
                for word in paragraph.words:
                    word_text = ''.join([s.text for s in word.symbols])
                    words.append({
                        'text': word_text,
                        'confidence': word.confidence
                    })

    full_text = annotation.text

    data = {
        'invoice_number': extract_invoice_number(full_text),
        'supplier_name': extract_supplier_name(full_text),
        'total_amount': extract_total_amount(full_text),
        'date_issued': extract_date(full_text),
        'po_number': extract_po_number(full_text),
        'confidence_scores': calculate_confidence(words),
    }

    return data


def extract_invoice_number(text):
    patterns = [
        r'invoice\s*number\s*:?\s*([A-Z0-9\-]+)',
        r'invoice\s*#?\s*:?\s*([A-Z0-9\-]+)',
        r'inv\s*#?\s*:?\s*([A-Z0-9\-]+)',
        r'(INV-[0-9]+)',
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(1).strip()
    return ''

def extract_supplier_name(text):
    patterns = [
        r'(?:from|vendor|supplier|bill\s*from|sold\s*by)\s*:?\s*([A-Za-z0-9\s&.,]+)',
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(1).strip()
    return ''


def extract_total_amount(text):
    patterns = [
        r'total\s*due\s*:?\s*\$?([\d,]+\.?\d*)',
        r'grand\s*total\s*:?\s*\$?([\d,]+\.?\d*)',
        r'total\s*:?\s*\$?([\d,]+\.?\d*)',
        r'amount\s*due\s*:?\s*\$?([\d,]+\.?\d*)',
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            amount = match.group(1).replace(',', '')
            try:
                return float(amount)
            except:
                pass
    return None




def extract_date(text):
    patterns = [
        (r'(\d{1,2})[/-](\d{1,2})[/-](\d{4})', '%d/%m/%Y'),
        (r'(\d{4})[/-](\d{1,2})[/-](\d{1,2})', '%Y/%m/%d'),
        (r'(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d{1,2}),?\s+(\d{4})', None),
    ]
    
    for pattern, fmt in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            if fmt is None:
                try:
                    date_str = match.group(0)
                    date_obj = datetime.strptime(date_str, '%B %d, %Y')
                    return date_obj.strftime('%Y-%m-%d')
                except:
                    try:
                        date_obj = datetime.strptime(date_str, '%B %d %Y')
                        return date_obj.strftime('%Y-%m-%d')
                    except:
                        pass
            else:
                return match.group(0)
    return ''


def extract_po_number(text):
    patterns = [
        r'P\.?O\.?\s*#?\s*:?\s*([A-Z0-9\-]+)',
        r'purchase\s*order\s*#?\s*:?\s*([A-Z0-9\-]+)',
        r'order\s*number\s*:?\s*([A-Z0-9\-]+)',
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(1).strip()
    return ''


def calculate_confidence(words):
    if not words:
        return {}

    total_confidence = sum(w['confidence'] for w in words)
    avg_confidence = total_confidence / len(words)

    return {
        'overall': round(avg_confidence * 100, 1),
    }

def perform_ocr(file_path):
    """
    قراءة النص من الفاتورة باستخدام Google Vision API
    
    Args:
        file_path: مسار ملف الفاتورة
        
    Returns:
        str: النص المستخرج من الفاتورة
    """
    annotation = extract_text_from_file(file_path)
    
    if not annotation:
        return ""
    
    # إرجاع النص الكامل
    return annotation.text