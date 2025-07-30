from django.db import models

# Create your models here.

class MasterSupp(models.Model):
    # Primary key is automatically created with an auto-incrementing integer if not specified
    id = models.AutoField(primary_key=True)
    campaign_id = models.CharField(max_length=255, default="NA")
    campaign_name = models.CharField(max_length=255, default="NA")
    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255)
    company = models.CharField(max_length=255)
    domain = models.CharField(max_length=255)
    email_address = models.CharField(max_length=255)
    industry = models.CharField(max_length=255)
    number_of_employees = models.CharField(max_length=255)
    job_title = models.CharField(max_length=255)
    phone = models.CharField(max_length=100)
    country = models.CharField(max_length=255)

    def __str__(self):
        return f'{self.first_name} {self.last_name} - {self.company}'


