from django.db import models


class Day(models.Model):
    day = models.CharField(max_length=9)

    def __str__(self):
        """A string representation of the model."""
        return self.day
