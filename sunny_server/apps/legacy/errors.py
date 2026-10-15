from django.http import JsonResponse
from django.shortcuts import render

def csrf_failure(request, reason=''):
    message = 'Không xác thực được yêu cầu. Hãy tải lại trang và đăng nhập lại nếu cần. Nếu vẫn lỗi, kiểm tra cấu hình domain HTTPS (CSRF_TRUSTED_ORIGINS).'
    if request.path.startswith('/api/'):
        return JsonResponse({'code':'csrf_failed','error':message},status=403)
    return render(request,'csrf_error.html',{'message':message},status=403)
