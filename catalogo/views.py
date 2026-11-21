from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db import IntegrityError, transaction
from django.db.models import Q, ProtectedError
from django.urls import reverse_lazy
from django.views.generic import (
    ListView,
    DetailView,
    CreateView,
    UpdateView,
    DeleteView,
)
from .forms import ProductoForm, CategoriaForm
from .models import Producto, Categoria


class SoloAdministradorMixin(LoginRequiredMixin, UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_superuser


class GuardadoSeguroMixin:
    def form_valid(self, form):
        try:
            with transaction.atomic():
                response = super().form_valid(form)
        except IntegrityError:
            form.add_error(
                None,
                "No se pudo guardar: otro registro usa esos datos o cambió una relación. Revisá e intentá de nuevo.",
            )
            return self.form_invalid(form)
        messages.success(self.request, "Cambios guardados.")
        return response


class ProductoListView(LoginRequiredMixin, ListView):
    model = Producto
    template_name = "catalogo/lista.html"
    paginate_by = 12

    def get_queryset(self):
        qs = super().get_queryset().select_related("categoria")
        q = self.request.GET.get("q", "").strip()[:100]
        cat = self.request.GET.get("categoria", "").strip()
        if q:
            qs = qs.filter(
                Q(nombre__icontains=q)
                | Q(codigo__icontains=q)
                | Q(origen__icontains=q)
                | Q(presentacion__icontains=q)
            )
        if cat:
            qs = qs.filter(categoria_id=cat)
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["categorias"] = Categoria.objects.all()
        context["categoria_actual"] = self.request.GET.get("categoria", "")
        return context


class ProductoDetailView(LoginRequiredMixin, DetailView):
    model = Producto
    template_name = "catalogo/detalle.html"


class ProductoCreateView(LoginRequiredMixin, GuardadoSeguroMixin, CreateView):
    model = Producto
    form_class = ProductoForm
    template_name = "catalogo/formulario.html"

    def form_valid(self, form):
        form.instance.creado_por = self.request.user
        form.instance.actualizado_por = self.request.user
        return super().form_valid(form)


class ProductoUpdateView(LoginRequiredMixin, GuardadoSeguroMixin, UpdateView):
    model = Producto
    form_class = ProductoForm
    template_name = "catalogo/formulario.html"

    def form_valid(self, form):
        form.instance.actualizado_por = self.request.user
        return super().form_valid(form)


class ProductoDeleteView(SoloAdministradorMixin, DeleteView):
    model = Producto
    template_name = "catalogo/confirmar_baja.html"
    success_url = reverse_lazy("catalogo:lista")

    def form_valid(self, form):
        messages.success(self.request, "Producto eliminado.")
        return super().form_valid(form)


class CategoriaListView(LoginRequiredMixin, ListView):
    model = Categoria
    template_name = "catalogo/categorias.html"
    paginate_by = 20


class CategoriaCreateView(SoloAdministradorMixin, GuardadoSeguroMixin, CreateView):
    model = Categoria
    form_class = CategoriaForm
    template_name = "catalogo/categoria_form.html"
    success_url = reverse_lazy("catalogo:categorias")


class CategoriaUpdateView(SoloAdministradorMixin, GuardadoSeguroMixin, UpdateView):
    model = Categoria
    form_class = CategoriaForm
    template_name = "catalogo/categoria_form.html"
    success_url = reverse_lazy("catalogo:categorias")


class CategoriaDeleteView(SoloAdministradorMixin, DeleteView):
    model = Categoria
    template_name = "catalogo/confirmar_baja.html"
    success_url = reverse_lazy("catalogo:categorias")

    def form_valid(self, form):
        try:
            with transaction.atomic():
                response = super().form_valid(form)
        except ProtectedError:
            form.add_error(
                None,
                "No se puede eliminar una categoría con productos. Reasignalos primero.",
            )
            return self.form_invalid(form)
        messages.success(self.request, "Categoría eliminada.")
        return response
