# ============================================================
# FORMS.PY — App Ranking (Capa 6: Validación)
# Valida los datos de entrada del endpoint de asignación
# antes de que el controller los procese.
# ============================================================

from django import forms


class AsignarPlazasForm(forms.Form):
    """
    Formulario para el endpoint POST /api/v1/ranking/asignar/
    Valida que el período venga en el formato correcto.
    """
    periodo = forms.CharField(
        max_length=20,
        min_length=3,
        error_messages={
            'required':  'El campo "periodo" es obligatorio.',
            'max_length': 'El período no puede superar los 20 caracteres.',
            'min_length': 'El período debe tener al menos 3 caracteres.',
        }
    )

    def clean_periodo(self):
        """
        Valida que el período tenga el formato esperado.
        Formatos válidos: 2024-1, 2024-2, 2025-1, etc.
        """
        periodo = self.cleaned_data.get('periodo', '').strip()

        # Verificar que no esté vacío después de limpiar espacios
        if not periodo:
            raise forms.ValidationError('El período no puede estar vacío.')

        # Verificar formato básico: debe contener un guión
        if '-' not in periodo:
            raise forms.ValidationError(
                'El formato del período no es válido. Use el formato: AAAA-N (ej: 2024-1).'
            )

        partes = periodo.split('-')
        if len(partes) != 2:
            raise forms.ValidationError(
                'El formato del período no es válido. Use el formato: AAAA-N (ej: 2024-1).'
            )

        anio, numero = partes

        # Validar que el año sea numérico y tenga 4 dígitos
        if not anio.isdigit() or len(anio) != 4:
            raise forms.ValidationError(
                'El año del período debe tener 4 dígitos (ej: 2024).'
            )

        # Validar que el número de período sea 1 o 2
        if numero not in ['1', '2']:
            raise forms.ValidationError(
                'El número de período debe ser 1 o 2 (ej: 2024-1 o 2024-2).'
            )

        return periodo


class ConsultarRankingForm(forms.Form):
    """
    Formulario para el endpoint GET /api/v1/ranking/consultar/
    Valida el parámetro 'periodo' de la query string.
    """
    periodo = forms.CharField(
        max_length=20,
        min_length=3,
        error_messages={
            'required': 'El parámetro "periodo" es obligatorio. Ejemplo: ?periodo=2024-1',
        }
    )