from django.urls import path
from .views import home
from . import views

urlpatterns = [
    path('', home, name='home'),   # gir view home() på "/"
    path('ving/historikk', views.ving_historikk, name='ving_historikk'),
    path('abonnement/ny/', views.nytt_abonnement, name='nytt_abonnement'),
    path('abonnement/', views.mine_abonnement, name='mine_abonnement'),
    path('abonnement/slett/<int:abo_id>/', views.slett_abonnement, name='slett_abonnement'),
    path('admin/run-sjekk/', views.trigge_sjekk_abonnementer, name='trigge_sjekk_abonnementer'),
    path('ving/aktiv/', views.ving_aktiv, name='ving_aktiv'),

]