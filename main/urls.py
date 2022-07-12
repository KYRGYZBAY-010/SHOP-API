from xml.etree.ElementInclude import include
from .views import ProjectView, ProjectDeteilView, ClientsView, Search, CommentView, LaiksView
from django.urls import path, include


urlpatterns = [
    path('project/', ProjectView.as_view(), name='project'),
    path('clients/', ClientsView.as_view(), name='clients'),
    path('comment/', CommentView.as_view(), name='comment'),
    path('laik_post/', LaiksView.as_view(), name='laiks'),
    path('search/<str:name>/', Search.as_view(), name='search'),
    path('project/<int:id>/',ProjectDeteilView.as_view(), name='deteil' ),
    path('massage/', include('order.urls'))
]