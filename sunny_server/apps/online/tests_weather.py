import json
from datetime import timedelta
from email.utils import format_datetime
from unittest.mock import patch,MagicMock
from urllib.error import HTTPError
from django.test import SimpleTestCase,override_settings
from django.core.cache import caches
from django.utils import timezone
from .weather import weather_api,get_weather,KEY,normalize,category

@override_settings(CACHES={'default':{'BACKEND':'django.core.cache.backends.locmem.LocMemCache'},'weather':{'BACKEND':'django.core.cache.backends.locmem.LocMemCache','LOCATION':'weather-tests'}},HOI_AN_WEATHER_ENABLED=True)
class WeatherTests(SimpleTestCase):
    def setUp(self):
        caches['weather'].clear();self.now=timezone.now().replace(minute=0,second=0,microsecond=0)
        self.raw={'properties':{'meta':{'updated_at':self.now.isoformat()},'timeseries':[{'time':(self.now+timedelta(hours=i)).isoformat(),'data':{'instant':{'details':{'air_temperature':25+i%5}},'next_1_hours':{'summary':{'symbol_code':'rainshowers_day' if i%4==0 else 'clearsky_day'}}}} for i in range(72)]}}
    def response(self):
        response=MagicMock();response.__enter__.return_value=response
        response.headers={'Expires':format_datetime(timezone.now()+timedelta(minutes=20)),'Last-Modified':format_datetime(timezone.now()-timedelta(minutes=10))}
        response.read.return_value=json.dumps(self.raw).encode();return response
    @patch('apps.online.weather.urlopen')
    def test_fixed_city_forecast_cached_and_no_client_location_or_secrets(self,fetch):
        fetch.return_value=self.response();first=get_weather();second=get_weather()
        self.assertEqual(fetch.call_count,1);self.assertEqual(first,second);self.assertEqual(len(first['days']),3)
        self.assertEqual(first['source'],'MET Norway');self.assertIn(first['condition'],['rain','sun'])
        request=fetch.call_args.args[0];self.assertIn('lat=15.8801&lon=108.3380',request.full_url);self.assertIn('sunnygovn.com',request.headers['User-agent'])
        response=self.client.get('/api/public/weather/?lat=0&lon=0')
        self.assertEqual(response.status_code,200);self.assertEqual(response.json()['location'],'Hoi An');self.assertEqual(fetch.call_count,1)
        self.assertNotIn('account',response.content.decode());self.assertNotIn('secret',response.content.decode())
    @patch('apps.online.weather.urlopen')
    def test_outage_no_fake_values_and_retry_backoff(self,fetch):
        fetch.side_effect=TimeoutError()
        response=self.client.get('/api/public/weather/')
        self.assertEqual(response.status_code,503);self.assertFalse(response.json()['available']);self.assertNotIn('temperature',response.json())
        self.client.get('/api/public/weather/');self.assertEqual(fetch.call_count,1)
        with self.settings(HOI_AN_WEATHER_ENABLED=False):self.assertEqual(self.client.get('/api/public/weather/').status_code,503)
    @patch('apps.online.weather.urlopen')
    def test_conditional_request_and_stale_fallback(self,fetch):
        cache=caches['weather'];cache.set(KEY,{'raw':self.raw,'until':timezone.now().timestamp()-60,'modified':'Tue, 24 Nov 2026 00:00:00 GMT'},3600)
        fetch.side_effect=HTTPError('url',304,'Not modified',{'Expires':format_datetime(timezone.now()+timedelta(minutes=20))},None)
        self.assertFalse(get_weather()['stale']);self.assertIn('If-modified-since',fetch.call_args.args[0].headers)
        stored=cache.get(KEY);stored['until']=timezone.now().timestamp()-60;cache.set(KEY,stored,3600);fetch.side_effect=TimeoutError()
        self.assertTrue(get_weather()['stale'])
    def test_invalid_and_old_data_are_not_presented_as_current(self):
        self.assertEqual(category('heavyrainandthunder_day'),'thunder')
        self.assertEqual(category('clearsky_night'),'clear_night')
        with self.assertRaises(ValueError):normalize(self.raw,self.now+timedelta(days=10))
        for row in self.raw['properties']['timeseries']:row['data']['instant']['details']['air_temperature']=None
        with self.assertRaises(ValueError):normalize(self.raw,self.now)
