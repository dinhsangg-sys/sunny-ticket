"""Render login states from Django against an isolated database for visual review."""
import os,json,tempfile
from pathlib import Path
os.environ.setdefault('DJANGO_SETTINGS_MODULE','config.settings.development')
import django
django.setup()
from django.conf import settings
from django.core.management import call_command
from django.db import connections
from django.test import Client
with tempfile.TemporaryDirectory() as folder:
    settings.DATABASES['default']['NAME']=str(Path(folder)/'preview.sqlite3');settings.ALLOWED_HOSTS=['testserver']
    call_command('migrate',verbosity=0)
    client=Client();normal=client.get('/login/?next=/counter/');error=client.post('/login/',{'username':'sunny-team','password':'invalid-test-password','next':'/counter/'})
    assert normal.status_code==error.status_code==200
    output={'normal':normal.content.decode(),'error':error.content.decode()}
    connections.close_all();print(json.dumps(output))
