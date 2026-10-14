from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import Q, F
from .validators import normalizar_rut, validar_rut, validar_telefono
from .managers import UsuarioManager

class ConservadoQuerySet(models.QuerySet):
    def delete(self):
        raise ValidationError('Los registros se conservan. Utiliza las operaciones autorizadas del sistema.')

class Usuario(AbstractUser):
    objects = UsuarioManager()
    class Rol(models.TextChoices):
        ADMINISTRADOR = 'ADMINISTRADOR', 'Administrador'
        ENCARGADO = 'ENCARGADO', 'Encargado de hotel'
    rol = models.CharField(max_length=20, choices=Rol.choices, default=Rol.ENCARGADO)
    class Meta:
        verbose_name = 'Usuario'
        constraints = [models.CheckConstraint(condition=Q(rol__in=['ADMINISTRADOR', 'ENCARGADO']), name='usuario_rol_valido')]
    def __str__(self):
        return self.get_full_name() or self.username

class Habitacion(models.Model):
    objects = ConservadoQuerySet.as_manager()
    class Estado(models.TextChoices):
        VACANTE = 'VACANTE', 'Vacante'
        OCUPADA = 'OCUPADA', 'Ocupada'
    class Orientacion(models.TextChoices):
        NORTE = 'NORTE', 'Norte'
        SUR = 'SUR', 'Sur'
        ESTE = 'ESTE', 'Este'
        OESTE = 'OESTE', 'Oeste'
        INTERIOR = 'INTERIOR', 'Interior'
    numero = models.CharField('Número', max_length=10, unique=True)
    capacidad = models.PositiveIntegerField('Capacidad', validators=[MinValueValidator(1)])
    orientacion = models.CharField('Orientación', max_length=10, choices=Orientacion.choices)
    estado = models.CharField(max_length=10, choices=Estado.choices, default=Estado.VACANTE, editable=False)
    activa = models.BooleanField(default=True, editable=False)
    class Meta:
        ordering = ['numero']
        constraints = [models.CheckConstraint(condition=Q(capacidad__gte=1), name='habitacion_capacidad_positiva'),
                       models.CheckConstraint(condition=Q(estado__in=['VACANTE', 'OCUPADA']), name='habitacion_estado_valido'),
                       models.CheckConstraint(condition=Q(activa=True) | Q(estado='VACANTE'), name='habitacion_inactiva_vacante')]
    def clean(self):
        self.numero = self.numero.strip().upper()
        if not self.numero:
            raise ValidationError({'numero': 'Indica el número de habitación.'})
        if self.pk:
            old = Habitacion.objects.get(pk=self.pk)
            if (old.estado == self.Estado.OCUPADA or self.detalles.filter(activa=True).exists()) and old.capacidad != self.capacidad:
                raise ValidationError({'capacidad': 'No puedes cambiar la capacidad de una habitación ocupada.'})
    def save(self, *args, **kwargs):
        self.numero = self.numero.strip().upper()
        if self._state.adding:
            self.estado, self.activa = self.Estado.VACANTE, True
        super().save(*args, **kwargs)
    def delete(self, *args, **kwargs):
        raise ValidationError('Utiliza la eliminación lógica; el historial debe conservarse.')
    def __str__(self):
        return f'Habitación {self.numero}'

class Pasajero(models.Model):
    objects = ConservadoQuerySet.as_manager()
    rut = models.CharField('RUT', max_length=10, unique=True, validators=[validar_rut])
    nombre_completo = models.CharField('Nombre completo', max_length=150)
    telefono = models.CharField('Teléfono', max_length=20, blank=True, validators=[validar_telefono])
    correo = models.EmailField('Correo electrónico', blank=True)
    class Meta:
        ordering = ['nombre_completo']
    def clean(self):
        self.rut = normalizar_rut(self.rut)
        self.nombre_completo = ' '.join(self.nombre_completo.split())
        if not self.nombre_completo:
            raise ValidationError({'nombre_completo': 'Indica el nombre completo.'})
    def save(self, *args, **kwargs):
        self.rut = normalizar_rut(self.rut)
        self.nombre_completo = ' '.join(self.nombre_completo.split())
        super().save(*args, **kwargs)
    def delete(self, *args, **kwargs):
        raise ValidationError('Los pasajeros y sus historiales se conservan.')
    def __str__(self):
        return self.nombre_completo

class HistorialQuerySet(models.QuerySet):
    def delete(self):
        raise ValidationError('El historial no puede eliminarse.')
    def update(self, **kwargs):
        fields = {f.name: f.attname for f in self.model._meta.concrete_fields}
        normalized = {fields.get(key, key) for key in kwargs}
        if normalized & set(self.model.campos_inmutables):
            raise ValidationError('Los datos históricos no pueden modificarse.')
        # Única actualización masiva permitida: cerrar los detalles/estadías.
        if kwargs and not (set(kwargs) == {'activa'} and kwargs['activa'] is False):
            raise ValidationError('Los cambios de estado históricos requieren la operación de salida.')
        return super().update(**kwargs)

class HistorialProtegido(models.Model):
    objects = HistorialQuerySet.as_manager()
    campos_inmutables = ()
    class Meta:
        abstract = True
    def delete(self, *args, **kwargs):
        raise ValidationError('El historial no puede eliminarse.')
    def save(self, *args, **kwargs):
        if self.pk:
            previous = type(self).objects.get(pk=self.pk)
            if any(getattr(previous, f) != getattr(self, f) for f in self.campos_inmutables):
                raise ValidationError('Los datos históricos no pueden modificarse.')
            if hasattr(previous, 'activa') and previous.activa is False and self.activa is True:
                raise ValidationError('Una estadía finalizada no puede reactivarse.')
            if getattr(previous, 'estado', None) == 'FINALIZADA':
                if any(getattr(previous, f.attname) != getattr(self, f.attname) for f in self._meta.concrete_fields):
                    raise ValidationError('Una asignación finalizada no puede modificarse ni reabrirse.')
        super().save(*args, **kwargs)

class Asignacion(HistorialProtegido):
    class Estado(models.TextChoices):
        ACTIVA = 'ACTIVA', 'Activa'
        FINALIZADA = 'FINALIZADA', 'Finalizada'
    responsable = models.ForeignKey(Pasajero, on_delete=models.PROTECT, related_name='asignaciones_responsable')
    responsable_nombre = models.CharField(max_length=150)
    responsable_rut = models.CharField(max_length=10)
    registrada_por = models.ForeignKey(Usuario, on_delete=models.PROTECT, related_name='asignaciones_registradas')
    liberada_por = models.ForeignKey(Usuario, on_delete=models.PROTECT, related_name='asignaciones_liberadas', null=True, blank=True)
    fecha_ingreso = models.DateTimeField(auto_now_add=True)
    fecha_salida = models.DateTimeField(null=True, blank=True)
    costo_total = models.PositiveIntegerField(editable=False)
    estado = models.CharField(max_length=12, choices=Estado.choices, default=Estado.ACTIVA, editable=False)
    campos_inmutables = ('responsable_id', 'responsable_nombre', 'responsable_rut', 'registrada_por_id', 'fecha_ingreso', 'costo_total')
    class Meta:
        ordering = ['-fecha_ingreso']
        constraints = [models.CheckConstraint(condition=Q(costo_total__gte=40000), name='asignacion_costo_positivo'),
                       models.CheckConstraint(condition=(Q(estado='ACTIVA', fecha_salida__isnull=True, liberada_por__isnull=True) | Q(estado='FINALIZADA', fecha_salida__isnull=False, liberada_por__isnull=False)), name='asignacion_cierre_coherente'),
                       models.CheckConstraint(condition=Q(fecha_salida__isnull=True) | Q(fecha_salida__gte=F('fecha_ingreso')), name='asignacion_fechas_coherentes')]
    @property
    def cantidad_pasajeros(self):
        return Hospedaje.objects.filter(detalle__asignacion=self).count()
    def __str__(self):
        return f'Asignación #{self.pk:04d}'

class DetalleHabitacionAsignada(HistorialProtegido):
    asignacion = models.ForeignKey(Asignacion, on_delete=models.PROTECT, related_name='detalles')
    habitacion = models.ForeignKey(Habitacion, on_delete=models.PROTECT, related_name='detalles')
    numero_snapshot = models.CharField(max_length=10)
    capacidad_snapshot = models.PositiveIntegerField()
    activa = models.BooleanField(default=True)
    pasajeros = models.ManyToManyField(Pasajero, through='Hospedaje', related_name='detalles_asignados')
    campos_inmutables = ('asignacion_id', 'habitacion_id', 'numero_snapshot', 'capacidad_snapshot')
    class Meta:
        ordering = ['numero_snapshot']
        constraints = [models.UniqueConstraint(fields=['asignacion', 'habitacion'], name='detalle_habitacion_unica'),
                       models.UniqueConstraint(fields=['habitacion'], condition=Q(activa=True), name='una_asignacion_activa_por_habitacion')]
    @property
    def costo(self):
        return self.capacidad_snapshot * 40000

class Hospedaje(HistorialProtegido):
    detalle = models.ForeignKey(DetalleHabitacionAsignada, on_delete=models.PROTECT, related_name='hospedajes')
    pasajero = models.ForeignKey(Pasajero, on_delete=models.PROTECT, related_name='hospedajes')
    nombre_snapshot = models.CharField(max_length=150)
    rut_snapshot = models.CharField(max_length=10)
    activa = models.BooleanField(default=True)
    campos_inmutables = ('detalle_id', 'pasajero_id', 'nombre_snapshot', 'rut_snapshot')
    class Meta:
        constraints = [models.UniqueConstraint(fields=['detalle', 'pasajero'], name='hospedaje_unico'),
                       models.UniqueConstraint(fields=['pasajero'], condition=Q(activa=True), name='un_hospedaje_activo_por_pasajero')]

class Movimiento(HistorialProtegido):
    usuario = models.ForeignKey(Usuario, on_delete=models.PROTECT, null=True, related_name='movimientos')
    accion = models.CharField(max_length=60)
    descripcion = models.CharField(max_length=255)
    fecha = models.DateTimeField(auto_now_add=True)
    campos_inmutables = ('usuario_id', 'accion', 'descripcion', 'fecha')
    class Meta:
        ordering = ['-fecha']

class LoginIntento(models.Model):
    clave = models.CharField(max_length=64, unique=True)
    fallos = models.PositiveIntegerField(default=0)
    bloqueado_hasta = models.DateTimeField(null=True, blank=True)
