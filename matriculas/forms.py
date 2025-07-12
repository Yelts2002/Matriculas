from django import forms
from django.core.exceptions import ValidationError
from django.db import models
from .models import *

class CicloForm(forms.ModelForm):
    class Meta:
        model = Ciclo
        fields = ['nombre', 'fecha_inicio', 'fecha_fin', 'activo', 'turnos']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'fecha_inicio': forms.DateInput(
                attrs={'type': 'date', 'class': 'form-control'},
                format='%Y-%m-%d'
            ),
            'fecha_fin': forms.DateInput(
                attrs={'type': 'date', 'class': 'form-control'},
                format='%Y-%m-%d'
            ),
            'turnos': forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'}),
            'activo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        labels = {
            'activo': 'Ciclo activo (disponible para matrículas)'
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Asegurar el formato de fecha
        self.fields['fecha_inicio'].input_formats = ['%Y-%m-%d']
        self.fields['fecha_fin'].input_formats = ['%Y-%m-%d']

    def clean(self):
        cleaned_data = super().clean()
        fecha_inicio = cleaned_data.get('fecha_inicio')
        fecha_fin = cleaned_data.get('fecha_fin')
        
        if fecha_inicio and fecha_fin:
            if fecha_inicio > fecha_fin:
                raise ValidationError("La fecha de inicio no puede ser posterior a la fecha de fin")
            
            # Verificar superposición con otros ciclos activos
            ciclos_solapados = Ciclo.objects.filter(
                activo=True,
                fecha_inicio__lte=fecha_fin,
                fecha_fin__gte=fecha_inicio
            ).exclude(pk=self.instance.pk if self.instance else None)
            
            if ciclos_solapados.exists():
                raise ValidationError("Existe un ciclo activo que se solapa con estas fechas")
        
        return cleaned_data
    
class TurnoForm(forms.ModelForm):
    class Meta:
        model = Turno
        fields = ['nombre']
        widgets = {
            'nombre': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ejemplo: Mañana, Tarde'
            }),
        }

class HorarioForm(forms.ModelForm):
    class Meta:
        model = Horario
        fields = ['turno', 'hora_inicio', 'hora_fin']
        widgets = {
            'turno': forms.Select(attrs={'class': 'form-select'}),
            'hora_inicio': forms.TimeInput(
                format='%H:%M',
                attrs={
                    'type': 'time',
                    'class': 'form-control'
                }
            ),
            'hora_fin': forms.TimeInput(
                format='%H:%M',
                attrs={
                    'type': 'time',
                    'class': 'form-control'
                }
            ),
        }
    
    def clean(self):
        cleaned_data = super().clean()
        hora_inicio = cleaned_data.get('hora_inicio')
        hora_fin = cleaned_data.get('hora_fin')
        
        if hora_inicio and hora_fin and hora_inicio >= hora_fin:
            raise ValidationError("La hora de inicio debe ser anterior a la hora de fin")

class AlumnoForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Establecer el formato de fecha en el campo
        self.fields['fecha_nacimiento'].widget.format = '%Y-%m-%d'
        self.fields['fecha_nacimiento'].input_formats = ['%Y-%m-%d']

    class Meta:
        model = Alumno
        fields = [
            'grado_estudios', 'nombres_completos', 'dni', 'sexo', 
            'celular_llamadas', 'numero_whatsapp', 'fecha_nacimiento',
            'colegio_de_procedencia', 'carrera_tentativa', 'sexo_data',
            'foto_previa', 'foto_frente', 'foto_corte'
        ]
        widgets = {
            'grado_estudios': forms.Select(attrs={'class': 'form-select'}),
            'nombres_completos': forms.TextInput(attrs={'class': 'form-control'}),
            'dni': forms.TextInput(attrs={
                'class': 'form-control',
                'maxlength': '8',
                'pattern': r'\d{8}',
                'title': 'Ingrese 8 dígitos numéricos'
            }),
            'celular_llamadas': forms.TextInput(attrs={
                'class': 'form-control',
                'maxlength': '9',
                'pattern': r'\d{9}',
                'title': 'Ingrese 9 dígitos numéricos'
            }),
            'numero_whatsapp': forms.TextInput(attrs={
                'class': 'form-control',
                'maxlength': '9',
                'pattern': r'\d{9}',
                'title': 'Ingrese 9 dígitos numéricos'
            }),
            'fecha_nacimiento': forms.DateInput(attrs={
                'type': 'date',
                'class': 'form-control'
            }),
            'colegio_de_procedencia': forms.TextInput(attrs={'class': 'form-control'}),
            'carrera_tentativa': forms.TextInput(attrs={'class': 'form-control'}),
            'sexo_data': forms.Select(attrs={'class': 'form-select'}),
            'foto_previa': forms.FileInput(attrs={'class': 'form-control'}),
            'foto_frente': forms.FileInput(attrs={'class': 'form-control'}),
            'foto_corte': forms.FileInput(attrs={'class': 'form-control'}),
        }
    
    def clean_dni(self):
        dni = self.cleaned_data['dni']
        if not dni.isdigit() or len(dni) != 8:
            raise ValidationError("El DNI debe tener exactamente 8 dígitos numéricos")
        return dni
    
    def clean_celular_llamadas(self):
        celular = self.cleaned_data['celular_llamadas']
        if not celular.isdigit() or len(celular) != 9:
            raise ValidationError("El celular debe tener exactamente 9 dígitos numéricos")
        return celular
    
    def clean_numero_whatsapp(self):
        whatsapp = self.cleaned_data['numero_whatsapp']
        if not whatsapp.isdigit() or len(whatsapp) != 9:
            raise ValidationError("El número de WhatsApp debe tener exactamente 9 dígitos numéricos")
        return whatsapp

class ApoderadoForm(forms.ModelForm):
    alumnos = forms.ModelMultipleChoiceField(
        queryset=Alumno.objects.none(),
        label='Alumnos a cargo',
        widget=forms.SelectMultiple(attrs={
            'class': 'form-select select2-multiple',
            'data-placeholder': 'Seleccione los alumnos'
        }),
        required=True
    )

    class Meta:
        model = Apoderado
        fields = ['nombre_completo', 'dni', 'celular', 'direccion', 'parentesco', 'alumnos']
        widgets = {
            'nombre_completo': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nombres y apellidos completos'
            }),
            'dni': forms.TextInput(attrs={
                'class': 'form-control',
                'maxlength': '8',
                'pattern': r'\d{8}',
                'title': 'Ingrese 8 dígitos numéricos'
            }),
            'celular': forms.TextInput(attrs={
                'class': 'form-control',
                'maxlength': '9',
                'pattern': r'\d{9}',
                'title': 'Ingrese 9 dígitos numéricos'
            }),
            'direccion': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Dirección completa'
            }),
            'parentesco': forms.Select(attrs={'class': 'form-select'}),
        }
        labels = {
            'parentesco': 'Parentesco con el/los alumno(s)'
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Filtrar alumnos sin apoderado o que ya están asignados a este apoderado
        if self.instance.pk:
            alumnos_actuales = self.instance.alumnos.all()
            self.fields['alumnos'].queryset = Alumno.objects.filter(
                models.Q(apoderados__isnull=True) | 
                models.Q(pk__in=alumnos_actuales)
            ).distinct()
            self.fields['alumnos'].initial = alumnos_actuales
        else:
            self.fields['alumnos'].queryset = Alumno.objects.filter(apoderados__isnull=True)
    
    def clean_dni(self):
        dni = self.cleaned_data['dni']
        if not dni.isdigit() or len(dni) != 8:
            raise ValidationError("El DNI debe tener exactamente 8 dígitos numéricos")
        return dni
    
    def clean_celular(self):
        celular = self.cleaned_data['celular']
        if not celular.isdigit() or len(celular) != 9:
            raise ValidationError("El celular debe tener exactamente 9 dígitos numéricos")
        return celular

class ApoderadoAlumnoForm(forms.ModelForm):
    alumno = forms.ModelChoiceField(
        queryset=Alumno.objects.all(),
        widget=forms.HiddenInput(),
        required=False
    )

    class Meta:
        model = Apoderado
        fields = ['nombre_completo', 'dni', 'celular', 'direccion', 'parentesco', 'alumno']
        widgets = {
            'direccion': forms.Textarea(attrs={'rows': 3}),
        }

    def clean(self):
        cleaned_data = super().clean()
        alumno = cleaned_data.get('alumno')

        if not alumno:
            raise forms.ValidationError("No se recibió un alumno válido para asociar.")

class MatriculaForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Configurar querysets iniciales
        self.fields['alumno'].queryset = Alumno.objects.filter(activo=True)
        self.fields['apoderado'].queryset = Apoderado.objects.all()
        self.fields['ciclo'].queryset = Ciclo.objects.filter(activo=True)
        self.fields['turno'].queryset = Turno.objects.all()
        self.fields['horario'].queryset = Horario.objects.none()
        
        # Si es una instancia existente, configurar los valores
        if self.instance.pk:
            self.fields['horario'].queryset = Horario.objects.filter(turno=self.instance.turno)
        
        # Si hay datos en el POST, configurar dinámicamente
        if 'turno' in self.data:
            try:
                turno_id = int(self.data.get('turno'))
                self.fields['horario'].queryset = Horario.objects.filter(turno_id=turno_id)
            except (ValueError, TypeError):
                pass

    class Meta:
        model = Matricula
        fields = ['alumno', 'apoderado', 'monto', 'cuotas', 'modalidad', 'ciclo', 'turno', 'horario', 'estado', 'tipo_alumno']
        widgets = {
            'alumno': forms.Select(attrs={
                'class': 'form-select select2',
                'data-placeholder': 'Seleccione un alumno'
            }),
            'apoderado': forms.Select(attrs={
                'class': 'form-select select2',
                'data-placeholder': 'Seleccione un apoderado'
            }),
            'monto': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0'
            }),
            'cuotas': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1',
                'max': '12'
            }),
            'modalidad': forms.Select(attrs={'class': 'form-select'}),
            'ciclo': forms.Select(attrs={'class': 'form-select'}),
            'turno': forms.Select(attrs={
                'class': 'form-select',
                'onchange': 'updateHorarios()'
            }),
            'horario': forms.Select(attrs={'class': 'form-select'}),
            'estado': forms.Select(attrs={'class': 'form-select'}),
            'tipo_alumno': forms.Select(attrs={'class': 'form-select'}),
        }
        labels = {
            'monto': 'Monto total (S/)',
            'cuotas': 'Número de cuotas'
        }
    
    def clean(self):
        cleaned_data = super().clean()
        alumno = cleaned_data.get('alumno')
        ciclo = cleaned_data.get('ciclo')
        
        # Verificar que el alumno no esté ya matriculado en este ciclo
        if alumno and ciclo:
            matriculas_existentes = Matricula.objects.filter(
                alumno=alumno,
                ciclo=ciclo,
                estado__in=['activa', 'congelada']
            ).exclude(pk=self.instance.pk if self.instance else None)
            
            if matriculas_existentes.exists():
                raise ValidationError(
                    f"Este alumno ya tiene una matrícula {matriculas_existentes.first().get_estado_display().lower()} "
                    f"para el ciclo {ciclo.nombre}"
                )
        
        # Validar que el horario pertenezca al turno seleccionado
        turno = cleaned_data.get('turno')
        horario = cleaned_data.get('horario')
        
        if turno and horario and horario.turno != turno:
            raise ValidationError("El horario seleccionado no corresponde al turno elegido")

class ReactivarMatriculaForm(forms.Form):
    nuevo_ciclo = forms.ModelChoiceField(
        queryset=Ciclo.objects.filter(activo=True),
        label="Nuevo Ciclo",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    nuevo_turno = forms.ModelChoiceField(
        queryset=Turno.objects.all(),
        label="Turno",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    nuevo_horario = forms.ModelChoiceField(
        queryset=Horario.objects.none(),
        label="Horario",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    actualizar_monto = forms.DecimalField(
        required=False,
        label="Nuevo Monto (opcional)",
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )
    actualizar_cuotas = forms.IntegerField(
        required=False,
        label="Nuevo N° de Cuotas (opcional)",
        min_value=1,
        max_value=12,
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        if 'nuevo_turno' in self.data:
            try:
                turno_id = int(self.data.get('nuevo_turno'))
                self.fields['nuevo_horario'].queryset = Horario.objects.filter(turno_id=turno_id)
            except (ValueError, TypeError):
                pass

class PagoForm(forms.ModelForm):
    class Meta:
        model = Pago
        fields = [
            'numero_cuota', 'tipo_pago', 'monto_programado',
            'monto_pagado', 'fecha_vencimiento', 'fecha_pago',
            'estado', 'observacion'
        ]
        widgets = {
            'fecha_vencimiento': forms.DateInput(attrs={'type': 'date'}),
            'fecha_pago': forms.DateInput(attrs={'type': 'date'}),
            'observacion': forms.Textarea(attrs={'rows': 2}),
        }