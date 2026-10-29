from unittest.mock import patch
from django.test import SimpleTestCase
from PIL import Image
from .ticket_processing import text_fields, image_fields, checked_fields

class TicketOcrTests(SimpleTestCase):
    def test_values_before_english_labels_and_footer_are_not_agent(self):
        text='Hạn sử dụng 24/10/2026\nExpiration date:\nTên gói dịch vụ ECO CL AH\nService Package:\nPARK: 16:00 - 22:00\nSHOW: 20:00 - 21:00\nCode 1234567890001-179-0000001\nĐại lý hợp tác AHBN\nCooperative agent:\nhttps://example.com/?invoiceid=abcdef&is_agency=1 1/2'
        fields=text_fields(text);self.assertEqual(fields['expiry'],'24/10/2026');self.assertEqual(fields['package'],'ECO CL AH');self.assertEqual(fields['agent'],'AHBN')
        self.assertEqual(text_fields('Cooperative agent:\nabcdef&is_agency=1 1/2')['agent'],'')
        self.assertEqual(text_fields('Đại lý hợp tác AHBN Cooperative agent:')['agent'],'AHBN')

    def test_value_only_column_and_single_column_ocr_mode(self):
        text='24/10/2026\nECO CL AH\nPARK: 16:00 - 22:00\nSHOW: 20:00 - 21:00\n1234567890001-179-0000001\nAHBN'
        with patch('pytesseract.image_to_string',return_value=text) as read:
            fields=image_fields(Image.new('RGB',(500,650),'white'),column=True)
        checked_fields(fields);self.assertEqual(fields['agent'],'AHBN');self.assertEqual(fields['package'],'ECO CL AH');self.assertEqual(read.call_args.kwargs['config'],'--psm 6')

    def test_vietnamese_labels_and_no_fabricated_values(self):
        fields=text_fields('Hạn sử dụng 24/10/2026 Tên gói dịch vụ ECO CK BM Thời gian P4RK: 16:00 - 22:00 SHOW: 20:00 - 21:00 Code 7142104160001-66-0134225 Đại lý hợp tác BM')
        self.assertEqual(fields['package'],'ECO CK BM');self.assertEqual(fields['park_time'],'16:00 - 22:00');self.assertEqual(fields['agent'],'BM')
        self.assertEqual(text_fields('24/10/2026')['park_time'],'')

    def test_image_retry_fills_only_missing_fields(self):
        with patch('apps.legacy.ticket_processing.ocr',return_value='24/10/2026 SHOW: 20:00 - 21:00'),patch('pytesseract.image_to_string',return_value='Service Package: ECO CK BM Time PARK: 16:00 - 22:00 SHOW: 19:00 - 20:00 Code 7142104160001-66-0134225 Cooperative agent: BM') as retry:
            fields=image_fields(Image.new('RGB',(500,650),'white'))
        self.assertEqual(fields['package'],'ECO CK BM');self.assertEqual(fields['agent'],'BM');self.assertEqual(fields['show_time'],'20:00 - 21:00');self.assertEqual(retry.call_count,1)

    def test_error_names_missing_fields_and_manual_correction_accepted(self):
        fields=text_fields('24/10/2026 SHOW: 20:00 - 21:00 Code 7142104160001-66-0134225')
        with self.assertRaisesMessage(ValueError,'Gói dịch vụ, Giờ PARK, Đại lý gốc'):checked_fields(fields)
        fields.update(package='ECO CK BM',park_time='16:00 - 22:00',agent='BM');self.assertEqual(checked_fields(fields),fields)
