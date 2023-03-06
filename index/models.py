from django.db import models

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