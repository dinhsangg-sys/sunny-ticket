from io import BytesIO
from tempfile import TemporaryDirectory
from django.test import TestCase,override_settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from PIL import Image
from .richtext import render_body,MARKER
from .admin import ServiceForm

class RichTextTests(TestCase):
    def test_old_text_and_rich_html_are_safe(self):
        self.assertIn('&lt;script&gt;',render_body('Old <script>alert(1)</script>'))
        result=render_body(MARKER+'<h2>Title</h2><p onclick="bad()">Text</p><script>bad()</script><a href="javascript:bad()">link</a><img src="https://tracker.test/a">')
        self.assertIn('<h2>Title</h2>',result)
        for forbidden in ['onclick','<script','javascript:','tracker.test']:self.assertNotIn(forbidden,result)
    def test_widget_and_image_upload(self):
        self.assertIn('sunny-editor',str(ServiceForm()['body']))
        self.assertEqual(self.client.post('/online/editor/upload/').status_code,403)
        user=get_user_model().objects.create_superuser('editor','editor@example.com','testpass')
        self.client.force_login(user)
        self.assertEqual(self.client.post('/online/editor/upload/',{'image':SimpleUploadedFile('x.svg',b'<svg/>')}).status_code,400)
        image=BytesIO();Image.new('RGB',(10,10)).save(image,'PNG')
        with TemporaryDirectory() as directory,override_settings(MEDIA_ROOT=directory):
            response=self.client.post('/online/editor/upload/',{'image':SimpleUploadedFile('x.png',image.getvalue(),content_type='image/png')})
            self.assertEqual(response.status_code,200)
            url=response.json()['url'];self.client.logout()
            response=self.client.get(url);self.assertEqual(response.status_code,200);response.close()
            self.assertIn(url,render_body(MARKER+'<img src="'+url+'" onerror="bad()">'))
