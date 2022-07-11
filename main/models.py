from django.db import models


class Project(models.Model):
    img = models.ImageField(upload_to='project-img', null = True, blank = True)
    img_1 = models.ImageField(upload_to='project-img', null = True, blank = True)
    img_2 = models.ImageField(upload_to='project-img', null = True, blank = True)
    img_3 = models.ImageField(upload_to='project-img', null = True, blank = True)
    title = models.CharField('Название', max_length=50)
    txt = models.TextField('Описание')
    site = models.URLField('Веб сайт', null=True)
    insta = models.URLField('Инстаграм', null=True)
    title2 =  models.CharField('Заголовок', max_length=30, null=True)
    date = models.DateTimeField('Дата и время публикации')

    def __str__(self):
        return self.title


    class Meta:
        verbose_name = 'Проекты'
        verbose_name_plural = 'Наши проекты'


class Clients(models.Model):
    title = models.CharField('Наши клиенты', max_length=50)
    icon = models.ImageField(null = True, blank = True)
    url = models.URLField(null = True)
    date = models.DateTimeField('Дата и время', null = True)

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = 'Клиенты'
        verbose_name_plural = 'Наши клиенты'
    

class Search(models.Model):
    name = models.CharField(max_length=30) 