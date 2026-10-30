import copy
from io import BytesIO
import json
from pathlib import Path
import tempfile
import uuid
from unittest.mock import patch
import pymupdf as fitz
from PIL import Image
import zxingcpp
from django.test import TestCase, override_settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.auth.models import Permission
from django.core import mail
from apps.accounts.models import User
from .models import Workspace, CounterTicketBatch, CounterIssuedQR
from .ticket_processing import extract_tickets

def qr_image(payload):
    code=zxingcpp.write_barcode_to_image(zxingcpp.create_barcode(payload,zxingcpp.BarcodeFormat.QRCode),scale=6)
    height,width=memoryview(code).shape;image=Image.frombytes('L',(width,height),bytes(code));stream=BytesIO();image.save(stream,format='PNG');return stream.getvalue()

def source_pdf(count=2,duplicate=False):
    document=fitz.open()
    for index in range(count):
        page=document.new_page();page.insert_image(fitz.Rect(60,60,230,230),stream=qr_image('SAMPLE-ONLY-'+str(0 if duplicate else index)))
        text='Expiration date: 31/12/2026\nService Package: ECO TEST\nTime: PARK: 16:00 - 22:00\nSHOW: 20:00 - 21:00\nCode / Ma ve: 1234567890001-1-'+str(index+1).zfill(7)+'\nCooperative agent: TEST'
        page.insert_text((40,300),text,fontsize=12)
    blob=document.tobytes();document.close();return blob

class CounterTicketTests(TestCase):
    def setUp(self):
        self.folder=tempfile.TemporaryDirectory();self.override=override_settings(COUNTER_PRIVATE_ROOT=Path(self.folder.name),EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend',COUNTER_EMAIL_ENABLED=False,DEFAULT_FROM_EMAIL='tickets@example.com');self.override.enable()
        self.user=User.objects.create_user('ticket-user',password='test-password',role='counter');self.user.user_permissions.add(*Permission.objects.filter(content_type__app_label='legacy',codename__in=['counter__view','counter__create']));self.client.force_login(self.user)
        self.data={'bookings':[{'id':'booking','bookingCode':'ST-TEST','qty':2,'source':'counter','counterSellerId':self.user.pk,'customerEmail':'guest@example.com'}]};Workspace.objects.create(pk=1,data=copy.deepcopy(self.data))
        self.source=source_pdf()

    def tearDown(self):self.override.disable();self.folder.cleanup()

    def upload(self,blob=None,booking='booking'):
        return self.client.post('/api/counter/'+booking+'/tickets/',{'files':SimpleUploadedFile('sample.pdf',self.source if blob is None else blob,content_type='application/pdf')})

    def generate(self,batch=None,rows=None,confirmed=True):
        batch=batch or CounterTicketBatch.objects.get();return self.client.post(f'/api/counter/ticket-batches/{batch.pk}/generate/',json.dumps({'confirmed':confirmed,'rows':batch.rows if rows is None else rows}),content_type='application/json')

    def test_import_pdf_and_output_dimensions_qr_and_immutability(self):
        response=self.upload();self.assertEqual(response.status_code,201,response.content);batch=CounterTicketBatch.objects.get();self.assertEqual(len(batch.rows),2);self.assertEqual(batch.rows[0]['package'],'ECO TEST')
        self.assertEqual(self.upload().status_code,200);self.assertEqual(CounterTicketBatch.objects.count(),1)
        result=self.generate(batch);self.assertEqual(result.status_code,200,result.content);self.assertEqual(CounterIssuedQR.objects.count(),2)
        download=self.client.get(result.json()['pdfUrl']);self.assertEqual(download.status_code,200);self.assertEqual(download['X-Frame-Options'],'SAMEORIGIN');blob=b''.join(download.streaming_content);download.close()
        with fitz.open(stream=blob,filetype='pdf') as document:
            self.assertEqual(len(document),2)
            self.assertAlmostEqual(document[0].rect.width*25.4/72,80,places=3);self.assertAlmostEqual(document[0].rect.height*25.4/72,110,places=3)
            self.assertIn('ECO TEST',document[0].get_text())
            image_rects=[rect for image in document[0].get_images(full=True) for rect in document[0].get_image_rects(image[0])]
            self.assertTrue(any(abs(rect.width*25.4/72-23.4)<.01 and abs(rect.height*25.4/72-23.4)<.01 for rect in image_rects))
        batch.refresh_from_db();changed=copy.deepcopy(batch.rows);changed[0]['package']='Other';self.assertEqual(self.generate(batch,changed).status_code,400)
        self.assertEqual(self.generate(batch).status_code,200)

    def test_bad_sources_and_duplicate_qr_rejected(self):
        self.assertEqual(self.upload(b'not a ticket').status_code,400)
        self.assertEqual(self.upload(source_pdf(2,True)).status_code,400);self.assertFalse(CounterTicketBatch.objects.exists())

    def test_update_source_reissues_only_after_review_and_preserves_old_pdf(self):
        self.upload();old=CounterTicketBatch.objects.get();self.generate(old);old.refresh_from_db();old_hash=old.output_hash
        url='/api/counter/booking/tickets/';request_id=str(uuid.uuid4());correct_blob=source_pdf(3)
        def update(blob=None):return self.client.post(url,{'replace':'1','requestId':request_id,'files':SimpleUploadedFile('correct.pdf',correct_blob if blob is None else blob)})
        self.assertEqual(update().status_code,403)
        self.user.user_permissions.add(Permission.objects.get(content_type__app_label='legacy',codename='counter__replace_tickets'))
        self.assertEqual(update(b'bad source').status_code,400)
        old.refresh_from_db();self.assertIsNone(old.superseded_at)
        result=update();self.assertEqual(result.status_code,201,result.content)
        replacement=CounterTicketBatch.objects.get(pk=result.json()['id']);self.assertFalse(replacement.output_hash)
        self.assertEqual(update().json()['id'],str(replacement.pk));self.assertEqual(CounterTicketBatch.objects.count(),2)
        old.refresh_from_db();self.assertIsNone(old.superseded_at)
        self.assertEqual(self.generate(replacement,replacement.rows[1:]).status_code,200)
        old.refresh_from_db();self.assertIsNotNone(old.superseded_at);self.assertEqual(old.output_hash,old_hash)
        self.assertEqual(CounterIssuedQR.objects.count(),3)
        # Selecting the same physical file explicitly still starts a new reviewable version.
        again=self.client.post(url,{'replace':'1','requestId':str(uuid.uuid4()),'files':SimpleUploadedFile('sample.pdf',self.source)})
        self.assertEqual(again.status_code,201);self.assertNotEqual(again.json()['id'],str(old.pk));self.assertFalse(again.json()['ready'])

    def test_booking_four_import_five_only_four_selected_pages_are_exported(self):
        data=copy.deepcopy(self.data);data['bookings'][0]['qty']=4;Workspace.objects.filter(pk=1).update(data=data)
        self.assertEqual(self.upload(source_pdf(5)).status_code,201);batch=CounterTicketBatch.objects.get()
        self.assertEqual(self.generate(batch,batch.rows).status_code,400)
        self.assertEqual(self.generate(batch,batch.rows[:3]).status_code,400)
        selected=[batch.rows[i] for i in (0,1,3,4)]
        response=self.generate(batch,selected);self.assertEqual(response.status_code,200,response.content)
        pdf=self.client.get(response.json()['pdfUrl']);blob=b''.join(pdf.streaming_content);pdf.close()
        with fitz.open(stream=blob,filetype='pdf') as document:self.assertEqual(len(document),4)
        batch.refresh_from_db();self.assertEqual([r['page'] for r in batch.selected],[1,2,4,5]);self.assertEqual(CounterIssuedQR.objects.count(),4)

    def test_reread_unissued_batch_and_protect_issued_version(self):
        self.upload();batch=CounterTicketBatch.objects.get();original=copy.deepcopy(batch.rows)
        damaged=copy.deepcopy(batch.rows);damaged[0]['agent']='WRONG';CounterTicketBatch.objects.filter(pk=batch.pk).update(rows=damaged)
        url=f'/api/counter/ticket-batches/{batch.pk}/reread/'
        response=self.client.post(url,{},content_type='application/json');self.assertEqual(response.status_code,200,response.content)
        batch.refresh_from_db();self.assertEqual(batch.rows[0]['agent'],original[0]['agent']);self.assertEqual(CounterIssuedQR.objects.count(),0)
        self.assertEqual(self.generate(batch).status_code,200)
        self.assertEqual(self.client.post(url,{},content_type='application/json').status_code,409)

    def test_multiple_images_ocr_fallback_and_count_mismatch(self):
        with patch('apps.legacy.ticket_processing.ocr',return_value=''):
            response=self.client.post('/api/counter/booking/tickets/',{'files':[SimpleUploadedFile('a.png',qr_image('PHOTO-1')),SimpleUploadedFile('b.png',qr_image('PHOTO-2'))]})
        self.assertEqual(response.status_code,201,response.content)
        batch=CounterTicketBatch.objects.get();self.assertEqual(len(batch.rows),2);self.assertEqual(batch.rows[0]['expiry'],'')
        self.assertEqual(self.generate(batch).status_code,400)
        self.assertEqual(self.generate(batch,batch.rows[:1]).status_code,400)
        self.assertEqual(self.generate(batch,confirmed=False).status_code,400)

    def test_jpeg_qr_and_ocr_fields_generate_one_ticket(self):
        stream=BytesIO()
        with Image.open(BytesIO(qr_image('JPEG-SAMPLE-ONLY'))) as image:image.convert('RGB').save(stream,format='JPEG',quality=95)
        data=copy.deepcopy(self.data);data['bookings'][0]['qty']=1;Workspace.objects.filter(pk=1).update(data=data)
        text='Expiration date: 31/12/2026 Service Package: ECO TEST Time: PARK: 16:00 - 22:00 SHOW: 20:00 - 21:00 Code / Ma ve: 1234567890001-1-0000001 Cooperative agent: TEST'
        with patch('apps.legacy.ticket_processing.ocr',return_value=text):
            result=self.client.post('/api/counter/booking/tickets/',{'files':SimpleUploadedFile('sample.jpg',stream.getvalue(),content_type='image/jpeg')})
        self.assertEqual(result.status_code,201,result.content);self.assertEqual(CounterTicketBatch.objects.get().rows[0]['package'],'ECO TEST')
        self.assertEqual(self.generate().status_code,200)

    def test_qr_cannot_be_attached_to_another_booking(self):
        self.upload();self.assertEqual(self.generate().status_code,200)
        data=copy.deepcopy(self.data);data['bookings'].append({**data['bookings'][0],'id':'other','bookingCode':'ST-OTHER'});Workspace.objects.filter(pk=1).update(data=data)
        self.assertEqual(self.upload(booking='other').status_code,201)
        batch=CounterTicketBatch.objects.get(booking_id='other');response=self.generate(batch);self.assertEqual(response.status_code,400)
        self.assertEqual(response.json()['error'],'QR đã được gắn cho booking ST-TEST. Chưa xuất bộ vé này.')
        self.assertEqual(CounterIssuedQR.objects.count(),2);batch.refresh_from_db();self.assertFalse(batch.output_hash)

    def test_other_staff_cannot_access_source_qr_pdf_generate_or_email(self):
        self.upload();batch=CounterTicketBatch.objects.get();self.assertEqual(self.generate(batch).status_code,200)
        other=User.objects.create_user('other-counter',password='test-password',role='counter');other.user_permissions.add(*self.user.user_permissions.all());self.client.force_login(other)
        urls=[f'/api/counter/ticket-batches/{batch.pk}/qr/1/',f'/api/counter/ticket-batches/{batch.pk}/pdf/','/api/counter/booking/tickets/']
        for url in urls:self.assertEqual(self.client.get(url).status_code,404)
        self.assertEqual(self.generate(batch).status_code,404)
        self.assertEqual(self.client.post(f'/api/counter/ticket-batches/{batch.pk}/email/',json.dumps({'email':'other@example.com','confirmed':True}),content_type='application/json').status_code,404)

    def test_email_requires_configuration_and_sends_once(self):
        self.upload();self.generate();batch=CounterTicketBatch.objects.get();url=f'/api/counter/ticket-batches/{batch.pk}/email/'
        body=json.dumps({'email':'guest@example.com','confirmed':True})
        self.assertEqual(self.client.post(url,body,content_type='application/json').status_code,400)
        with override_settings(COUNTER_EMAIL_ENABLED=True):
            response=self.client.post(url,body,content_type='application/json');self.assertEqual(response.status_code,200,response.content)
            self.assertEqual(len(mail.outbox),1);self.assertEqual(mail.outbox[0].to,['guest@example.com']);self.assertEqual(len(mail.outbox[0].attachments),1)
            self.assertEqual(self.client.post(url,body,content_type='application/json').status_code,200);self.assertEqual(len(mail.outbox),1)

    def test_uncertain_email_not_retried(self):
        self.upload();self.generate();batch=CounterTicketBatch.objects.get();url=f'/api/counter/ticket-batches/{batch.pk}/email/';body=json.dumps({'email':'guest@example.com','confirmed':True})
        with override_settings(COUNTER_EMAIL_ENABLED=True),patch('apps.legacy.counter_tickets.EmailMessage.send',side_effect=TimeoutError()):
            self.assertEqual(self.client.post(url,body,content_type='application/json').status_code,502)
            self.assertEqual(self.client.post(url,body,content_type='application/json').status_code,409)
        batch.refresh_from_db();self.assertEqual(batch.email_state,'uncertain')
