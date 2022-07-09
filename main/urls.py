from xml.etree.ElementInclude import include
from .views import ProjectView, ProjectDeteilView
from django.urls import path, include


urlpatterns = [
    path('home/', ProjectView.as_view(), name='home'),
    path('project/<int:id>/',ProjectDeteilView.as_view(), name='deteil' ),
    path('massage/', include('order.urls'))
]