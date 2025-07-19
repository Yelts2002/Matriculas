from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, CreateView, UpdateView, DetailView, DeleteView, FormView
from django.urls import reverse_lazy
from django.contrib import messages
from django.http import HttpResponse
from django.template.loader import get_template
from xhtml2pdf import pisa
from io import BytesIO
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Sum, Q
from django.views import View

from .models import *
from .forms import *

def home(request):
    return render(request, 'home.html') 

# Vistas para Configuración (Ciclos, Turnos, Horarios)
class CicloListView(ListView):
    model = Ciclo
    template_name = 'matriculas/ciclo_list.html'
    context_object_name = 'ciclos'

class CicloCreateView(CreateView):
    model = Ciclo
    form_class = CicloForm
    template_name = 'matriculas/ciclo_form.html'
    success_url = reverse_lazy('matriculas:ciclo_list')

    def form_valid(self, form):
        messages.success(self.request, 'Ciclo creado exitosamente')
        return super().form_valid(form)

class CicloUpdateView(UpdateView):
    model = Ciclo
    form_class = CicloForm
    template_name = 'matriculas/ciclo_form.html'
    success_url = reverse_lazy('matriculas:ciclo_list')

    def form_valid(self, form):
        messages.success(self.request, 'Ciclo actualizado exitosamente')
        return super().form_valid(form)

class TurnoListView(ListView):
    model = Turno
    template_name = 'matriculas/turno_list.html'
    context_object_name = 'turnos'

class TurnoCreateView(CreateView):
    model = Turno
    form_class = TurnoForm
    template_name = 'matriculas/turno_form.html'
    success_url = reverse_lazy('matriculas:turno_list')

    def form_valid(self, form):
        messages.success(self.request, 'Turno creado exitosamente')
        return super().form_valid(form)

class TurnoUpdateView(UpdateView):
    model = Turno
    form_class = TurnoForm
    template_name = 'matriculas/turno_form.html'
    success_url = reverse_lazy('matriculas:turno_list')

    def form_valid(self, form):
        messages.success(self.request, 'Turno actualizado exitosamente')
        return super().form_valid(form)

class HorarioListView(ListView):
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

class HorarioCreateView(CreateView):
    model = Horario
    form_class = HorarioForm
    template_name = 'matriculas/horario_form.html'
    success_url = reverse_lazy('matriculas:horario_list')

    def form_valid(self, form):
        messages.success(self.request, 'Horario creado exitosamente')
        return super().form_valid(form)

class HorarioUpdateView(UpdateView):
    model = Horario
    form_class = HorarioForm
    template_name = 'matriculas/horario_form.html'
    success_url = reverse_lazy('matriculas:horario_list')

    def form_valid(self, form):
        messages.success(self.request, 'Horario actualizado exitosamente')
        return super().form_valid(form)

# Vistas para Alumnos
class AlumnoListView(ListView):
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

class AlumnoCreateView(CreateView):
    model = Alumno
    form_class = AlumnoForm
    template_name = 'matriculas/alumno_form.html'
    success_url = reverse_lazy('matriculas:alumno_list')

    def form_valid(self, form):
        messages.success(self.request, 'Alumno registrado exitosamente')
        return super().form_valid(form)

class AlumnoUpdateView(UpdateView):
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

class AlumnoDetailView(DetailView):
    model = Alumno
    template_name = 'matriculas/alumno_detail.html'
    context_object_name = 'alumno'

class AlumnoDeleteView(View):
    def post(self, request, pk):
        try:
            alumno = Alumno.objects.get(pk=pk)
            alumno.delete()
            return JsonResponse({'success': True})
        except Alumno.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Alumno no encontrado'}, status=404)

# Vistas para Apoderados
class ApoderadoListView(ListView):
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

class ApoderadoCreateView(CreateView):
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


class ApoderadoUpdateView(UpdateView):
    model = Apoderado
    form_class = ApoderadoForm
    template_name = 'matriculas/apoderado_form.html'
    success_url = reverse_lazy('matriculas:apoderado_list')

    def form_valid(self, form):
        messages.success(self.request, 'Datos del apoderado actualizados exitosamente')
        return super().form_valid(form)

class ApoderadoDetailView(DetailView):
    model = Apoderado
    template_name = 'matriculas/apoderado_detail.html'
    context_object_name = 'apoderado'

class ApoderadoDeleteView(DeleteView):
    model = Apoderado
    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.object.delete()
        return JsonResponse({'success': True})

# Vista para asignar apoderado a alumno
class AsignarCrearApoderadoView(FormView):
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
def asignar_apoderado_existente(request):
    alumno_id = request.POST.get('alumno_id')
    apoderado_id = request.POST.get('apoderado_id')
    alumno = get_object_or_404(Alumno, pk=alumno_id)
    apoderado = get_object_or_404(Apoderado, pk=apoderado_id)
    apoderado.alumnos.add(alumno)
    messages.success(request, f'{apoderado.nombre_completo} asignado a {alumno.nombres_completos}')
    return redirect('matriculas:alumno_detail', pk=alumno.pk)

# Vistas para Matrículas
class MatriculaListView(ListView):
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

class MatriculaCreateView(CreateView):
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

        messages.success(self.request, 'Matrícula registrada exitosamente')
        return redirect('matriculas:matricula_detail', pk=matricula.pk)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.alumno:
            context['alumno'] = self.alumno
        return context

class MatriculaUpdateView(UpdateView):
    model = Matricula
    form_class = MatriculaForm
    template_name = 'matriculas/matricula_form.html'
    success_url = reverse_lazy('matriculas:matricula_list')

    def form_valid(self, form):
        messages.success(self.request, 'Matrícula actualizada exitosamente')
        return super().form_valid(form)

class MatriculaDetailView(DetailView):
    model = Matricula
    template_name = 'matriculas/matricula_detail.html'
    context_object_name = 'matricula'

from django.http import JsonResponse

class MatriculaDeleteView(DeleteView):
    model = Matricula
    success_url = reverse_lazy('matriculas:matricula_list')

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.object.delete()
        return JsonResponse({'success': True})

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
    
def todos_apoderados(request):
    apoderados = Apoderado.objects.all().values('id', 'nombre_completo')
    data = [{'id': a['id'], 'nombre': a['nombre_completo']} for a in apoderados]
    return JsonResponse({'apoderados': data})

def todos_alumnos(request):
    alumnos = Alumno.objects.all().values('id', 'nombres_completos')
    data = [{'id': a['id'], 'nombre': a['nombres_completos']} for a in alumnos]
    return JsonResponse({'alumnos': data})

def buscar_alumnos(request):
    q = request.GET.get('q', '')
    alumnos = Alumno.objects.filter(nombres_completos__icontains=q)[:20]
    data = [{'id': a.id, 'nombre': a.nombres_completos} for a in alumnos]
    return JsonResponse(data, safe=False)

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
            form.save()
            messages.success(request, 'Pago actualizado correctamente.')
            return redirect('matriculas:lista_pagos_matricula', matricula_id=pago.matricula.id)
    else:
        form = PagoForm(instance=pago)
    return render(request, 'matriculas/formulario_pago.html', {'form': form, 'matricula': pago.matricula})

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