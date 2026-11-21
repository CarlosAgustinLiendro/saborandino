/**
 * Sabor Andino S.R.L. - Sistema de Gestión Web
 * JavaScript Principal: Temas, Modales, Vistas y Utilidades
 */

(function () {
  'use strict';

  // 1. Inicialización de Tema (Modo Claro / Oscuro)
  function inicializarTema() {
    const temaGuardado = localStorage.getItem('sabor_andino_tema');
    const temaPreferido = temaGuardado || (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light');
    aplicarTema(temaPreferido);

    // Sincronizar todos los switches de tema en la página
    document.querySelectorAll('.tema-switch-input').forEach((input) => {
      input.checked = (temaPreferido === 'dark');
      input.addEventListener('change', function () {
        const nuevoTema = this.checked ? 'dark' : 'light';
        aplicarTema(nuevoTema);
        // Sincronizar otros switches si existen
        document.querySelectorAll('.tema-switch-input').forEach((other) => {
          if (other !== input) other.checked = input.checked;
        });
      });
    });
  }

  function aplicarTema(tema) {
    if (tema === 'dark') {
      document.documentElement.setAttribute('data-theme', 'dark');
    } else {
      document.documentElement.removeAttribute('data-theme');
    }
    localStorage.setItem('sabor_andino_tema', tema);

    // Actualizar iconos de tema
    const btnIcon = document.getElementById('icono-tema-btn');
    if (btnIcon) {
      btnIcon.textContent = (tema === 'dark') ? '☀️' : '🌙';
    }
  }

  window.toggleTemaRapido = function () {
    const temaActual = document.documentElement.getAttribute('data-theme') === 'dark' ? 'dark' : 'light';
    const nuevoTema = temaActual === 'dark' ? 'light' : 'dark';
    aplicarTema(nuevoTema);
    document.querySelectorAll('.tema-switch-input').forEach((input) => {
      input.checked = (nuevoTema === 'dark');
    });
  };

  // 2. Sistema de Modales
  window.abrirModal = function (modalId) {
    const modal = document.getElementById(modalId);
    if (!modal) return;
    modal.classList.add('activo');
    modal.setAttribute('aria-hidden', 'false');
    document.body.classList.add('modal-abierto');
  };

  window.cerrarModal = function (modalId) {
    const modal = document.getElementById(modalId);
    if (!modal) return;
    modal.classList.remove('activo');
    modal.setAttribute('aria-hidden', 'true');
    // Verificar si queda algún otro modal abierto
    if (!document.querySelector('.modal-overlay.activo')) {
      document.body.classList.remove('modal-abierto');
    }
  };

  // 3. Modal de Detalle de Producto Dinámico
  window.verDetalleProducto = function (elemento) {
    const dataset = elemento.dataset;
    const modal = document.getElementById('modal-detalle-producto');
    if (!modal) return;

    const elNombre = modal.querySelector('#detalle-nombre');
    const elCategoria = modal.querySelector('#detalle-categoria');
    const elPresentacion = modal.querySelector('#detalle-presentacion');
    const elStock = modal.querySelector('#detalle-stock');
    const elOrigen = modal.querySelector('#detalle-origen');
    const elVencimiento = modal.querySelector('#detalle-vencimiento');
    const elPrecio = modal.querySelector('#detalle-precio');
    const elDescripcion = modal.querySelector('#detalle-descripcion');
    const elImagen = modal.querySelector('#detalle-imagen');
    const elEditarLink = modal.querySelector('#detalle-editar-btn');

    if (elNombre) elNombre.textContent = dataset.nombre || 'Producto';
    if (elCategoria) elCategoria.textContent = dataset.categoria || 'Sin categoría';
    if (elPresentacion) elPresentacion.textContent = dataset.presentacion || 'Estándar';
    if (elStock) elStock.textContent = `${dataset.stock || 0} un.`;
    if (elOrigen) elOrigen.textContent = dataset.origen || 'Valles Calchaquíes (Salta)';
    if (elVencimiento) elVencimiento.textContent = dataset.vencimiento || 'No especificado';
    if (elPrecio) elPrecio.textContent = dataset.precio ? `$ ${dataset.precio}` : '$ 0.00';
    if (elDescripcion) elDescripcion.textContent = dataset.descripcion || 'Sin descripción adicional.';
    if (elImagen && dataset.imagen) elImagen.src = dataset.imagen;
    if (elEditarLink && dataset.urlEditar) elEditarLink.href = dataset.urlEditar;

    abrirModal('modal-detalle-producto');
  };

  // 4. Modal de Confirmación de Eliminación Dinámico
  window.abrirModalEliminar = function (nombre, urlEliminar) {
    const modal = document.getElementById('modal-confirmar-eliminar');
    if (!modal) return;

    const elNombre = modal.querySelector('#eliminar-producto-nombre');
    const elForm = modal.querySelector('#form-confirmar-eliminar');

    if (elNombre) elNombre.textContent = `"${nombre}"`;
    if (elForm && urlEliminar) elForm.action = urlEliminar;

    abrirModal('modal-confirmar-eliminar');
  };

  // 5. Toggle de Visibilidad de Contraseña
  window.togglePassword = function (inputId, btn) {
    const input = document.getElementById(inputId);
    if (!input) return;
    if (input.type === 'password') {
      input.type = 'text';
      btn.setAttribute('aria-label', 'Ocultar contraseña');
      btn.innerHTML = `<svg width="20" height="20" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.88 9.88l-3.29-3.29m7.532 7.532l3.29 3.29M3 3l18 18"/></svg>`;
    } else {
      input.type = 'password';
      btn.setAttribute('aria-label', 'Mostrar contraseña');
      btn.innerHTML = `<svg width="20" height="20" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"/><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"/></svg>`;
    }
  };

  // 6. Selector de Avatar Interactivo
  window.seleccionarAvatar = function (avatarId) {
    const inputHidden = document.getElementById('id_avatar');
    if (inputHidden) {
      inputHidden.value = avatarId;
    }
    document.querySelectorAll('.avatar-opcion').forEach((btn) => {
      if (btn.dataset.avatar === avatarId) {
        btn.classList.add('seleccionado');
      } else {
        btn.classList.remove('seleccionado');
      }
    });
  };

  // 7. Toggle de Vista en Catálogo (Tarjetas / Tabla)
  window.cambiarVistaCatalogo = function (modo) {
    const contTarjetas = document.getElementById('catalogo-vista-tarjetas');
    const contTabla = document.getElementById('catalogo-vista-tabla');
    const btnTarjetas = document.getElementById('btn-vista-tarjetas');
    const btnTabla = document.getElementById('btn-vista-tabla');

    if (!contTarjetas || !contTabla) return;

    if (modo === 'tabla') {
      contTarjetas.style.display = 'none';
      contTabla.style.display = 'block';
      if (btnTabla) btnTabla.classList.add('activo');
      if (btnTarjetas) btnTarjetas.classList.remove('activo');
      localStorage.setItem('sabor_andino_vista_cat', 'tabla');
    } else {
      contTarjetas.style.display = 'grid';
      contTabla.style.display = 'none';
      if (btnTarjetas) btnTarjetas.classList.add('activo');
      if (btnTabla) btnTabla.classList.remove('activo');
      localStorage.setItem('sabor_andino_vista_cat', 'tarjetas');
    }
  };

  // 8. Menú Usuario y Menú Módulos Dropdowns
  window.toggleMenuUsuario = function () {
    const dropdown = document.getElementById('menu-usuario-dropdown');
    if (dropdown) {
      dropdown.classList.toggle('abierto');
    }
    const modulosDropdown = document.getElementById('menu-modulos-dropdown');
    if (modulosDropdown) {
      modulosDropdown.classList.remove('abierto');
    }
  };

  window.toggleMenuModulos = function (e) {
    if (e) e.stopPropagation();
    const dropdown = document.getElementById('menu-modulos-dropdown');
    if (dropdown) {
      dropdown.classList.toggle('abierto');
    }
    const userDropdown = document.getElementById('menu-usuario-dropdown');
    if (userDropdown) {
      userDropdown.classList.remove('abierto');
    }
  };

  // 9. Acordeón de FAQs
  window.toggleFaq = function (elemento) {
    const item = elemento.closest('.faq-item');
    if (item) {
      item.classList.toggle('abierto');
    }
  };

  // Event Listeners Globales al Cargar el DOM
  document.addEventListener('DOMContentLoaded', function () {
    inicializarTema();

    // Restaurar vista de catálogo guardada
    const vistaGuardada = localStorage.getItem('sabor_andino_vista_cat');
    if (vistaGuardada) {
      cambiarVistaCatalogo(vistaGuardada);
    }

    // Cerrar modales con la tecla Escape
    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape') {
        const activo = document.querySelector('.modal-overlay.activo');
        if (activo) {
          activo.classList.remove('activo');
          activo.setAttribute('aria-hidden', 'true');
          document.body.classList.remove('modal-abierto');
        }
        const menuUser = document.getElementById('menu-usuario-dropdown');
        if (menuUser && menuUser.classList.contains('abierto')) {
          menuUser.classList.remove('abierto');
        }
      }
    });

    // Cerrar modal al hacer clic en el backdrop
    document.querySelectorAll('.modal-overlay').forEach((overlay) => {
      overlay.addEventListener('click', function (e) {
        if (e.target === overlay) {
          overlay.classList.remove('activo');
          overlay.setAttribute('aria-hidden', 'true');
          document.body.classList.remove('modal-abierto');
        }
      });
    });

    // Cerrar dropdowns al hacer clic fuera
    document.addEventListener('click', function (e) {
      const capsule = document.getElementById('usuario-capsula');
      const dropdown = document.getElementById('menu-usuario-dropdown');
      if (capsule && dropdown && !capsule.contains(e.target) && !dropdown.contains(e.target)) {
        dropdown.classList.remove('abierto');
      }

      const modulosBtn = document.getElementById('btn-modulos-dropdown');
      const modulosDropdown = document.getElementById('menu-modulos-dropdown');
      if (modulosBtn && modulosDropdown && !modulosBtn.contains(e.target) && !modulosDropdown.contains(e.target)) {
        modulosDropdown.classList.remove('abierto');
      }
    });

    // Previsualización de imagen al cambiar selector en formulario de producto
    const selectImagen = document.querySelector('.selector-imagen');
    const previewImg = document.getElementById('preview-imagen-producto');
    if (selectImagen && previewImg) {
      selectImagen.addEventListener('change', function () {
        previewImg.src = `/static/img/productos/${this.value}`;
      });
    }

    // Auto-cierre de avisos/alertas tras 6 segundos
    document.querySelectorAll('.aviso-toast').forEach((toast) => {
      setTimeout(() => {
        toast.style.opacity = '0';
        setTimeout(() => toast.remove(), 400);
      }, 6000);
    });
  });
})();
