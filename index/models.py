from django.db import models
import uuid

# Create your models here.
class User(models.Model):
    name = models.CharField('Name', max_length=100)
    email = models.EmailField('Email')
    num = models.CharField('Name', max_length=100)

    def __str__(self):
        return self.name

class Project(models.Model):
    # headline = models.CharField(max_length=100)
    created_at = models.DateTimeField(
            'Criado em', auto_now_add=True
        )
    user = models.ForeignKey(User, on_delete=models.CASCADE)

class Process(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.IntegerField()
    status = models.CharField(max_length=200)