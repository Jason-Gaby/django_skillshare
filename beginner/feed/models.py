from django.db import models
from sorl.thumbnail import ImageField

class Post(models.Model):
    text = models.CharField(max_length=140, null=False, blank=False)
    image = ImageField()

    def __str__(self):
        return self.text