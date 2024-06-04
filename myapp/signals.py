# from django.db.models.signals import post_migrate
# from django.dispatch import receiver
# from django.db import connection
# from .models import PDFPageDataItem

# @receiver(post_migrate)
# def clear_pdf_data(sender, **kwargs):
#     # 检查表是否存在
#     with connection.cursor() as cursor:
#         cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=%s", [PDFPageDataItem._meta.db_table])
#         if cursor.fetchone():
#             PDFPageDataItem.objects.all().delete()

