from django.urls import path
from .views import home
from . import views

urlpatterns = [
    path('', home, name='home'),   # gir view home() på "/"
    path('ving/', views.ving_liste, name='ving_liste'),
    path('abonnement/ny/', views.nytt_abonnement, name='nytt_abonnement'),
    path('abonnement/', views.mine_abonnement, name='mine_abonnement'),
    path('abonnement/slett/<int:abo_id>/', views.slett_abonnement, name='slett_abonnement'),
    path('admin/run-sjekk/', views.trigge_sjekk_abonnementer, name='trigge_sjekk_abonnementer'),
    path('ving/nabildet/', views.ving_nåbilde, name='ving_nåbilde'),

]