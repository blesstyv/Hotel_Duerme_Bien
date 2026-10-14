"""Registro técnico, sin URL pública. El prototipo utiliza sus paneles por rol."""
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Usuario

@admin.register(Usuario)
class UsuarioAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (('Perfil del hotel', {'fields': ('rol',)}),)
    list_display = ('username', 'first_name', 'last_name', 'rol', 'is_active')
