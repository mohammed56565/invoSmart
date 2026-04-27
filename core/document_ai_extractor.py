import os
from google.cloud import documentai_v1 as documentai
from google.api_core.client_options import ClientOptions
from datetime import datetime
import re 

from dotenv import load_dotenv
load_dotenv()


def process_invoice_with_documentai(image_path):
    project_id = os.getenv('DOCUMENT_AI_PROJECT_ID')
    location = os.getenv('DOCUMENT_AI_LOCATION', 'us')
    processor_id = os.getenv('DOCUMENT_AI_PROCESSOR_ID')
    credentials_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
    
    if not all([project_id, processor_id, credentials_path]):
        return None
    
    if os.path.exists(credentials_path):
        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = credentials_path
    else:
        return None
    
    try:
        opts = ClientOptions(api_endpoint=f"{location}-documentai.googleapis.com")
        client = documentai.DocumentProcessorServiceClient(client_options=opts)
        name = client.processor_path(project_id, location, processor_id)
        
        with open(image_path, "rb") as image_file:
            image_content = image_file.read()
        
        if image_path.lower().endswith('.pdf'):
            mime_type = "application/pdf"
        else:
            mime_type = "image/jpeg"
        
        raw_document = documentai.RawDocument(content=image_content, mime_type=mime_type)
        request = documentai.ProcessRequest(name=name, raw_document=raw_document)
        result = client.process_document(request=request)
        document = result.document
        extracted_data = extract_invoice_fields(document)
        
        return extracted_data
        
    except Exception as e:
        return None


def extract_invoice_fields(document):
    extracted = {
        'supplier_name': None,
        'invoice_number': None,
        'total_amount': None,
        'date_issued': None,
        'po_number': None,
        'confidence_score': 0.0,
        'field_confidences': {
            'invoice_number': 0.0,
            'supplier_name': 0.0,
            'total_amount': 0.0,
            'date_issued': 0.0,
            'po_number': 0.0,
        }
    }
    
    if hasattr(document, 'entities'):
        for entity in document.entities:
            entity_type = entity.type_
            entity_text = entity.mention_text.strip()
            confidence = entity.confidence
            
            if entity_type in ['supplier_name', 'vendor_name', 'seller_name']:
                if confidence > 0.3:
                    supplier = entity_text.split('\n')[0].strip()
                    if len(supplier) > 3:
                        extracted['supplier_name'] = supplier
                        extracted['field_confidences']['supplier_name'] = round(confidence * 100, 2)
            
            if entity_type in ['invoice_id', 'invoice_number']:
                if confidence > 0.4:
                    extracted['invoice_number'] = entity_text
                    extracted['field_confidences']['invoice_number'] = round(confidence * 100, 2)
            
            if entity_type in ['total_amount', 'net_amount', 'invoice_total', 'total', 'grand_total']:
                if confidence > 0.3:
                    amount = extract_amount(entity_text)
                    if amount and amount > 0:
                        extracted['total_amount'] = amount
                        extracted['field_confidences']['total_amount'] = round(confidence * 100, 2)
            
            if entity_type in ['invoice_date', 'date', 'issue_date', 'bill_date', 
                                'due_date', 'delivery_date', 'purchase_date']:
                if confidence > 0.3:
                    date_parsed = parse_date(entity_text)
                    if date_parsed:
                        if not extracted['date_issued']:
                            extracted['date_issued'] = date_parsed
                            extracted['field_confidences']['date_issued'] = round(confidence * 100, 2)
            
            if entity_type in ['purchase_order', 'po_number']:
                if confidence > 0.4:
                    extracted['po_number'] = entity_text
                    extracted['field_confidences']['po_number'] = round(confidence * 100, 2)
    
    if not extracted['supplier_name'] and hasattr(document, 'text'):
        supplier_from_text = extract_supplier_from_text(document.text)
        if supplier_from_text:
            extracted['supplier_name'] = supplier_from_text
            extracted['field_confidences']['supplier_name'] = 50.0
    
    if not extracted['date_issued'] and hasattr(document, 'text'):
        date_from_text = extract_date_from_text(document.text)
        if date_from_text:
            extracted['date_issued'] = date_from_text
            extracted['field_confidences']['date_issued'] = 50.0
    
    if not extracted['po_number'] and hasattr(document, 'text'):
        po_from_text = extract_po_from_text(document.text)
        if po_from_text:
            extracted['po_number'] = po_from_text
            extracted['field_confidences']['po_number'] = 50.0
    
    all_confidences = [v for v in extracted['field_confidences'].values() if v > 0]
    if all_confidences:
        extracted['confidence_score'] = round(sum(all_confidences) / len(all_confidences), 2)
    else:
        extracted['confidence_score'] = 0.0
    
    return extracted


def extract_amount(text):
    amount_match = re.search(r'[\d,]+\.?\d*', text.replace(',', ''))
    if amount_match:
        try:
            return float(amount_match.group())
        except:
            return None
    return None


def parse_date(date_string):
    date_formats = [
        '%Y-%m-%d', '%d/%m/%Y', '%m/%d/%Y', '%d-%m-%Y', '%m-%d-%Y',
        '%Y/%m/%d', '%B %d, %Y', '%d %B %Y', '%b %d, %Y', '%d %b %Y',
        '%b. %d, %Y', '%d %b. %Y', '%B %d %Y', '%b %d %Y',
        '%d.%m.%Y', '%d-%b-%Y',
    ]
    
    date_string = date_string.strip()
    
    for fmt in date_formats:
        try:
            date_obj = datetime.strptime(date_string, fmt)
            return date_obj.strftime('%Y-%m-%d')
        except:
            continue
    
    return None


def extract_supplier_from_text(text):
    patterns = [
        r'Seller:\s*\n\s*([^\n]+)',
        r'Vendor:\s*\n\s*([^\n]+)',
        r'From:\s*\n\s*([^\n]+)',
        r'Bill To:\s*\n\s*([^\n]+)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            supplier = match.group(1).strip()
            if len(supplier) > 3 and not supplier.isdigit():
                return supplier
    
    return None


def extract_date_from_text(text):
    patterns = [
        r'Date of [Ii]ssue:\s*([A-Za-z]+\.?\s+\d{1,2},?\s+\d{4})',
        r'Invoice [Dd]ate:\s*([A-Za-z]+\.?\s+\d{1,2},?\s+\d{4})',
        r'Date:\s*([A-Za-z]+\.?\s+\d{1,2},?\s+\d{4})',
        r'Bill Date:\s*([A-Za-z]+\.?\s+\d{1,2},?\s+\d{4})',
        r'Date of [Ii]ssue:\s*(\d{1,2}/\d{1,2}/\d{4})',
        r'Invoice [Dd]ate:\s*(\d{1,2}/\d{1,2}/\d{4})',
        r'Date:\s*(\d{1,2}/\d{1,2}/\d{4})',
        r'Bill Date:\s*(\d{1,2}/\d{1,2}/\d{4})',
        r'Invoice [Dd]ate:\s*([A-Za-z]+\s+\d{1,2}\s+\d{4})',
        r'Date:\s*([A-Za-z]+\s+\d{1,2}\s+\d{4})',
        r'\b([A-Za-z]{3,9}\.?\s+\d{1,2},?\s+\d{4})\b',
        r'\b(\d{1,2}/\d{1,2}/\d{4})\b',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            date_str = match.group(1)
            parsed = parse_date(date_str)
            if parsed:
                return parsed
    
    return None


def extract_po_from_text(text):
    patterns = [
        r'PO\s*Number[:\s]+(\d+)',
        r'Purchase\s*Order[:\s]+(\d+)',
        r'Order\s*Number[:\s]+(\d+)',
        r'PO[:\s#]+(\d+)',
        r'P\.?O\.?[:\s#]+(\d+)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            po_num = match.group(1).strip()
            return po_num
    
    return None