# ============================================================
# FORMS.PY — App Estudiantes (Capa 6: Validación)
# Valida los datos de entrada ANTES de llegar al controller.
# El view llama al form, si es válido pasa al controller.
# ============================================================

from django import forms
from .models import Estudiante


class EstudianteForm(forms.ModelForm):
    """
    Formulario para registrar y actualizar estudiantes.
    Valida todos los campos antes de que el controller
    los procese. El view instancia este form con request.data.
    """

    class Meta:
        model  = Estudiante
        fields = [
            'cedula', 'nombres', 'apellidos', 'correo', 'telefono',
            'estado_civil', 'cargas_familiares', 'ubicacion_geografica',
            'situacion_economica', 'calificaciones', 'nivel_academico',
            'modulos_ingles_aprobados', 'calificaciones_cerradas',
        ]

    def clean_cedula(self):
        """Valida formato de cédula ecuatoriana (10 dígitos)."""
        cedula = self.cleaned_data.get('cedula', '')
        if not cedula.isdigit():
            raise forms.ValidationError('La cédula debe contener solo dígitos.')
        if len(cedula) != 10:
            raise forms.ValidationError('La cédula debe tener exactamente 10 dígitos.')
        return cedula

    def clean_calificaciones(self):
        """Valida que el promedio esté en rango 0-10."""
        calificaciones = self.cleaned_data.get('calificaciones')
        if calificaciones is not None:
            if calificaciones < 0 or calificaciones > 10:
                raise forms.ValidationError('Las calificaciones deben estar entre 0 y 10.')
        return calificaciones

    def clean_nivel_academico(self):
        """Valida que el nivel esté en rango 1-12."""
        nivel = self.cleaned_data.get('nivel_academico')
        if nivel is not None:
            if nivel < 1 or nivel > 12:
                raise forms.ValidationError('El nivel académico debe estar entre 1 y 12.')
        return nivel

    def clean_cargas_familiares(self):
        """Valida que las cargas familiares no sean un número irreal."""
        cargas = self.cleaned_data.get('cargas_familiares')
        if cargas is not None and cargas > 20:
            raise forms.ValidationError('El número de cargas familiares parece inusual (máx. 20).')
        return cargas


class ActualizarRequisitosForm(forms.Form):
    """
    Formulario para actualizar los requisitos habilitantes
    de un estudiante de forma independiente.
    """
    modulos_ingles_aprobados = forms.BooleanField(required=False)
    calificaciones_cerradas  = forms.BooleanField(required=False)
