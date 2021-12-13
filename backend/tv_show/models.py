from django.db import models


class TvShow(models.Model):
    title = models.CharField(max_length=200)
    subreddit = models.CharField(max_length=200)
    thetvdb_id = models.CharField(max_length=6)
    imdb_id = models.CharField(max_length=10)
    footer = models.TextField()

    def __str__(self):
        """A string representation of the model."""
        return self.title
