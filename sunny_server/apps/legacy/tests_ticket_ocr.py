from unittest.mock import patch
from django.test import SimpleTestCase
from PIL import Image
from .ticket_processing import text_fields, image_fields, checked_fields

class TicketOcrTests(SimpleTestCase):
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
