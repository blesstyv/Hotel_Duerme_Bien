from django.contrib.auth.models import UserManager

class UsuarioManager(UserManager):
    def create_superuser(self, username, email=None, password=None, **extra_fields):
        extra_fields.setdefault('rol', 'ADMINISTRADOR')
        if extra_fields['rol'] != 'ADMINISTRADOR':
            raise ValueError('La cuenta técnica inicial debe tener el rol Administrador.')
        return super().create_superuser(username, email, password, **extra_fields)
