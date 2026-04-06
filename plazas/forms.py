# ============================================================
# FORMS.PY — App Plazas (Capa 6: Validación)
# managed=False: valida campos reales de practicas.*
# Usa Form simple — NO ModelForm.
# ============================================================

from django import forms


class PlazaPracticaForm(forms.Form):
    """
    Valida los datos para crear/actualizar practicas.plaza_practica.
    Usa Form (no ModelForm) porque el modelo es managed=False.
    """
    AREA_OPCIONES = [
        ('clinica',          'Clínica'),
        ('cirugia',          'Cirugía'),
        ('pediatria',        'Pediatría'),
        ('ginecologia',      'Ginecología'),
        ('emergencias',      'Emergencias'),
        ('medicina_interna', 'Medicina Interna'),
        ('otro',             'Otro'),
    ]

    id_institucion  = forms.IntegerField()
    area            = forms.ChoiceField(choices=AREA_OPCIONES)
    nombre_plaza    = forms.CharField(max_length=200)
    cupo_total      = forms.IntegerField(min_value=1, initial=1)
    cupo_disponible = forms.IntegerField(min_value=0, initial=1)
    fecha_inicio    = forms.DateField(required=False)
    fecha_fin       = forms.DateField(required=False)
    descripcion     = forms.CharField(required=False, widget=forms.Textarea)
    activa          = forms.BooleanField(required=False, initial=True)

    def clean(self):
        cleaned         = super().clean()
        cupo_total      = cleaned.get('cupo_total', 1)
        cupo_disponible = cleaned.get('cupo_disponible', 1)
        if cupo_disponible > cupo_total:
            raise forms.ValidationError(
                'El cupo disponible no puede superar el cupo total.'
            )
        return cleaned


class AsignarPeriodoForm(forms.Form):
    """Valida el período para el endpoint de asignación de ranking."""
    periodo = forms.CharField(max_length=10)

    def clean_periodo(self):
        periodo = self.cleaned_data.get('periodo', '').strip()
        if not periodo or '-' not in periodo:
            raise forms.ValidationError('Formato inválido. Use AAAA-N (ej: 2024-1).')
        partes = periodo.split('-')
        if len(partes) != 2 or not partes[0].isdigit() or len(partes[0]) != 4:
            raise forms.ValidationError('Formato inválido. Ejemplo: 2024-1')
        if partes[1] not in ['1', '2']:
            raise forms.ValidationError('El número de período debe ser 1 o 2.')
        return periodo