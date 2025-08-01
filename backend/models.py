from django.db import models

# Create your models here.
from django.contrib.auth.models import AbstractUser

class CustomUser(AbstractUser):
    fullname = models.CharField(max_length=255, null=True, blank=True) 
    username = models.CharField(max_length=255, unique=True, blank=False, null=False)
    title = models.TextField(null=True, blank=True)
    email = models.EmailField(unique=True) 
    created_at = models.DateTimeField(auto_now_add=True,blank=False,null=False)



class Currency(models.Model):
    name = models.CharField(max_length=50)
    symbol = models.CharField(max_length=10, unique=True)
    is_crypto = models.BooleanField(default=True)
    active = models.BooleanField(default=True)
    
class Balances(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=20, decimal_places=8, default=0)
    currency =models.ForeignKey(Currency, on_delete=models.CASCADE)
    
    class Meta:
        unique_together = ('user', 'currency')
        
