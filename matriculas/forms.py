# Formulario para editar el template de WhatsApp
from django import forms
from django.core.exceptions import ValidationError
from .models import MensajeWhatsAppConfig, Ciclo, Turno, Horario, Alumno, Apoderado, Matricula, Pago, Perfil, User
from django.db import models

class MensajeWhatsAppConfigForm(forms.ModelForm):
    class Meta:
        model = MensajeWhatsAppConfig
        fields = ['nombre', 'template', 'activo']
        widgets = {
            'template': forms.Textarea(attrs={'rows': 5, 'class': 'form-control'}),
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'activo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

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
    DIAS_SEMANA = Horario.DIAS_SEMANA

    dias_bloque1 = forms.MultipleChoiceField(
        choices=DIAS_SEMANA,
        widget=forms.CheckboxSelectMultiple(attrs={
            'class': 'form-checkbox text-blue-600 rounded focus:ring focus:ring-blue-300'
        }),
        label="Días (Bloque 1)"
    )

    dias_bloque2 = forms.MultipleChoiceField(
        choices=DIAS_SEMANA,
        required=False,
        widget=forms.CheckboxSelectMultiple(attrs={
            'class': 'form-checkbox text-blue-600 rounded focus:ring focus:ring-blue-300'
        }),
        label="Días (Bloque 2)"
    )

    class Meta:
        model = Horario
        fields = [
            'nombre',
            'hora_inicio1', 'hora_fin1', 'dias_bloque1',
            'hora_inicio2', 'hora_fin2', 'dias_bloque2'
        ]
        widgets = {
            'nombre': forms.TextInput(attrs={
                'class': 'w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring focus:ring-blue-200',
                'placeholder': 'Ej: Turno Mañana, Grupo Intensivo'
            }),
            'hora_inicio1': forms.TimeInput(format='%H:%M', attrs={
                'type': 'time',
                'class': 'w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring focus:ring-blue-200',
            }),
            'hora_fin1': forms.TimeInput(format='%H:%M', attrs={
                'type': 'time',
                'class': 'w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring focus:ring-blue-200',
            }),
            'hora_inicio2': forms.TimeInput(format='%H:%M', attrs={
                'type': 'time',
                'class': 'w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring focus:ring-blue-200',
            }),
            'hora_fin2': forms.TimeInput(format='%H:%M', attrs={
                'type': 'time',
                'class': 'w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring focus:ring-blue-200',
            }),
        }

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.dias_bloque1 = ','.join(self.cleaned_data.get('dias_bloque1', []))
        instance.dias_bloque2 = ','.join(self.cleaned_data.get('dias_bloque2', []))
        if commit:
            instance.save()
        return instance


class AlumnoForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Establecer el formato de fecha en el campo
        self.fields['fecha_nacimiento'].widget.format = '%Y-%m-%d'
        self.fields['fecha_nacimiento'].input_formats = ['%Y-%m-%d']
        self.fields['fecha_nacimiento'].required = False
        # Hacer campos no obligatorios
        self.fields['colegio_de_procedencia'].required = False
        self.fields['carrera_tentativa'].required = False
        self.fields['foto_previa'].required = False
        self.fields['foto_frente'].required = False
        self.fields['foto_corte'].required = False
        self.fields['sexo_data'].required = False
        self.fields['direccion_alumno'].required = False
        
    class Meta:
        model = Alumno
        fields = [
            'nombres_completos', 'dni', 'grado_estudios', 'sexo', 
            'celular_llamadas', 'numero_whatsapp', 'fecha_nacimiento',
            'colegio_de_procedencia', 'carrera_tentativa', 'sexo_data',
            'foto_previa', 'foto_frente', 'foto_corte', 'direccion_alumno'
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
            'foto_previa': forms.FileInput(attrs={'class': 'form-control'}),
            'foto_frente': forms.FileInput(attrs={'class': 'form-control'}),
            'foto_corte': forms.FileInput(attrs={'class': 'form-control'}),
            'direccion_alumno': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Dirección completa'
            }),
        }
    
    def clean_genero(self):
        cleaned_data = super().clean()
        sexo = cleaned_data.get('sexo')
        
        # Automáticamente establecer sexo_data basado en sexo
        if sexo == 'M':
            cleaned_data['sexo_data'] = 'hijo'
        elif sexo == 'F':
            cleaned_data['sexo_data'] = 'hija'
        
        return cleaned_data
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
        self.fields['direccion'].required = False

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
        
        self.fields['alumno'].queryset = Alumno.objects.filter(activo=True)
        self.fields['apoderado'].queryset = Apoderado.objects.all()
        self.fields['ciclo'].queryset = Ciclo.objects.filter(activo=True)
        self.fields['turno'].queryset = Turno.objects.all()
        self.fields['horario'].queryset = Horario.objects.all()

    class Meta:
        model = Matricula
        fields = ['alumno', 'apoderado','modalidad', 'ciclo', 'turno', 'horario', 'estado', 'tipo_matricula', 'tipo_alumno']
        widgets = {
            'alumno': forms.Select(attrs={
                'class': 'form-select select2',
                'data-placeholder': 'Seleccione un alumno'
            }),
            'apoderado': forms.Select(attrs={
                'class': 'form-select select2',
                'data-placeholder': 'Seleccione un apoderado'
            }),

            'modalidad': forms.Select(attrs={'class': 'form-select'}),
            'ciclo': forms.Select(attrs={'class': 'form-select'}),
            'turno': forms.Select(attrs={'class': 'form-select'}),
            'horario': forms.Select(attrs={'class': 'form-select'}),
            'estado': forms.Select(attrs={'class': 'form-select'}),
            'tipo_matricula': forms.Select(attrs={'class': 'form-select'}),
            'tipo_alumno': forms.Select(attrs={'class': 'form-select'}),
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

class MontoCuotasForm(forms.Form):
    cuotas = forms.IntegerField(
        min_value=1,
        max_value=6,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'id': 'id_cuotas',
            'onchange': 'actualizarCamposCuotas()'
        })
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        num_cuotas = self.data.get('cuotas', 1) if self.data else self.initial.get('cuotas', 1)

        try:
            num_cuotas = int(num_cuotas)
        except ValueError:
            num_cuotas = 1

        for i in range(1, num_cuotas + 1):
            field_monto = f'monto_cuota_{i}'
            field_fecha = f'fecha_cuota_{i}'

            self.fields[field_monto] = forms.DecimalField(
                label=f'Monto Cuota {i}',
                max_digits=10,
                decimal_places=2,
                widget=forms.NumberInput(attrs={
                    'class': 'form-control monto-cuota',
                    'step': '0.01',
                    'oninput': 'calcularTotal()'
                })
            )
            if field_monto in self.initial:
                self.fields[field_monto].initial = self.initial[field_monto]

            self.fields[field_fecha] = forms.DateField(
                label=f'Fecha Vencimiento Cuota {i}',
                widget=forms.DateInput(attrs={
                    'class': 'form-control',
                    'type': 'date',
                })
            )
            if field_fecha in self.initial:
                self.fields[field_fecha].initial = self.initial[field_fecha]

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
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({
                'class': 'w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500'
            })
            self.fields['foto_comprobante'].required = False

    class Meta:
        model = Pago
        fields = [
            'numero_cuota', 'tipo_pago', 'monto_programado',
            'monto_pagado', 'fecha_vencimiento', 'fecha_pago',
            'estado', 'observacion', 'forma_pago', 'foto_comprobante'
        ]
        
        widgets = {
            'fecha_vencimiento': forms.DateInput(attrs={'type': 'date'}),
            'fecha_pago': forms.DateInput(attrs={'type': 'date'}),
            'observacion': forms.Textarea(attrs={'rows': 2}),
            'foto_comprobante': forms.FileInput(attrs={'class': 'form-control'}),
        }

class UsuarioCreateForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control'}))
    tipo = forms.ChoiceField(choices=Perfil.TIPO_USUARIO_CHOICES, widget=forms.Select(attrs={'class': 'form-select'}))

    class Meta:
        model = User
        fields = ['username', 'password', 'tipo']

        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'password': forms.PasswordInput(attrs={'class': 'form-input w-full'}),
            'tipo': forms.Select(attrs={'class': 'form-select w-full'}),
    }

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password'])
        if commit:
            user.save()
            Perfil.objects.filter(user=user).update(tipo=self.cleaned_data['tipo'])
        return user