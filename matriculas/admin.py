from django.contrib import admin
from django.db import models
from django.db.models import Q
from django import forms
from django.core.exceptions import ValidationError
from .models import *

class CicloForm(forms.ModelForm):
    fecha_inicio = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}))
    fecha_fin = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}))
    
    class Meta:
        model = Ciclo
        fields = ['nombre', 'turnos', 'fecha_inicio', 'fecha_fin', 'activo']
        widgets = {
            'turnos': forms.CheckboxSelectMultiple(),
        }
    
    def clean(self):
        cleaned_data = super().clean()
        fecha_inicio = cleaned_data.get('fecha_inicio')
        fecha_fin = cleaned_data.get('fecha_fin')
        
        if fecha_inicio and fecha_fin and fecha_inicio > fecha_fin:
            raise ValidationError("La fecha de inicio no puede ser posterior a la fecha de fin")

@admin.register(Alumno)
class AlumnoAdmin(admin.ModelAdmin):
    list_display = ('codigo', 'nombres_completos', 'grado_estudios', 'dni', 'sexo', 'activo')
    search_fields = ('codigo', 'nombres_completos', 'dni', 'colegio_de_procedencia', 'carrera_tentativa')
    list_filter = ('grado_estudios', 'sexo', 'activo')
    readonly_fields = ('codigo', 'fecha_registro')
    ordering = ('codigo',)
    fieldsets = (
        ("Datos Generales", {
            'fields': ('codigo', 'nombres_completos', 'dni', 'sexo', 'sexo_data', 'grado_estudios', 'fecha_nacimiento', 'activo')
        }),
        ("Contacto", {
            'fields': ('celular_llamadas', 'numero_whatsapp')
        }),
        ("Procedencia y Carrera", {
            'fields': ('colegio_de_procedencia', 'carrera_tentativa')
        }),
        ("Fotos", {
            'fields': ('foto_previa', 'foto_frente', 'foto_corte')
        }),
        ("Fechas", {
            'fields': ('fecha_registro',)
        }),
    )
    actions = ['activar_alumnos', 'desactivar_alumnos']
    
    def activar_alumnos(self, request, queryset):
        updated = queryset.update(activo=True)
        self.message_user(request, f"{updated} alumnos activados correctamente")
    activar_alumnos.short_description = "Activar alumnos seleccionados"
    
    def desactivar_alumnos(self, request, queryset):
        updated = queryset.update(activo=False)
        self.message_user(request, f"{updated} alumnos desactivados correctamente")
    desactivar_alumnos.short_description = "Desactivar alumnos seleccionados"

@admin.register(Apoderado)
class ApoderadoAdmin(admin.ModelAdmin):
    list_display = ('codigo', 'nombre_completo', 'mostrar_alumnos', 'dni', 'celular', 'parentesco', 'fecha_registro')
    search_fields = ('codigo', 'nombre_completo', 'dni', 'alumnos__codigo', 'alumnos__nombres_completos')
    list_filter = ('parentesco', 'fecha_registro')
    readonly_fields = ('codigo', 'fecha_registro')
    ordering = ('-fecha_registro',)
    filter_horizontal = ('alumnos',)
    date_hierarchy = 'fecha_registro'

    def mostrar_alumnos(self, obj):
        return ", ".join([alumno.codigo for alumno in obj.alumnos.all()])
    
    mostrar_alumnos.short_description = "Alumnos"

@admin.register(Ciclo)
class CicloAdmin(admin.ModelAdmin):
    form = CicloForm
    list_display = ('nombre', 'fecha_inicio', 'fecha_fin', 'activo', 'mostrar_turnos')
    filter_horizontal = ('turnos',)
    search_fields = ('nombre',)
    list_filter = ('activo',)
    ordering = ('-fecha_inicio', 'nombre')
    actions = ['finalizar_ciclos', 'activar_ciclos']
    
    def mostrar_turnos(self, obj):
        return ", ".join([turno.nombre for turno in obj.turnos.all()])
    mostrar_turnos.short_description = "Turnos"
    
    def finalizar_ciclos(self, request, queryset):
        for ciclo in queryset:
            ciclo.finalizar_ciclo()
        self.message_user(request, f"{queryset.count()} ciclos finalizados correctamente")
    finalizar_ciclos.short_description = "Finalizar ciclos seleccionados"
    
    def activar_ciclos(self, request, queryset):
        updated = queryset.update(activo=True)
        self.message_user(request, f"{updated} ciclos activados correctamente")
    activar_ciclos.short_description = "Activar ciclos seleccionados"

@admin.register(Turno)
class TurnoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'mostrar_horarios', 'mostrar_ciclos')
    search_fields = ('nombre',)
    ordering = ('nombre',)
    filter_horizontal = ('ciclos',)
    
    def mostrar_horarios(self, obj):
        return obj.horarios.count()
    mostrar_horarios.short_description = "Horarios"
    
    def mostrar_ciclos(self, obj):
        return obj.ciclos.count()
    mostrar_ciclos.short_description = "Ciclos Activos"

@admin.register(Horario)
class HorarioAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'turno', 'hora_inicio', 'hora_fin', 'mostrar_ciclos')
    list_filter = ('turno',)
    ordering = ('turno', 'hora_inicio')
    search_fields = ('turno__nombre',)
    
    def mostrar_ciclos(self, obj):
        return obj.turno.ciclos.count()
    mostrar_ciclos.short_description = "Ciclos Activos"

@admin.register(Matricula)
class MatriculaAdmin(admin.ModelAdmin):
    list_display = (
        'codigo', 'alumno_link', 'apoderado_link', 'ciclo', 'turno', 'horario', 
        'modalidad', 'estado', 'monto', 'cuotas', 'fecha_matricula'
    )
    search_fields = (
        'codigo', 'alumno__nombres_completos', 'alumno__dni',
        'apoderado__nombre_completo', 'apoderado__dni'
    )
    list_filter = ('estado', 'modalidad', 'ciclo', 'turno', 'horario')
    readonly_fields = ('codigo', 'fecha_matricula')
    ordering = ('-fecha_matricula',)
    list_select_related = ('alumno', 'apoderado', 'ciclo', 'turno', 'horario')
    actions = ['marcar_como_finalizadas', 'marcar_como_activas']
    date_hierarchy = 'fecha_matricula'
    
    def alumno_link(self, obj):
        from django.utils.html import format_html
        return format_html('<a href="{}">{}</a>', 
                         f'/admin/colegio/alumno/{obj.alumno.id}/change/',
                         obj.alumno)
    alumno_link.short_description = 'Alumno'
    alumno_link.admin_order_field = 'alumno__nombres_completos'
    
    def apoderado_link(self, obj):
        from django.utils.html import format_html
        return format_html('<a href="{}">{}</a>', 
                         f'/admin/colegio/apoderado/{obj.apoderado.id}/change/',
                         obj.apoderado)
    apoderado_link.short_description = 'Apoderado'
    apoderado_link.admin_order_field = 'apoderado__nombre_completo'
    
    def marcar_como_finalizadas(self, request, queryset):
        updated = queryset.update(estado='finalizada')
        self.message_user(request, f"{updated} matrículas marcadas como finalizadas")
    marcar_como_finalizadas.short_description = "Marcar como finalizadas"
    
    def marcar_como_activas(self, request, queryset):
        updated = queryset.update(estado='activa')
        self.message_user(request, f"{updated} matrículas marcadas como activas")
    marcar_como_activas.short_description = "Marcar como activas"
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'alumno', 'apoderado', 'ciclo', 'turno', 'horario'
        )