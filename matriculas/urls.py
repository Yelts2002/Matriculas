from django.urls import path
from . import views
from .views import ficha_matricula_pdf  # asegúrate de importar la vista si no lo has hecho

app_name = 'matriculas'  # Esto define el namespace

urlpatterns = [
    path('', views.dashboard_view, name='home'),
    
    path('dashboard/', views.dashboard_view, name='dashboard'),

    # Alumnos
    path('alumnos/', views.AlumnoListView.as_view(), name='alumno_list'),
    path('alumnos/registrar/', views.AlumnoCreateView.as_view(), name='alumno_create'),
    path('alumnos/<int:pk>/', views.AlumnoDetailView.as_view(), name='alumno_detail'),
    path('alumnos/editar/<int:pk>/', views.AlumnoUpdateView.as_view(), name='alumno_update'),
    path('alumnos/eliminar/<int:pk>/', views.AlumnoDeleteView.as_view(), name='alumno_delete'),
    
    # Apoderados
    path('apoderados/', views.ApoderadoListView.as_view(), name='apoderado_list'),
    path('apoderados/registrar/', views.ApoderadoCreateView.as_view(), name='apoderado_create'),
    path('apoderados/registrar/<int:alumno_id>/', views.AsignarCrearApoderadoView.as_view(), name='asignar_apoderado'),
    path('apoderados/<int:pk>/', views.ApoderadoDetailView.as_view(), name='apoderado_detail'),
    path('apoderados/editar/<int:pk>/', views.ApoderadoUpdateView.as_view(), name='apoderado_update'),
    path('apoderados/eliminar/<int:pk>/', views.ApoderadoDeleteView.as_view(), name='apoderado_delete'),
    path('apoderado/asignar-existente/', views.asignar_apoderado_existente, name='asignar_apoderado_existente'),

    # Matrículas
    path('matriculas/', views.MatriculaListView.as_view(), name='matricula_list'),
    path('matriculas/registrar/', views.MatriculaCreateView.as_view(), name='matricula_create'),
    path('matriculas/registrar/<int:alumno_id>/', views.MatriculaCreateView.as_view(), name='matricula_create_alumno'),
    path('matriculas/<int:pk>/', views.MatriculaDetailView.as_view(), name='matricula_detail'),
    path('matriculas/<int:pk>/editar/', views.MatriculaUpdateView.as_view(), name='matricula_update'),
    path('matriculas/ficha/<int:pk>/pdf/', views.ficha_matricula_pdf, name='ficha_matricula_pdf'),
    path('matriculas/eliminar/<int:pk>/', views.MatriculaDeleteView.as_view(), name='matricula_delete'),

    # Pagos
    path('pagos/matricula/<int:matricula_id>/', views.lista_pagos_matricula, name='lista_pagos_matricula'),
    path('pagos/matricula/<int:matricula_id>/registrar/', views.registrar_pago, name='registrar_pago'),
    path('pagos/editar/<int:pago_id>/', views.editar_pago, name='editar_pago'),
    path('pagos/resumen/', views.resumen_general_pagos, name='resumen_general_pagos'),
    path('ajax/confirmar-pago/<int:pago_id>/', views.confirmar_pago_ajax, name='ajax_confirmar_pago'),

    # AJAX
    path('ajax/apoderado-por-alumno/', views.obtener_apoderado_por_alumno, name='ajax_apoderado_por_alumno'),
    path('ajax/alumnos-por-apoderado/', views.obtener_alumnos_por_apoderado, name='ajax_alumnos_por_apoderado'),
    path('ajax/todos-apoderados/', views.todos_apoderados, name='ajax_todos_apoderados'),
    path('ajax/todos-alumnos/', views.todos_alumnos, name='ajax_todos_alumnos'),
    path('ajax/buscar-alumnos/', views.buscar_alumnos, name='ajax_buscar_alumnos'),
    path('ajax/buscar-apoderados/', views.buscar_apoderados, name='ajax_buscar_apoderados'),

    # Configuración
    path('ciclos/', views.CicloListView.as_view(), name='ciclo_list'),
    path('ciclos/registrar/', views.CicloCreateView.as_view(), name='ciclo_create'),
    path('ciclos/editar/<int:pk>/', views.CicloUpdateView.as_view(), name='ciclo_update'),
    path('turnos/', views.TurnoListView.as_view(), name='turno_list'),
    path('turnos/registrar/', views.TurnoCreateView.as_view(), name='turno_create'),
    path('turnos/editar/<int:pk>/', views.TurnoUpdateView.as_view(), name='turno_update'),
    path('horarios/', views.HorarioListView.as_view(), name='horario_list'),
    path('horarios/registrar/', views.HorarioCreateView.as_view(), name='horario_create'),
    path('horarios/editar/<int:pk>/', views.HorarioUpdateView.as_view(), name='horario_update'),    
]