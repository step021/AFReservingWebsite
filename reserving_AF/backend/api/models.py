from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

# Create your models here.
class Client(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name
    
class UserClientHistoricalData(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='historical_data')
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='historical_data')
    file = models.FileField(upload_to='dataloss/historical_data')
    claims_file = models.FileField(upload_to='dataloss/claims_data', null=True, blank=True)
    reserves_file = models.FileField(upload_to='dataloss/reserves_data', null=True, blank=True)
    upper_bound_update = models.DateField(null=True, blank=True)
    lower_bound_update = models.DateField(null=True, blank=True)

    def __str__(self):
        return f"{self.user.username} - {self.client.name}"
    

class DataLoss(models.Model):
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name="datalosss")
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name="datalosss")
    curr_quarter = models.CharField(max_length=100, default='Q2')
    current_year = models.CharField(max_length=100, default='2021')
    paid_case = models.CharField(max_length=100, default='paid')
    created_at = models.DateTimeField(auto_now_add=True)
    excel_output = models.FileField(upload_to='dataloss/output/', null=True, blank=True)

    def __str__(self):
        return f"{self.client.name} - {self.curr_quarter} {self.current_year}"

# Signal to create historical data for each client when a new user is created
@receiver(post_save, sender=User)
def create_historical_data(sender, instance, created, **kwargs):
    if created:
        clients = ['optima']
        client_files = {
            'optima': 'dataloss/historical_data/Output.xlsx',
        }

        for client_name in clients:
            client, _ = Client.objects.get_or_create(name=client_name)
            UserClientHistoricalData.objects.create(
                user=instance,
                client=client,
                file=client_files[client_name]
            )
