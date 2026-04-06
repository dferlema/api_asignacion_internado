# ============================================================
# FORMS.PY — App Estudiantes (Capa 6: Validación)
# managed=False: valida campos reales de estudiantil.estudiante.
# No hay campos standalone ni de ModelBase.
# ============================================================

from django import forms
from .models import Estudiante, SituacionEconomica, CargaFamiliar


class EstudianteForm(forms.Form):
    """
    Formulario para crear/actualizar estudiantil.estudiante.
    Usa Form en lugar de ModelForm porque el modelo es managed=False
    y varios campos se insertan vía SQL o desde core.persona.
    Solo valida los campos que el API recibe directamente.
    """
    codigo_estudiante = forms.CharField(max_length=20)
    nivel_actual      = forms.IntegerField(required=False, min_value=1, max_value=12)
    estado            = forms.ChoiceField(
        choices=[
            ('ACTIVO',     'Activo'),
            ('SUSPENDIDO', 'Suspendido'),
            ('RETIRADO',   'Retirado'),
            ('GRADUADO',   'Graduado'),
            ('BECA',       'Con Beca'),
        ],
        required=False
    )

    def clean_codigo_estudiante(self):
        codigo = self.cleaned_data.get('codigo_estudiante', '').strip()
        if not codigo:
            raise forms.ValidationError('El código de estudiante es obligatorio.')
        return codigo


class SituacionEconomicaForm(forms.Form):
    """
    Formulario para crear/actualizar estudiantil.situacion_economica.
    """
    NIVEL_POBREZA_OPCIONES = [
        ('EXTREMA', 'Pobreza Extrema'),
        ('BAJA',    'Nivel Bajo'),
        ('MEDIA',   'Nivel Medio'),
        ('ALTA',    'Nivel Alto'),
    ]
    nivel_pobreza           = forms.ChoiceField(choices=NIVEL_POBREZA_OPCIONES)
    ingreso_familiar        = forms.DecimalField(required=False, max_digits=10, decimal_places=2)
    numero_miembros_hogar   = forms.IntegerField(required=False, min_value=1)
    tiene_bono_desarrollo   = forms.BooleanField(required=False)
    tiene_discapacidad      = forms.BooleanField(required=False)
    porcentaje_discapacidad = forms.IntegerField(required=False, min_value=0, max_value=100)
    trabaja                 = forms.BooleanField(required=False)
    horas_trabajo_semana    = forms.IntegerField(required=False, min_value=0)


class CargaFamiliarForm(forms.Form):
    """Formulario para crear estudiantil.carga_familiar."""
    PARENTESCO_OPCIONES = [
        ('HIJO',     'Hijo/a'),
        ('PADRE',    'Padre'),
        ('MADRE',    'Madre'),
        ('CONYUGUE', 'Cónyuge'),
        ('HERMANO',  'Hermano/a'),
        ('OTRO',     'Otro'),
    ]
    parentesco    = forms.ChoiceField(choices=PARENTESCO_OPCIONES)
    edad          = forms.IntegerField(required=False, min_value=0, max_value=120)
    es_dependiente = forms.BooleanField(required=False, initial=True)