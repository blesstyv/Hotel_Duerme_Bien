from django.urls import include, path

urlpatterns = [path('', include('hotel.urls'))]
# No se expone /admin/: los roles operan exclusivamente en las vistas autorizadas.
handler403 = 'hotel.views.error_403'
handler404 = 'hotel.views.error_404'
handler500 = 'hotel.views.error_500'
