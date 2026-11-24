"""Fixed Hoi An forecast proxy. No customer coordinates, payment data or API keys."""
import gzip,json,math,zlib
from datetime import timedelta
from email.utils import parsedate_to_datetime
from urllib.request import Request,urlopen
from urllib.error import HTTPError,URLError
from zoneinfo import ZoneInfo
from django.conf import settings
from django.core.cache import caches
from django.http import JsonResponse
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from django.views.decorators.http import require_GET

URL='https://api.met.no/weatherapi/locationforecast/2.0/compact?lat=15.8801&lon=108.3380'
KEY='hoi-an-forecast-v1'
ZONE=ZoneInfo('Asia/Ho_Chi_Minh')

def category(symbol):
    night=str(symbol).endswith('_night')
    symbol=str(symbol).split('_')[0]
    if 'thunder' in symbol:return 'thunder'
    if 'sleet' in symbol or 'snow' in symbol:return 'snow'
    if 'rain' in symbol:return 'rain'
    if symbol=='fog':return 'fog'
    if symbol=='clearsky':return 'clear_night' if night else 'sun'
    if symbol in ('fair','partlycloudy'):return 'partly_cloudy'
    if symbol=='cloudy':return 'cloudy'
    return 'unknown'

def normalize(raw,now):
    entries=[]
    for row in raw['properties']['timeseries']:
        stamp=parse_datetime(row['time'])
        if not stamp or timezone.is_naive(stamp):continue
        stamp=stamp.astimezone(ZONE)
        value=row['data']['instant']['details']['air_temperature']
        if type(value) not in (int,float) or not math.isfinite(value) or not -60<=value<=65:continue
        period=row['data'].get('next_1_hours') or row['data'].get('next_6_hours') or row['data'].get('next_12_hours') or {}
        condition=category(period.get('summary',{}).get('symbol_code'))
        entries.append({'stamp':stamp,'temperature':round(value,1),'condition':condition})
    if not entries:raise ValueError('No valid forecast')
    nearest=min(entries,key=lambda row:abs((row['stamp']-now).total_seconds()))
    if abs((nearest['stamp']-now).total_seconds())>10800:raise ValueError('Forecast too old')
    days=[];today=now.astimezone(ZONE).date()
    severity={'unknown':0,'sun':1,'clear_night':1,'partly_cloudy':2,'cloudy':3,'fog':4,'snow':5,'rain':6,'thunder':7}
    for offset in range(3):
        day=today+timedelta(days=offset)
        samples=[row for row in entries if row['stamp'].date()==day and row['stamp']>=now-timedelta(hours=1)]
        if not samples:continue
        days.append({'date':day.isoformat(),'min':min(row['temperature'] for row in samples),'max':max(row['temperature'] for row in samples),'condition':max(('sun' if row['condition']=='clear_night' else row['condition'] for row in samples),key=lambda value:severity[value])})
    return {'location':'Hoi An','timezone':'Asia/Ho_Chi_Minh','temperature':nearest['temperature'],'condition':nearest['condition'],'forecastTime':nearest['stamp'].isoformat(),'updatedAt':raw['properties']['meta']['updated_at'],'days':days,'source':'MET Norway'}

def expiry(headers,now):
    try:return max(10800,int((parsedate_to_datetime(headers['Expires'])-now).total_seconds()))
    except (KeyError,TypeError,ValueError,OverflowError):return 10800

def get_weather():
    cache=caches['weather'];now=timezone.now();stored=cache.get(KEY)
    if stored and stored['until']>now.timestamp():return {**normalize(stored['raw'],now),'stale':False}
    if cache.get(KEY+'-retry'):raise ValueError('Retry later')
    if not cache.add(KEY+'-lock',True,15):raise ValueError('Updating')
    try:
        headers={'User-Agent':settings.HOI_AN_WEATHER_USER_AGENT,'Accept':'application/json','Accept-Encoding':'gzip, deflate'}
        if stored and stored.get('modified'):headers['If-Modified-Since']=stored['modified']
        request=Request(URL,headers=headers)
        try:
            with urlopen(request,timeout=4) as response:
                blob=response.read(524289)
                if len(blob)>524288:raise ValueError('Response too large')
                if response.headers.get('Content-Encoding')=='gzip':blob=gzip.decompress(blob)
                elif response.headers.get('Content-Encoding')=='deflate':
                    blob=zlib.decompress(blob)
                if len(blob)>2097152:raise ValueError('Response too large')
                raw=json.loads(blob);payload=normalize(raw,now)
                stored={'raw':raw,'until':now.timestamp()+expiry(response.headers,now),'modified':response.headers.get('Last-Modified','')}
                cache.set(KEY,stored,max(86400,int(stored['until']-now.timestamp())+21600));return {**payload,'stale':False}
        except HTTPError as exc:
            if exc.code==304 and stored:
                stored['until']=now.timestamp()+expiry(exc.headers,now);cache.set(KEY,stored,max(86400,int(stored['until']-now.timestamp())+21600))
                return {**normalize(stored['raw'],now),'stale':False}
            raise
    except (OSError,ValueError,KeyError,TypeError,IndexError,EOFError,zlib.error):
        cache.set(KEY+'-retry',True,120)
        if stored and now.timestamp()-stored.get('until',0)<21600:
            return {**normalize(stored['raw'],now),'stale':True}
        raise ValueError('Weather unavailable') from None
    finally:cache.delete(KEY+'-lock')

@require_GET
def weather_api(request):
    if not settings.HOI_AN_WEATHER_ENABLED:return JsonResponse({'available':False},status=503)
    try:response=JsonResponse({'available':True,**get_weather()})
    except (OSError,ValueError):response=JsonResponse({'available':False},status=503)
    response['Cache-Control']='public, max-age=120';return response
