from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import *
from django.urls import reverse_lazy, reverse
from django.contrib import messages
from django.http import HttpResponse, HttpResponseForbidden, JsonResponse
from django.template.loader import get_template
from xhtml2pdf import pisa
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Sum, Q
from django.views import View
from django.contrib.auth.views import LoginView, LogoutView, PasswordChangeView, PasswordChangeDoneView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils.decorators import method_decorator
from .models import CodigoManager
from .forms import *
from django.contrib.admin.views.decorators import staff_member_required
from django.utils import timezone
from django.db import transaction

# Vista para editar el template de WhatsApp
@staff_member_required
def editar_mensaje_whatsapp(request):
    config = MensajeWhatsAppConfig.objects.first()
    if not config:
        config = MensajeWhatsAppConfig.objects.create()
    if request.method == 'POST':
        form = MensajeWhatsAppConfigForm(request.POST, instance=config)
        if form.is_valid():
            form.save()
            messages.success(request, 'Mensaje de WhatsApp actualizado correctamente.')
            return redirect('matriculas:editar_mensaje_whatsapp')
    else:
        form = MensajeWhatsAppConfigForm(instance=config)
    return render(request, 'matriculas/editar_mensaje_whatsapp.html', {'form': form})

@login_required
def dashboard_view(request):
    hoy = timezone.now().date()
    primer_dia_mes = hoy.replace(day=1)
    # Último día del mes actual
    if hoy.month == 12:
        ultimo_dia_mes = hoy.replace(month=12, day=31)
    else:
        import calendar
        last_day = calendar.monthrange(hoy.year, hoy.month)[1]
        ultimo_dia_mes = hoy.replace(day=last_day)

    total_alumnos = Alumno.objects.filter(activo=True).count()
    matriculas_activas = Matricula.objects.filter(estado='activa').count()

    pagos_mes = Pago.objects.filter(
        fecha_pago__range=(primer_dia_mes, hoy),
        estado='pagado'
    ).aggregate(total=Sum('monto_pagado'))['total'] or 0.00

    # Cuotas del mes (todas las cuotas con vencimiento este mes)
    cuotas_mes = Pago.objects.filter(
        fecha_vencimiento__range=(primer_dia_mes, ultimo_dia_mes),
        tipo_pago='cuota'
    )
    total_cuotas_mes = cuotas_mes.count()
    total_cuotas_pendientes_mes = cuotas_mes.filter(estado='pendiente').count()
    total_monto_cuotas_mes = cuotas_mes.aggregate(total=Sum('monto_programado'))['total'] or 0.00
    total_monto_cuotas_pendientes_mes = cuotas_mes.filter(estado='pendiente').aggregate(total=Sum('monto_programado'))['total'] or 0.00

    ciclo_actual = Ciclo.objects.filter(activo=True).order_by('-fecha_inicio').first()
    total_apoderados = Apoderado.objects.count()
    context = {
        'total_alumnos': total_alumnos,
        'matriculas_activas': matriculas_activas,
        'pagos_mes': pagos_mes,
        'total_cuotas_mes': total_cuotas_mes,
        'total_cuotas_pendientes_mes': total_cuotas_pendientes_mes,
        'total_monto_cuotas_mes': total_monto_cuotas_mes,
        'total_monto_cuotas_pendientes_mes': total_monto_cuotas_pendientes_mes,
        'ciclo_actual': ciclo_actual.nombre if ciclo_actual else None,
        'total_apoderados': total_apoderados,
    }
    return render(request, 'home.html', context)

# Vistas para Configuración (Ciclos, Turnos, Horarios)
class CicloListView(LoginRequiredMixin, ListView):
    model = Ciclo
    template_name = 'matriculas/ciclo_list.html'
    context_object_name = 'ciclos'

class CicloCreateView(LoginRequiredMixin, CreateView ):
    model = Ciclo
    form_class = CicloForm
    template_name = 'matriculas/ciclo_form.html'
    success_url = reverse_lazy('matriculas:ciclo_list')

    def form_valid(self, form):
        messages.success(self.request, 'Ciclo creado exitosamente')
        return super().form_valid(form)

class CicloUpdateView(LoginRequiredMixin, UpdateView):
    model = Ciclo
    form_class = CicloForm
    template_name = 'matriculas/ciclo_form.html'
    success_url = reverse_lazy('matriculas:ciclo_list')

    def form_valid(self, form):
        messages.success(self.request, 'Ciclo actualizado exitosamente')
        return super().form_valid(form)

class TurnoListView(LoginRequiredMixin, ListView):
    model = Turno
    template_name = 'matriculas/turno_list.html'
    context_object_name = 'turnos'

class TurnoCreateView(LoginRequiredMixin, CreateView):
    model = Turno
    form_class = TurnoForm
    template_name = 'matriculas/turno_form.html'
    success_url = reverse_lazy('matriculas:turno_list')

    def form_valid(self, form):
        messages.success(self.request, 'Turno creado exitosamente')
        return super().form_valid(form)

class TurnoUpdateView(LoginRequiredMixin, UpdateView):
    model = Turno
    form_class = TurnoForm
    template_name = 'matriculas/turno_form.html'
    success_url = reverse_lazy('matriculas:turno_list')

    def form_valid(self, form):
        messages.success(self.request, 'Turno actualizado exitosamente')
        return super().form_valid(form)

class HorarioListView(LoginRequiredMixin, ListView):
    model = Horario
    template_name = 'matriculas/horario_list.html'
    context_object_name = 'horarios'

    def get_queryset(self):
        queryset = super().get_queryset()
        turno_id = self.request.GET.get('turno')
        if turno_id:
            queryset = queryset.filter(turno_id=turno_id)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['turnos'] = Turno.objects.all()
        return context

class HorarioCreateView(LoginRequiredMixin, CreateView):
    model = Horario
    form_class = HorarioForm
    template_name = 'matriculas/horario_form.html'
    success_url = reverse_lazy('matriculas:horario_list')

    def form_valid(self, form):
        messages.success(self.request, 'Horario creado exitosamente')
        return super().form_valid(form)

class HorarioUpdateView(LoginRequiredMixin, UpdateView):
    model = Horario
    form_class = HorarioForm
    template_name = 'matriculas/horario_form.html'
    success_url = reverse_lazy('matriculas:horario_list')

    def form_valid(self, form):
        messages.success(self.request, 'Horario actualizado exitosamente')
        return super().form_valid(form)

# Vistas para Alumnos
class AlumnoListView(LoginRequiredMixin, ListView):
    model = Alumno
    template_name = 'matriculas/alumno_list.html'
    context_object_name = 'alumnos'
    paginate_by = 20

    def get_queryset(self):
        queryset = super().get_queryset()
        search_query = self.request.GET.get('search')
        if search_query:
            queryset = queryset.filter(
                models.Q(nombres_completos__icontains=search_query) |
                models.Q(dni__icontains=search_query) |
                models.Q(codigo__icontains=search_query)
            )
        return queryset

class AlumnoCreateView(LoginRequiredMixin, CreateView):
    model = Alumno
    form_class = AlumnoForm
    template_name = 'matriculas/alumno_form.html'
    success_url = reverse_lazy('matriculas:alumno_list')

    def form_valid(self, form):
        messages.success(self.request, 'Alumno registrado exitosamente')
        return super().form_valid(form)

class AlumnoUpdateView(LoginRequiredMixin, UpdateView):
    model = Alumno
    form_class = AlumnoForm
    template_name = 'matriculas/alumno_form.html'
    success_url = reverse_lazy('matriculas:alumno_list')

    def form_valid(self, form):
        original = self.get_object()
        if original.grado_estudios != form.cleaned_data['grado_estudios']:
            messages.warning(self.request, "El código del alumno ha sido actualizado por el cambio de grado.")
        messages.success(self.request, "Datos del alumno actualizados exitosamente.")
        return super().form_valid(form)

class AlumnoDetailView(LoginRequiredMixin, DetailView):
    model = Alumno
    template_name = 'matriculas/alumno_detail.html'
    context_object_name = 'alumno'

class AlumnoDeleteView(LoginRequiredMixin, View):
    def post(self, request, pk):
        try:
            alumno = Alumno.objects.get(pk=pk)
            alumno.delete()
            return JsonResponse({'success': True})
        except Alumno.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Alumno no encontrado'}, status=404)

# Vistas para Apoderados
class ApoderadoListView(LoginRequiredMixin, ListView):
    model = Apoderado
    template_name = 'matriculas/apoderado_list.html'
    context_object_name = 'apoderados'
    paginate_by = 20

    def get_queryset(self):
        queryset = super().get_queryset()
        search_query = self.request.GET.get('search')
        if search_query:
            queryset = queryset.filter(
                models.Q(nombre_completo__icontains=search_query) |
                models.Q(dni__icontains=search_query) |
                models.Q(codigo__icontains=search_query)
            )
        return queryset

class ApoderadoCreateView(LoginRequiredMixin, CreateView):
    model = Apoderado
    form_class = ApoderadoForm  # ← Usa el formulario correcto
    template_name = 'matriculas/apoderado_form.html'
    success_url = reverse_lazy('matriculas:apoderado_list')

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        
        alumno_id = self.request.GET.get('alumno_id')
        if alumno_id:
            try:
                alumno = Alumno.objects.get(pk=alumno_id)
                # Incluir al alumno aún si ya tiene apoderado
                form.fields['alumnos'].queryset = Alumno.objects.filter(
                    models.Q(apoderados__isnull=True) | models.Q(pk=alumno.pk)
                ).distinct()
                form.fields['alumnos'].initial = [alumno]
            except Alumno.DoesNotExist:
                pass
        return form

    def form_valid(self, form):
        apoderado = form.save(commit=False)
        alumnos = form.cleaned_data.get('alumnos')

        if not alumnos:
            form.add_error('alumnos', 'Debe seleccionar al menos un alumno')
            return self.form_invalid(form)

        # Generar código con el primer alumno
        primer_alumno = alumnos.first()
        apoderado.codigo = CodigoManager.generar_codigo_apoderado(primer_alumno.codigo)
        apoderado.save()
        form.save_m2m()  # guarda relación many-to-many
        messages.success(self.request, 'Apoderado registrado exitosamente')
        return redirect(self.success_url)

class ApoderadoUpdateView(LoginRequiredMixin, UpdateView):
    model = Apoderado
    form_class = ApoderadoForm
    template_name = 'matriculas/apoderado_form.html'
    success_url = reverse_lazy('matriculas:apoderado_list')

    def form_valid(self, form):
        messages.success(self.request, 'Datos del apoderado actualizados exitosamente')
        return super().form_valid(form)

class ApoderadoDetailView(LoginRequiredMixin, DetailView):
    model = Apoderado
    template_name = 'matriculas/apoderado_detail.html'
    context_object_name = 'apoderado'

class ApoderadoDeleteView(LoginRequiredMixin, DeleteView):
    model = Apoderado
    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.object.delete()
        return JsonResponse({'success': True})

# Vista para asignar apoderado a alumno
class AsignarCrearApoderadoView(LoginRequiredMixin, FormView):
    template_name = 'matriculas/asignar_apoderado.html'
    form_class = ApoderadoAlumnoForm

    def dispatch(self, request, *args, **kwargs):
        self.alumno = get_object_or_404(Alumno, pk=self.kwargs.get('alumno_id'))
        return super().dispatch(request, *args, **kwargs)

    def get_initial(self):
        initial = super().get_initial()
        initial['alumno'] = self.alumno
        return initial

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        search = self.request.GET.get('buscar')
        if search:
            context['resultados'] = Apoderado.objects.filter(dni__icontains=search) | Apoderado.objects.filter(nombre_completo__icontains=search)
        context['alumno'] = self.alumno
        return context

    def form_valid(self, form):
        apoderado = form.save(commit=False)

        # Generar código basado en el alumno si no hay
        if not apoderado.codigo:
            apoderado.codigo = CodigoManager.generar_codigo_apoderado(self.alumno.codigo)

        apoderado.save()  # Guardar primero para que tenga ID

        apoderado.alumnos.add(self.alumno)  # Luego ya puedes usar la relación M2M
        messages.success(self.request, f'Se ha creado y asignado el apoderado {apoderado.nombre_completo}')
        return redirect('matriculas:alumno_detail', pk=self.alumno.pk)
    
    def save(self, *args, **kwargs):
        if not self.pk and hasattr(self, 'alumnos'):
            raise ValueError("No se puede asignar alumnos hasta que el apoderado esté guardado")
        super().save(*args, **kwargs)

@require_POST
@login_required
def asignar_apoderado_existente(request):
    alumno_id = request.POST.get('alumno_id')
    apoderado_id = request.POST.get('apoderado_id')
    alumno = get_object_or_404(Alumno, pk=alumno_id)
    apoderado = get_object_or_404(Apoderado, pk=apoderado_id)
    apoderado.alumnos.add(alumno)
    messages.success(request, f'{apoderado.nombre_completo} asignado a {alumno.nombres_completos}')
    return redirect('matriculas:alumno_detail', pk=alumno.pk)

# Vistas para Matrículas
class MatriculaListView(LoginRequiredMixin, ListView):
    model = Matricula
    template_name = 'matriculas/matricula_list.html'
    context_object_name = 'matriculas'
    paginate_by = 20

    def get_queryset(self):
        queryset = super().get_queryset()
        search_query = self.request.GET.get('search')
        if search_query:
            queryset = queryset.filter(
                models.Q(alumno__nombres_completos__icontains=search_query) |
                models.Q(codigo__icontains=search_query)
            )
        return queryset

class MatriculaCreateView(LoginRequiredMixin, CreateView):
    model = Matricula
    form_class = MatriculaForm
    template_name = 'matriculas/matricula_form.html'
    success_url = reverse_lazy('matriculas:matricula_list')

    def dispatch(self, request, *args, **kwargs):
        self.alumno_id = request.GET.get('alumno_id')
        self.alumno = None
        if self.alumno_id:
            self.alumno = get_object_or_404(Alumno, pk=self.alumno_id)
        return super().dispatch(request, *args, **kwargs)

    def get_initial(self):
        initial = super().get_initial()
        if self.alumno:
            initial['alumno'] = self.alumno
            # Obtener primer apoderado si existe
            apoderado = self.alumno.apoderados.first()
            if apoderado:
                initial['apoderado'] = apoderado
            # Código generado automáticamente
            initial['codigo'] = CodigoManager.generar_codigo_matricula(self.alumno.codigo)
        return initial

    def get_form(self, form_class=None):
        form = super().get_form(form_class)

        # Si el alumno fue pasado, limitar queryset y desactivar campo
        if self.alumno:
            form.fields['alumno'].initial = self.alumno

            apoderado = self.alumno.apoderados.first()
            if apoderado:
                form.fields['apoderado'].initial = apoderado
        return form

    def form_valid(self, form):
        matricula = form.save(commit=False)

        horario = form.cleaned_data.get('horario')
        if horario:
            matricula.turno = horario.turno  # Se asigna automáticamente el turno desde el horario

        matricula.usuario_registro = self.request.user
        matricula.save()

        # === Generar pagos automáticos ===
        monto_total = matricula.monto
        cuotas = matricula.cuotas
        monto_por_cuota = round(monto_total / cuotas, 2)
        fecha_base = timezone.now().date()

        for i in range(1, cuotas + 1):
            fecha_vencimiento = fecha_base + timezone.timedelta(days=30 * (i - 1))
            Pago.objects.create(
                matricula=matricula,
                numero_cuota=i,
                tipo_pago='cuota',
                monto_programado=monto_por_cuota,
                fecha_vencimiento=fecha_vencimiento,
                estado='pendiente',
                usuario_registro=self.request.user
            )

        messages.success(self.request, f'Matrícula "{matricula.codigo}"registrada exitosamente.')
        return redirect('matriculas:matricula_detail', pk=matricula.pk)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.alumno:
            context['alumno'] = self.alumno
        return context

class MatriculaUpdateView(LoginRequiredMixin, UpdateView):
    model = Matricula
    form_class = MatriculaForm
    template_name = 'matriculas/matricula_form.html'
    success_url = reverse_lazy('matriculas:matricula_list')

    def form_valid(self, form):
        matricula = form.save(commit=False)
        
        original_matricula = Matricula.objects.get(pk=matricula.pk)

        monto_cambiado = original_matricula.monto != matricula.monto
        cuotas_cambiadas = original_matricula.cuotas != matricula.cuotas

        with transaction.atomic():
            matricula.save()

            if monto_cambiado or cuotas_cambiadas:
                Pago.objects.filter(matricula=matricula).delete()

                monto_total = matricula.monto
                cuotas = matricula.cuotas
                
                if cuotas > 0:
                    monto_por_cuota = round(monto_total / cuotas, 2)
                else:
                    monto_por_cuota = monto_total

                fecha_base = timezone.now().date()

                for i in range(1, cuotas + 1):
                    fecha_vencimiento = fecha_base + timezone.timedelta(days=30 * (i - 1))
                    Pago.objects.create(
                        matricula=matricula,
                        numero_cuota=i,
                        tipo_pago='cuota',
                        monto_programado=monto_por_cuota,
                        fecha_vencimiento=fecha_vencimiento,
                        estado='pendiente',
                        usuario_registro=self.request.user
                    )
                messages.info(self.request, 'Los pagos de la matrícula han sido recalculados y actualizados.')
            
            messages.success(self.request, 'Matrícula actualizada exitosamente')
            return super().form_valid(form)

class MatriculaDetailView(LoginRequiredMixin, DetailView):
    model = Matricula
    template_name = 'matriculas/matricula_detail.html'
    context_object_name = 'matricula'

class MatriculaDeleteView(LoginRequiredMixin, DeleteView):
    model = Matricula
    success_url = reverse_lazy('matriculas:matricula_list')

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.object.delete()
        return JsonResponse({'success': True})

@login_required
def ficha_matricula_pdf(request, pk):
    matricula = get_object_or_404(Matricula, pk=pk)
    
    template_path = 'matriculas/ficha_matricula_pdf.html'
    context = {'matricula': matricula}
    
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'filename="ficha_matricula_{matricula.codigo}.pdf"'
    
    template = get_template(template_path)
    html = template.render(context)
    
    pisa_status = pisa.CreatePDF(html, dest=response)
    
    if pisa_status.err:
        return HttpResponse('Error al generar el PDF', status=500)
    return response

#AJAX  
@login_required
def obtener_apoderado_por_alumno(request):
    alumno_id = request.GET.get('alumno_id')
    try:
        alumno = Alumno.objects.get(id=alumno_id)
        apoderado = alumno.apoderados.first()
        if apoderado:
            return JsonResponse({
                'id': apoderado.id,
                'nombre': f"{apoderado.codigo} - {apoderado.nombre_completo}"
            })
    except Alumno.DoesNotExist:
        pass
    return JsonResponse({}, status=404)

@login_required
def obtener_alumnos_por_apoderado(request):
    apoderado_id = request.GET.get('apoderado_id')
    try:
        apoderado = Apoderado.objects.get(id=apoderado_id)
        alumnos = apoderado.alumnos.all()
        data = [{
            'id': alumno.id,
            'nombre': f"{alumno.codigo} - {alumno.nombres_completos}"
        } for alumno in alumnos]
        return JsonResponse({'alumnos': data})
    except Apoderado.DoesNotExist:
        return JsonResponse({'alumnos': []})
    
@login_required
def todos_apoderados(request):
    apoderados = Apoderado.objects.all().values('id', 'nombre_completo')
    data = [{'id': a['id'], 'nombre': a['nombre_completo']} for a in apoderados]
    return JsonResponse({'apoderados': data})

@login_required
def todos_alumnos(request):
    alumnos = Alumno.objects.all().values('id', 'nombres_completos')
    data = [{'id': a['id'], 'nombre': a['nombres_completos']} for a in alumnos]
    return JsonResponse({'alumnos': data})

@login_required
def buscar_alumnos(request):
    q = request.GET.get('q', '')
    alumnos = Alumno.objects.filter(nombres_completos__icontains=q)[:20]
    data = [{'id': a.id, 'nombre': a.nombres_completos} for a in alumnos]
    return JsonResponse(data, safe=False)

@login_required
def buscar_apoderados(request):
    q = request.GET.get('q', '')
    apoderados = Apoderado.objects.filter(nombre_completo__icontains=q)[:20]
    data = [{'id': a.id, 'nombre': a.nombre_completo} for a in apoderados]
    return JsonResponse(data, safe=False)

@login_required
def lista_pagos_matricula(request, matricula_id):
    matricula = get_object_or_404(Matricula, id=matricula_id)
    pagos = matricula.pagos.order_by('numero_cuota', 'fecha_vencimiento')
    return render(request, 'matriculas/lista_pagos.html', {'matricula': matricula, 'pagos': pagos})

@login_required
def registrar_pago(request, matricula_id):
    matricula = get_object_or_404(Matricula, id=matricula_id)
    if request.method == 'POST':
        form = PagoForm(request.POST)
        if form.is_valid():
            nuevo_pago = form.save(commit=False)
            nuevo_pago.matricula = matricula
            nuevo_pago.usuario_registro = request.user
            nuevo_pago.save()
            messages.success(request, 'Pago registrado correctamente.')
            return redirect('matriculas:lista_pagos_matricula', matricula_id=matricula.id)
    else:
        form = PagoForm()
    return render(request, 'matriculas/formulario_pago.html', {'form': form, 'matricula': matricula})

@login_required
def editar_pago(request, pago_id):
    pago = get_object_or_404(Pago, id=pago_id)
    if request.method == 'POST':
        form = PagoForm(request.POST, instance=pago)
        if form.is_valid():
            pago_editado = form.save(commit=False)

            # Ajuste adicional:
            if pago_editado.estado == 'pendiente':
                pago_editado.monto_pagado = 0
                pago_editado.fecha_pago = None

            pago_editado.save()
            messages.success(request, 'Pago actualizado correctamente.')
            return redirect('matriculas:lista_pagos_matricula', matricula_id=pago.matricula.id)
    else:
        form = PagoForm(instance=pago)
    return render(request, 'matriculas/formulario_pago.html', {
        'form': form,
        'matricula': pago.matricula
    })

@login_required
def resumen_general_pagos(request):
    matriculas = Matricula.objects.select_related('alumno').annotate(
        total_pagos=Count('pagos'),
        cuotas_pagadas=Count('pagos', filter=Q(pagos__estado='pagado')),
        cuotas_pendientes=Count('pagos', filter=Q(pagos__estado='pendiente')),
        monto_total=Sum('pagos__monto_programado'),
        monto_pagado=Sum('pagos__monto_pagado'),
    )
    return render(request, 'matriculas/lista_general_pagos.html', {'matriculas': matriculas})

@require_POST
@login_required
def confirmar_pago_ajax(request, pago_id):
    pago = get_object_or_404(Pago, id=pago_id, estado='pendiente')
    monto = pago.monto_programado
    fecha_actual = timezone.now().date()

    pago.confirmar_pago(monto_pagado=monto, usuario=request.user, fecha_pago=fecha_actual)

    return JsonResponse({
        'success': True,
        'fecha_pago': fecha_actual.strftime('%Y-%m-%d'),
        'monto_pagado': str(monto),
        'estado': pago.get_estado_display()
    })

#usuarios
class CustomLoginView(LoginView):
    template_name = 'matriculas/login.html'
    redirect_authenticated_user = True

    def get_success_url(self):
        perfil = getattr(self.request.user, 'perfil', None)
        if perfil and perfil.tipo == 'admin':
            return reverse_lazy('matriculas:home')
        return reverse_lazy('matriculas:alumno_list')  

@login_required
def vista_solo_admin(request):
    if request.user.perfil.tipo != 'admin':
        return HttpResponseForbidden("Acceso restringido a administradores.")
    
    return render(request, 'matriculas/admin_view.html')

class CustomLogoutView(LogoutView):
    next_page = reverse_lazy('matriculas:login')

class CustomPasswordChangeView(PasswordChangeView):
    template_name = 'matriculas/password_change_form.html'
    success_url = reverse_lazy('password_change_done')

class CustomPasswordChangeDoneView(PasswordChangeDoneView):
    template_name = 'matriculas/password_change_done.html'

@method_decorator(login_required, name='dispatch')
class UsuarioCreateView(CreateView):
    model = User
    form_class = UsuarioCreateForm
    template_name = 'matriculas/usuario_create.html'

    def form_valid(self, form):
        usuario = form.save(commit=False)
        raw_password = form.cleaned_data.get("password")  # almacena antes de guardar
        usuario.set_password(raw_password)
        usuario.save()
        
        tipo = getattr(usuario.perfil, 'tipo', 'usuario')  # si usas perfil

        messages.success(
            self.request,
            f"✅ Usuario creado con éxito.<br><strong>Usuario:</strong> {usuario.username} <br><strong>Contraseña:</strong> {raw_password} <br><strong>Tipo:</strong> {tipo}"
        )

        # Redirigir a la misma URL para limpiar el formulario (POST-Redirect-GET)
        return redirect(reverse('matriculas:usuario_create'))

@login_required
def cobranza_vencidas_view(request):
    hoy = timezone.now().date()
    # Cuotas vencidas y no pagadas
    cuotas_vencidas = Pago.objects.filter(
        fecha_vencimiento__lt=hoy,
        estado='pendiente',
        tipo_pago='cuota'
    ).select_related('matricula__alumno', 'matricula__apoderado')

    # Agrupar por apoderado para reportes
    apoderados = {}
    for cuota in cuotas_vencidas:
        apoderado = cuota.matricula.apoderado
        if apoderado:
            if apoderado.id not in apoderados:
                apoderados[apoderado.id] = {
                    'apoderado': apoderado,
                    'cuotas': []
                }
            apoderados[apoderado.id]['cuotas'].append(cuota)

    context = {
        'cuotas_vencidas': cuotas_vencidas,
        'apoderados': apoderados.values(),
    }
    return render(request, 'matriculas/cobranzas_vencidas.html', context)

@login_required
def enviar_recordatorio_cobranza(request, apoderado_id):
    apoderado = get_object_or_404(Apoderado, id=apoderado_id)
    cuota = Pago.objects.filter(
        matricula__apoderado=apoderado,
        estado='pendiente',
        fecha_vencimiento__lt=timezone.now().date(),
        tipo_pago='cuota'
    ).order_by('fecha_vencimiento').first()
    if not cuota:
        messages.info(request, 'No hay cuotas vencidas para este apoderado.')
        return redirect('matriculas:cobranzas_vencidas')
    # Redirigir al enlace de WhatsApp generado
    return redirect(cuota.get_whatsapp_url())