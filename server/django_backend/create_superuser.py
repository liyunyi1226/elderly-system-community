import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'django_backend.settings')
django.setup()

from django.contrib.auth.models import User

def create_superuser():
    username = 'admin'
    password = 'admin123456'
    email = 'admin@example.com'
    
    if not User.objects.filter(username=username).exists():
        User.objects.create_superuser(
            username=username,
            email=email,
            password=password
        )
        print(f"超级用户创建成功！")
        print(f"用户名: {username}")
        print(f"密码: {password}")
    else:
        print(f"用户 {username} 已存在")

if __name__ == '__main__':
    create_superuser()
