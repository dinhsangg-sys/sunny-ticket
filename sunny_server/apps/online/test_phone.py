from django.test import SimpleTestCase
from django.core.exceptions import ValidationError
from .phone import normalize_phone,country
from .forms import CartCheckoutForm

class PhoneTests(SimpleTestCase):
    def test_normalization_and_trunk_prefix(self):
        self.assertEqual(normalize_phone('0932 548 145','Vietnam (+84)'),'+84932548145')
        self.assertEqual(normalize_phone('+84 (0)932-548-145','VN'),'+84932548145')
        self.assertEqual(normalize_phone('(202) 555-0100','+1'),'+12025550100')
        self.assertEqual(normalize_phone('06 12345678','IT'),'+390612345678')
        self.assertEqual(country('United States (+1)'),('US','1'))
    def test_rejects_unknown_codes_mismatch_and_bad_numbers(self):
        for number,code in [('0932548145','+1'),('+84932548145','+1'),('letters','+84'),('123456789012345678','+84'),('2025550100','+999'),('++12025550100','+1')]:
            with self.assertRaises(ValidationError):normalize_phone(number,code)
    def test_country_control_default_and_translations(self):
        form=CartCheckoutForm(lang='en')
        self.assertEqual(form['phone_country'].value(),'+1')
        self.assertIn('United States (+1)',str(form['phone_country']))
        self.assertIn('Việt Nam (+84)',str(CartCheckoutForm(lang='vi')['phone_country']))
        self.assertIn('phone_country.js',str(form.media))

    def test_checkout_saves_normalized_phone_and_rejects_mismatch(self):
        import uuid
        data={'request_id':str(uuid.uuid4()),'quote_token':'test-token','customer_name':'Guest','email':'guest@example.test','phone_country':'Việt Nam (+84)','phone':'0932548145','agreed':'on'}
        form=CartCheckoutForm(data,lang='vi');self.assertTrue(form.is_valid(),form.errors)
        self.assertEqual(form.cleaned_data['phone'],'+84932548145')
        form=CartCheckoutForm({**data,'phone_country':'+1','phone':'+84932548145'},lang='en')
        self.assertFalse(form.is_valid());self.assertIn('phone',form.errors)
