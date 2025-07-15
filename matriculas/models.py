from django.db import models, transaction
from django.db.models import Max
from django.core.exceptions import ValidationError
from django.urls import reverse
from django.utils import timezone
from django.contrib.auth.models import User

class Ciclo(models.Model):
    nombre = models.CharField(max_length=50, unique=True, verbose_name="Nombre del ciclo")
    fecha_inicio = models.DateField(verbose_name="Fecha de inicio")
    fecha_fin = models.DateField(verbose_name="Fecha de finalización")
    activo = models.BooleanField(default=True, verbose_name="Ciclo activo")
    turnos = models.ManyToManyField('Turno', related_name='ciclos', verbose_name="Turnos disponibles")

    class Meta:
        verbose_name = "Ciclo"
        verbose_name_plural = "Ciclos"
        ordering = ['nombre']

    def __str__(self):
        return self.nombre
    
    def finalizar_ciclo(self):

        with transaction.atomic():
            matriculas_activas = self.matricula_set.filter(estado='activa')
            matriculas_activas.update(estado='finalizada')            
            alumnos_ids = matriculas_activas.values_list('alumno_id', flat=True).distinct()            
            Alumno.objects.filter(id__in=alumnos_ids).update(activo=False)
            
            self.activo = False
            self.save()
            
        return True

    @classmethod
    def verificar_ciclos_finalizados(cls):

        hoy = timezone.now().date()
        ciclos_a_finalizar = cls.objects.filter(
            activo=True,
            fecha_fin__lte=hoy
        )
        for ciclo in ciclos_a_finalizar:
            ciclo.finalizar_ciclo()
            
        return ciclos_a_finalizar.count()

class Turno(models.Model):
    nombre = models.CharField(max_length=50, unique=True, verbose_name="Nombre del turno")

    class Meta:
        verbose_name = "Turno"
        verbose_name_plural = "Turnos"
        ordering = ['nombre']

    def __str__(self):
        return self.nombre

class Horario(models.Model):
    turno = models.ForeignKey(Turno, on_delete=models.CASCADE, related_name='horarios', verbose_name="Turno")
    hora_inicio = models.TimeField(verbose_name="Hora de inicio")
    hora_fin = models.TimeField(verbose_name="Hora de fin")

    class Meta:
        verbose_name = "Horario"
        verbose_name_plural = "Horarios"
        ordering = ['hora_inicio']
        unique_together = ('turno', 'hora_inicio', 'hora_fin')  # evita duplicados

    def __str__(self):
        return f"{self.turno.nombre} - {self.hora_inicio.strftime('%I:%M %p')} a {self.hora_fin.strftime('%I:%M %p')}"

class CodigoManager:
    @staticmethod
    def generar_codigo_alumno(grado_estudios):
        grado_map = {
            'pre': 'RP6',
            '5s': 'RS5',
            '4s': 'RS4',
            '3s': 'RS3',
            '2s': 'RS2',
            '1s': 'RS1',
            '6p': 'EP6',
            '5p': 'EP5'
        }
        
        prefijo = grado_map.get(grado_estudios, 'RSX')
        ultimo_codigo = Alumno.objects.filter(
            codigo__regex=rf'^{prefijo}\d+$'
        ).aggregate(Max('codigo'))['codigo__max']

        numero = int(ultimo_codigo[len(prefijo):]) + 1 if ultimo_codigo else 1
        return f"{prefijo}{numero:03d}"

    @staticmethod
    def generar_codigo_apoderado(codigo_alumno):
        if codigo_alumno.startswith('RP'):
            return f"AP{codigo_alumno[1:]}"
        elif codigo_alumno.startswith(('RS', 'EP')):
            return f"AS{codigo_alumno[2:]}"
        return f"AX{codigo_alumno[1:]}"

    @staticmethod
    def generar_codigo_matricula(codigo_alumno):
        if codigo_alumno.startswith('RP'):
            return f"MP{codigo_alumno[1:]}"
        elif codigo_alumno.startswith(('RS', 'EP')):
            return f"MS{codigo_alumno[2:]}"
        return f"MX{codigo_alumno[1:]}"


class Alumno(models.Model):
    GRADO_OPCIONES = [
        ('5p', '5to de primaria'),
        ('6p', '6to de primaria'),
        ('1s', '1ro de secundaria'),
        ('2s', '2do de secundaria'),
        ('3s', '3ro de secundaria'),
        ('4s', '4to de secundaria'),
        ('5s', '5to de secundaria'),
        ('pre', 'Preuniversitario'),
    ]

    SEXO_OPCIONES = [('M', 'Masculino'), ('F', 'Femenino')]

    codigo = models.CharField(max_length=10, unique=True, blank=True, editable=False)
    grado_estudios = models.CharField(max_length=30, choices=GRADO_OPCIONES)
    nombres_completos = models.CharField(max_length=100)
    dni = models.CharField(max_length=8, unique=True)
    sexo = models.CharField(max_length=1, choices=SEXO_OPCIONES)
    celular_llamadas = models.CharField(max_length=9)
    numero_whatsapp = models.CharField(max_length=9)
    fecha_nacimiento = models.DateField()
    fecha_registro = models.DateTimeField(auto_now_add=True)
    activo = models.BooleanField(default=True)
    colegio_de_procedencia = models.CharField(max_length=100)
    carrera_tentativa = models.CharField(max_length=100)
    foto_previa = models.ImageField(upload_to="alumnos/fotos_previas/", blank=True, null=True)
    foto_frente = models.ImageField(upload_to="alumnos/fotos_frente/", blank=True, null=True)
    foto_corte = models.ImageField(upload_to="alumnos/fotos_corte/", blank=True, null=True)
    sexo_data = models.CharField(max_length=10, choices=[('hija', 'hija'), ('hijo', 'hijo')])

    class Meta:
        verbose_name = "Alumno"
        verbose_name_plural = "Alumnos"
        ordering = ['codigo']

    def save(self, *args, **kwargs):
        if self.pk:
            original = Alumno.objects.get(pk=self.pk)
            if original.grado_estudios != self.grado_estudios:
                self.codigo = CodigoManager.generar_codigo_alumno(self.grado_estudios)
        else:
            if not self.codigo:
                self.codigo = CodigoManager.generar_codigo_alumno(self.grado_estudios)

        if Alumno.objects.filter(codigo=self.codigo).exclude(pk=self.pk).exists():
            raise ValidationError({'codigo': 'Este código ya está en uso'})

        super().save(*args, **kwargs)
        self.actualizar_codigos_relacionados()

    def actualizar_codigos_relacionados(self):
        # No se actualiza el código del apoderado (se mantiene con el primer alumno)
        for matricula in self.matriculas.all():
            nuevo_codigo = CodigoManager.generar_codigo_matricula(self.codigo)
            if matricula.codigo != nuevo_codigo:
                matricula.codigo = nuevo_codigo
                matricula.save()

    def get_absolute_url(self):
        return reverse('alumno_detail', args=[str(self.id)])

    def __str__(self):
        return f"{self.codigo} - {self.nombres_completos}"


class Apoderado(models.Model):
    PARENTESCO_CHOICES = [
        ('Padre', 'Padre'), ('Madre', 'Madre'), ('Hermano', 'Hermano'), ('Hermana', 'Hermana'),
        ('Tio', 'Tío'), ('Tia', 'Tía'), ('Primo', 'Primo'), ('Prima', 'Prima'),
        ('Abuelo', 'Abuelo'), ('Abuela', 'Abuela'),
    ]

    codigo = models.CharField(max_length=10, unique=True, blank=True, editable=False)
    alumnos = models.ManyToManyField(Alumno, related_name='apoderados')
    nombre_completo = models.CharField(max_length=100)
    dni = models.CharField(max_length=8, unique=True)
    celular = models.CharField(max_length=9)
    direccion = models.TextField()
    parentesco = models.CharField(max_length=10, choices=PARENTESCO_CHOICES)
    fecha_registro = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Apoderado"
        verbose_name_plural = "Apoderados"

    def save(self, *args, **kwargs):
        if not self.codigo and self.alumnos.exists():
            primer_alumno = self.alumnos.order_by('fecha_registro').first()
            self.codigo = CodigoManager.generar_codigo_apoderado(primer_alumno.codigo)

        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('apoderado_detail', args=[str(self.id)])

    def __str__(self):
        return f"{self.codigo} - {self.nombre_completo}"

class Matricula(models.Model):
    ESTADO_CHOICES = [
        ('activa', 'Activa'), ('congelada', 'Congelada'), ('finalizada', 'Finalizada'),]
    MODALIDADES = [('presencial', 'Presencial'), ('virtual', 'Virtual'),]
    TIPOS_ALUMNO = [ ('regular', 'REGULAR'), ('promocion', 'PROMOCION'), ('beca50', 'BECA 50%'), ('beca100', 'BECA 100%'), ('fondo_social', 'FONDO SOCIAL'),]

    codigo = models.CharField(max_length=10, unique=True, blank=True, editable=False)
    alumno = models.ForeignKey(Alumno, on_delete=models.CASCADE, related_name='matriculas')
    apoderado = models.ForeignKey(Apoderado, on_delete=models.CASCADE)
    monto = models.DecimalField(max_digits=10, decimal_places=2)
    cuotas = models.IntegerField()
    modalidad = models.CharField(max_length=20, choices=MODALIDADES)
    ciclo = models.ForeignKey(Ciclo, on_delete=models.PROTECT)
    turno = models.ForeignKey(Turno, on_delete=models.PROTECT)
    horario = models.ForeignKey(Horario, on_delete=models.PROTECT)
    fecha_matricula = models.DateField(auto_now_add=True)
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='activa')
    tipo_alumno = models.CharField(max_length=20, choices=TIPOS_ALUMNO, default='regular')
    usuario_registro = models.ForeignKey('auth.User', on_delete=models.PROTECT, related_name='matriculas_registradas')

    class Meta:
        verbose_name = "Matrícula"
        verbose_name_plural = "Matrículas"

    def clean(self):
        if not self.codigo and hasattr(self, 'alumno'):
            self.codigo = CodigoManager.generar_codigo_matricula(self.alumno.codigo)

        if Matricula.objects.filter(codigo=self.codigo).exclude(pk=self.pk).exists():
            raise ValidationError({'codigo': 'Este código ya está en uso'})

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('matricula_detail', args=[str(self.id)])

    def __str__(self):
        return f"{self.codigo} - {self.alumno.nombres_completos}"

    def reactivar_para_nuevo_ciclo(self, nuevo_ciclo, nuevo_turno, nuevo_horario, usuario):
        """
        Reactiva una matrícula para un nuevo ciclo
        """
        if self.estado != 'finalizada':
            raise ValidationError("Solo se pueden reactivar matrículas finalizadas")
        if not nuevo_ciclo.activo:
            raise ValidationError("El nuevo ciclo no está activo")
        if nuevo_turno not in nuevo_ciclo.turnos.all():
            raise ValidationError("El turno seleccionado no está disponible en este ciclo")
        if nuevo_horario.turno != nuevo_turno:
            raise ValidationError("El horario no corresponde al turno seleccionado")
        if not self.alumno.activo:
            self.alumno.activo = True
            self.alumno.save()
            
        nueva_matricula = Matricula.objects.create(
            alumno=self.alumno,
            apoderado=self.apoderado,
            monto=self.monto,
            cuotas=self.cuotas,
            modalidad=self.modalidad,
            ciclo=nuevo_ciclo,
            turno=nuevo_turno,
            horario=nuevo_horario,
            estado='activa',
            tipo_alumno=self.tipo_alumno,
            usuario_registro=usuario
        )
        
        return nueva_matricula
    
class Pago(models.Model):
    ESTADO_PAGO = [
        ('pendiente', 'Pendiente'),
        ('pagado', 'Pagado'),
        ('observado', 'Observado'),
    ]

    TIPO_PAGO = [
        ('cuota', 'Cuota mensual'),
        ('matricula', 'Matrícula'),
        ('otros', 'Otros'),
    ]

    matricula = models.ForeignKey('Matricula', on_delete=models.CASCADE, related_name='pagos')
    numero_cuota = models.IntegerField(null=True, blank=True)
    tipo_pago = models.CharField(max_length=20, choices=TIPO_PAGO)
    monto_programado = models.DecimalField(max_digits=10, decimal_places=2)
    monto_pagado = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    fecha_vencimiento = models.DateField()
    fecha_pago = models.DateField(null=True, blank=True)
    estado = models.CharField(max_length=20, choices=ESTADO_PAGO, default='pendiente')
    observacion = models.TextField(blank=True)
    usuario_registro = models.ForeignKey(User, on_delete=models.PROTECT, related_name='pagos_registrados')
    fecha_registro = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Pago"
        verbose_name_plural = "Pagos"
        ordering = ['fecha_vencimiento']
        unique_together = ('matricula', 'numero_cuota', 'tipo_pago')

    def __str__(self):
        cuota_info = f" - Cuota {self.numero_cuota}" if self.numero_cuota else ""
        return f"{self.matricula.codigo}{cuota_info} - {self.get_estado_display()}"

    def confirmar_pago(self, monto_pagado, usuario, fecha_pago=None):
        self.monto_pagado = monto_pagado
        self.fecha_pago = fecha_pago or timezone.now().date()
        self.estado = 'pagado'
        self.usuario_registro = usuario
        self.save()