from django import forms
from django.core.exceptions import ValidationError
from .models import *

class CicloForm(forms.ModelForm):
    class Meta:
        model = Ciclo
        fields = ['nombre', 'turnos']
        widgets = {
            'turnos': forms.CheckboxSelectMultiple(),
        }

class TurnoForm(forms.ModelForm):
    class Meta:
        model = Turno
        fields = ['nombre']

class HorarioForm(forms.ModelForm):
    class Meta:
        model = Horario
        fields = ['turno', 'hora_inicio', 'hora_fin']
        widgets = {
            'hora_inicio': forms.TimeInput(format='%H:%M', attrs={'type': 'time'}),
            'hora_fin': forms.TimeInput(format='%H:%M', attrs={'type': 'time'}),
        }

class AlumnoForm(forms.ModelForm):
    class Meta:
        model = Alumno
        fields = [
            'grado_estudios', 'nombres_completos', 'dni', 'sexo', 
            'celular_llamadas', 'numero_whatsapp', 'fecha_nacimiento',
            'colegio_de_procedencia', 'carrera_tentativa', 'sexo_data',
            'foto_previa', 'foto_frente', 'foto_corte'
        ]
        widgets = {
            'fecha_nacimiento': forms.DateInput(attrs={'type': 'date'}),
        }

class ApoderadoForm(forms.ModelForm):
    alumnos = forms.ModelMultipleChoiceField(
        queryset=Alumno.objects.none(),  # Se setea dinámicamente
        label='Alumnos sin apoderado',
        widget=forms.SelectMultiple(attrs={
            'class': 'form-select select2',
            'style': 'width: 100%;'
        }),
        help_text='Seleccione a los alumnos.',
        required=True
    )

    class Meta:
        model = Apoderado
        fields = ['nombre_completo', 'dni', 'celular', 'direccion', 'parentesco', 'alumnos']
        widgets = {
            'nombre_completo': forms.TextInput(attrs={'class': 'form-control'}),
            'dni': forms.TextInput(attrs={'class': 'form-control', 'maxlength': 8}),
            'celular': forms.TextInput(attrs={'class': 'form-control', 'maxlength': 9}),
            'direccion': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'parentesco': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Modo edición: incluir alumnos actuales del apoderado
        if self.instance.pk:
            alumnos_actuales = self.instance.alumnos.all()
            self.fields['alumnos'].queryset = Alumno.objects.filter(models.Q(apoderados__isnull=True) | models.Q(pk__in=alumnos_actuales)
            ).distinct()
            self.fields['alumnos'].initial = alumnos_actuales
        else:
            # Modo creación: solo alumnos sin apoderado
            self.fields['alumnos'].queryset = Alumno.objects.filter(apoderados__isnull=True)



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
    class Meta:
        model = Matricula
        fields = [
            'alumno', 'apoderado', 'monto', 'cuotas', 'modalidad',
            'ciclo', 'horario'
        ]
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Mostrar todos los horarios
        self.fields['horario'].queryset = Horario.objects.all()

        # Si hay instancia cargada o datos POST, puedes precargar el valor seleccionado
        if 'alumno' in self.data:
            try:
                alumno_id = int(self.data.get('alumno'))
                self.fields['alumno'].queryset = Alumno.objects.filter(id=alumno_id)
            except (ValueError, TypeError):
                pass
        elif self.instance.pk and self.instance.alumno:
            self.fields['alumno'].queryset = Alumno.objects.filter(id=self.instance.alumno.id)

        if 'apoderado' in self.data:
            try:
                apoderado_id = int(self.data.get('apoderado'))
                self.fields['apoderado'].queryset = Apoderado.objects.filter(id=apoderado_id)
            except (ValueError, TypeError):
                pass
        elif self.instance.pk and self.instance.apoderado:
            self.fields['apoderado'].queryset = Apoderado.objects.filter(id=self.instance.apoderado.id)

