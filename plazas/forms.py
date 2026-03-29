# ============================================================
# FORMS.PY — App Plazas (Capa 6: Validación)
# Valida los datos de entrada para crear y actualizar plazas.
# ============================================================

from django import forms
from .models import PlazaInternado


class PlazaInternadoForm(forms.ModelForm):
    """
    Formulario para crear y actualizar plazas de internado.
    El view instancia este form con request.data antes
    de delegar al controller.
    """

    class Meta:
        model  = PlazaInternado
        fields = [
            'codigo', 'institucion', 'area',
            'ciudad', 'direccion', 'estado', 'periodo',
        ]

    def clean_codigo(self):
        """
        Valida que el código tenga el formato correcto.
        Formato esperado: PLAZA-AAAA-NNN (ej: PLAZA-2024-001)
        """
        codigo = self.cleaned_data.get('codigo', '').strip().upper()
        if not codigo:
            raise forms.ValidationError('El código de la plaza es obligatorio.')
        if len(codigo) < 5:
            raise forms.ValidationError(
                'El código de la plaza debe tener al menos 5 caracteres.'
            )
        return codigo

    def clean_periodo(self):
        """Valida el formato del período académico."""
        periodo = self.cleaned_data.get('periodo', '').strip()
        if '-' not in periodo:
            raise forms.ValidationError(
                'El formato del período no es válido. Use el formato: AAAA-N (ej: 2024-1).'
            )
        partes = periodo.split('-')
        if len(partes) != 2 or not partes[0].isdigit() or len(partes[0]) != 4:
            raise forms.ValidationError(
                'Formato inválido. Ejemplo correcto: 2024-1'
            )
        return periodo

    def clean(self):
        """Validación cruzada: la plaza disponible no puede tener estado cancelada."""
        cleaned = super().clean()
        estado = cleaned.get('estado')
        if estado == 'cancelada':
            raise forms.ValidationError(
                'No se puede crear una plaza con estado "cancelada" directamente. '
                'Créela como "disponible" y luego cámbiela de estado si es necesario.'
            )
        return cleaned


class ActualizarEstadoPlazaForm(forms.Form):
    """
    Formulario para actualizar únicamente el estado de una plaza.
    Usado en el endpoint PATCH de estado.
    """
    estado = forms.ChoiceField(
        choices=PlazaInternado.ESTADO_OPCIONES,
        error_messages={
            'required':       'El campo "estado" es obligatorio.',
            'invalid_choice': 'Estado inválido. Opciones: disponible, ocupada, reservada, cancelada.',
        }
    )
    observaciones = forms.CharField(
        required=False,
        max_length=500,
        help_text='Motivo del cambio de estado (opcional).'
    )
