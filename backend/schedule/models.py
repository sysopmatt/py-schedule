from django.db import models

from tv_show.models import TvShow
from day.models import Day


class Schedule(models.Model):
    title = models.CharField(max_length=200)
    show = models.ForeignKey(TvShow, on_delete=models.CASCADE)
    thread = models.CharField(max_length=200)
    time = models.TimeField(auto_now=False, auto_now_add=False, default='12:00')
    day = models.ForeignKey(Day, models.SET_NULL, null=True)

    def __str__(self):
        """A string representation of the model."""
        return self.title
