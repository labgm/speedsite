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

class Processament(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    priority = models.IntegerField(default=1)
    position = models.IntegerField(default=1)
    status = models.CharField(max_length=20)
    submition_date = models.DateTimeField(auto_now_add=True)
    output = models.TextField(blank=True)

    def __str__(self):
        return self.nome

class Process(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.IntegerField()
    status = models.CharField(max_length=200)