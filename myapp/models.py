from django.db import models

class PDFPageDataItem(models.Model):
    filename = models.CharField(max_length=255)
    page_number = models.IntegerField()
    label_1 = models.BooleanField(default=False)
    label_2 = models.BooleanField(default=False)
    label_3 = models.BooleanField(default=False)
    label_4 = models.BooleanField(default=False)
    label_5 = models.BooleanField(default=False)
    label_6 = models.BooleanField(default=False)
    label_7 = models.BooleanField(default=False)
    label_8 = models.BooleanField(default=False)
    label_9 = models.BooleanField(default=False)
    label_10 = models.BooleanField(default=False)

    class Meta:
        unique_together = ('filename', 'page_number')
        db_table = 'myapp_pdfpagedataitem'  # 指定表名
