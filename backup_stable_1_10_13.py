"""Run on Ubuntu: sudo .venv/bin/python /path/to/this.py /home/sunny-ticket
Stop the app first so attachments/source do not change during the backup.
This script only reads the application and never resets/migrates its database.
"""
import datetime
from contextlib import closing
import hashlib
import json
import os
from pathlib import Path
import sqlite3
import subprocess
import sys
import tempfile
import zipfile

def main():
    root=Path(sys.argv[1] if len(sys.argv)>1 else '/home/sunny-ticket').resolve()
    database=root/'sunny_server'/'db.sqlite3'
    if not database.is_file() or not database.stat().st_size:
        raise RuntimeError('Database SQLite không tồn tại hoặc rỗng. Chưa sao lưu dữ liệu. Kiểm tra cấu hình database thực tế.')
    output=root.parent/'sunny-ticket-backups'
    output.mkdir(mode=0o700,exist_ok=True)
    stamp=datetime.datetime.now().astimezone().strftime('%Y%m%d-%H%M%S-%f')
    destination=output/('sunny-current-'+stamp+'.zip')
    excluded={'.git','.venv','venv','__pycache__','node_modules','staticfiles'}
    manifest={'createdAt':datetime.datetime.now().astimezone().isoformat(),'referenceTag':'stable-1.10.13','applicationRoot':str(root),'files':{}}
    try:
        manifest['gitHead']=subprocess.check_output(['git','-C',str(root),'rev-parse','HEAD'],text=True,stderr=subprocess.DEVNULL).strip()
    except (OSError,subprocess.CalledProcessError):
        manifest['gitHead']='unavailable'
    with tempfile.TemporaryDirectory(dir=output) as temp:
        snapshot=Path(temp)/'db.sqlite3'
        with closing(sqlite3.connect(database.as_uri()+'?mode=ro',uri=True)) as source,closing(sqlite3.connect(snapshot)) as target:
            source.backup(target)
            if target.execute('PRAGMA quick_check').fetchall()!=[('ok',)]:
                raise RuntimeError('Bản sao database không vượt qua kiểm tra toàn vẹn.')
            tables={r[0] for r in target.execute("SELECT name FROM sqlite_master WHERE type='table'")}
            if 'legacy_workspace' not in tables:
                raise RuntimeError('Database không có bảng legacy_workspace. Hãy kiểm tra đúng database đang dùng.')
        temporary=Path(temp)/'backup.zip'
        with zipfile.ZipFile(temporary,'x',zipfile.ZIP_DEFLATED) as archive:
            def add(path,name):
                before=path.stat()
                digest=hashlib.sha256()
                with path.open('rb') as src,archive.open(name,'w') as dst:
                    while chunk:=src.read(1024*1024):digest.update(chunk);dst.write(chunk)
                after=path.stat()
                if (before.st_size,before.st_mtime_ns)!=(after.st_size,after.st_mtime_ns):
                    raise RuntimeError('Tệp đang thay đổi: '+name+'. Dừng ứng dụng rồi chạy lại.')
                manifest['files'][name]={'sha256':digest.hexdigest(),'bytes':after.st_size}
            add(snapshot,'database/db.sqlite3')
            for directory,folders,files in os.walk(root,followlinks=False):
                base=Path(directory)
                for folder in folders:
                    if (base/folder).is_symlink():raise RuntimeError('Cần sao lưu riêng thư mục liên kết: '+str(base/folder))
                folders[:]=[f for f in folders if f not in excluded]
                for filename in files:
                    path=base/filename
                    if path.is_symlink():raise RuntimeError('Cần sao lưu riêng tệp liên kết: '+str(path))
                    if filename.startswith('db.sqlite3') or filename.endswith(('.pyc','.zip')):continue
                    add(path,'application/'+path.relative_to(root).as_posix())
            archive.writestr('manifest.json',json.dumps(manifest,ensure_ascii=False,indent=2))
        with zipfile.ZipFile(temporary) as archive:
            if archive.testzip():raise RuntimeError('Tệp ZIP không vượt qua kiểm tra CRC.')
        os.chmod(temporary,0o600)
        temporary.rename(destination)
    print('Đã sao lưu và kiểm tra: '+str(destination))
    print('Bao gồm database SQLite, mã nguồn hiện tại, media và tệp cấu hình cục bộ. Giữ bản sao ở nơi riêng tư vì có dữ liệu/tài khoản.')

if __name__=='__main__':
    for stream in (sys.stdout,sys.stderr):
        if hasattr(stream,'reconfigure'):stream.reconfigure(encoding='utf-8')
    try:main()
    except Exception as exc:
        print('CHƯA SAO LƯU THÀNH CÔNG: '+str(exc),file=sys.stderr)
        sys.exit(1)
