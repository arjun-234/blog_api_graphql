from django.db import models
from django.contrib.auth.models import User

class Blog(models.Model):
    title = models.CharField(max_length=50)
    date = models.CharField(max_length=30)
    content = models.TextField()
    author = models.ForeignKey(User,on_delete=models.CASCADE)
    likes = models.ManyToManyField(User,related_name='blog_likes')
    unlikes = models.ManyToManyField(User,related_name='blog_unlikes')
    
    def __str__(self):
        return self.title

    def total_likes(self):
        return self.likes.count()

    def total_unlikes(self):
        return self.unlikes.count()


class Comment(models.Model):
    blog = models.ForeignKey(Blog,on_delete=models.CASCADE)
    comment = models.TextField()
    commentor = models.ForeignKey(User,on_delete=models.CASCADE)

    def __str__(self):
        return self.comment



