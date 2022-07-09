from django.db import models


class Project(models.Model):
    img = models.ImageField(upload_to='project-img', null = True, blank = True)
    title = models.CharField('Название', max_length=50)
    txt = models.TextField('Описание')
    date = models.DateTimeField('Дата и время публикации')

    def __str__(self):
        return self.title


    class Meta:
        verbose_name = 'Проекты'
        verbose_name_plural = 'Наши проекты'


class OrderProject(models.Model):
    pass