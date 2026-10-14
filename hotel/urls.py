from django.urls import path

from . import views

app_name = "hotel"

urlpatterns = [
    path("", views.inicio, name="inicio"),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("administracion/", views.dashboard_admin, name="dashboard_admin"),
    path("administracion/encargados/", views.encargado_list, name="encargado_list"),
    path("administracion/encargados/nuevo/", views.encargado_crear, name="encargado_crear"),
    path("administracion/encargados/<int:pk>/editar/", views.encargado_editar, name="encargado_editar"),
    path("administracion/encargados/<int:pk>/estado/", views.encargado_estado, name="encargado_estado"),
    path("hotel/", views.dashboard_encargado, name="dashboard_encargado"),
    path("habitaciones/", views.habitacion_list, name="habitacion_list"),
    path("habitaciones/nueva/", views.habitacion_crear, name="habitacion_crear"),
    path("habitaciones/<int:pk>/editar/", views.habitacion_editar, name="habitacion_editar"),
    path("habitaciones/<int:pk>/eliminar/", views.habitacion_eliminar, name="habitacion_eliminar"),
    path("habitaciones/<int:pk>/historial/", views.habitacion_historial, name="habitacion_historial"),
    path("pasajeros/", views.pasajero_list, name="pasajero_list"),
    path("pasajeros/nuevo/", views.pasajero_crear, name="pasajero_crear"),
    path("pasajeros/<int:pk>/editar/", views.pasajero_editar, name="pasajero_editar"),
    path("pasajeros/<int:pk>/historial/", views.pasajero_historial, name="pasajero_historial"),
    path("asignaciones/", views.asignacion_list, name="asignacion_list"),
    path("asignaciones/nueva/", views.asignacion_crear, name="asignacion_crear"),
    path("asignaciones/<int:pk>/", views.asignacion_detalle, name="asignacion_detalle"),
    path("asignaciones/<int:pk>/salida/", views.asignacion_liberar, name="asignacion_liberar"),
    path("ocupacion/", views.ocupacion, name="ocupacion"),
    path("historiales/", views.historiales, name="historiales"),
]
