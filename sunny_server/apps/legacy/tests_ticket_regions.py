from io import BytesIO
from unittest.mock import patch
import pymupdf as fitz
from PIL import Image
from django.test import SimpleTestCase
from .ticket_processing import extract_tickets
from .tests_counter_tickets import qr_image

class TicketRegionTests(SimpleTestCase):
    def pdf(self,sideways=False,duplicate=False):
        doc=fitz.open();page=doc.new_page(width=800 if sideways else 400,height=400 if sideways else 800)
        for i in range(2):
            x,y=(i*400,0) if sideways else (0,i*400)
            page.insert_image(fitz.Rect(x+250,y+30,x+350,y+130),stream=qr_image('REGION-'+str(0 if duplicate else i)))
            page.insert_text((x+30,y+180),'Expiration date: '+('01/11/2026' if i==0 else '02/11/2026')+'\nService Package: '+('ECO FIRST' if i==0 else 'VIP SECOND')+'\nTime PARK: 16:00 - 22:00\nSHOW: 20:00 - 21:00\nCode 1234567890001-1-'+str(i+1).zfill(7)+'\nCooperative agent: '+('FIRST' if i==0 else 'SECOND'),fontsize=10)
        blob=doc.tobytes();doc.close();return blob

    def test_stacked_and_side_by_side_pdf_keep_fields_attached_to_qr(self):
        for sideways in (False,True):
            rows=extract_tickets(self.pdf(sideways));self.assertEqual(len(rows),2)
            self.assertEqual([r['source_page'] for r in rows],[1,1]);self.assertEqual([r['package'] for r in rows],['ECO FIRST','VIP SECOND'])
            self.assertEqual([r['agent'] for r in rows],['FIRST','SECOND']);self.assertEqual([r['expiry'] for r in rows],['01/11/2026','02/11/2026'])
            self.assertNotEqual(rows[0]['qr_hash'],rows[1]['qr_hash'])

    def test_two_images_are_ocr_processed_separately(self):
        image=Image.new('RGB',(800,1000),'white')
        for i in range(2):
            with Image.open(BytesIO(qr_image('PHOTO-REGION-'+str(i)))) as qr:image.paste(qr.resize((150,150)),(600,40+i*500))
        stream=BytesIO();image.save(stream,format='PNG')
        with patch('apps.legacy.ticket_processing.region_fields',side_effect=[{'package':'FIRST'},{'package':'SECOND'}]) as read:
            rows=extract_tickets(stream.getvalue())
        self.assertEqual(len(rows),2);self.assertEqual(read.call_count,2);self.assertEqual([r['package'] for r in rows],['FIRST','SECOND'])

    def test_duplicate_qr_in_one_page_is_rejected(self):
        with self.assertRaisesMessage(ValueError,'QR trùng'):extract_tickets(self.pdf(duplicate=True))
