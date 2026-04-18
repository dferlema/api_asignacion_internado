# ============================================================
# CONTROLLERS.PY — App Ranking (Capa 3: Orquestación)
# explicar() ahora resuelve el estudiante por UUID, cédula o nombre.
# ============================================================

from helpers.response_helper import (
    respuesta_exito, respuesta_error_general, respuesta_error_validacion
)
from helpers.error_helper import manejar_excepcion
from rest_framework import status
from .business import RankingBusiness


class RankingController:

    @staticmethod
    def generar():
        """Ejecuta XGBoost + SHAP y retorna el ranking."""
        try:
            servicio    = RankingBusiness()
            ranking     = servicio.generar_ranking()
            importancia = servicio.importancia_variables()
            return respuesta_exito(
                mensaje='Ranking generado exitosamente con XGBoost + SHAP.',
                datos={
                    'total_estudiantes':     len(ranking),
                    'ranking':               ranking,
                    'importancia_variables': importancia,
                    'pesos_utilizados':      RankingBusiness.PESOS,
                }
            )
        except ValueError as e:
            return respuesta_error_validacion(mensaje=str(e))
        except Exception as e:
            return respuesta_error_general(manejar_excepcion(e, 'generar_ranking'))

    @staticmethod
    def asignar(periodo: str):
        """Genera ranking con SHAP, persiste y asigna plazas."""
        try:
            servicio  = RankingBusiness()
            ranking   = servicio.generar_ranking(periodo_codigo=periodo)
            RankingBusiness.persistir_ranking(ranking, periodo)
            resultado = RankingBusiness.asignar_plazas(ranking, periodo)
            return respuesta_exito(
                mensaje=(
                    f'Asignación completada para {periodo}. '
                    f'{resultado["total_asignados"]} asignados, '
                    f'{resultado["total_lista_espera"]} en lista de espera.'
                ),
                datos={'periodo': periodo, **resultado},
                codigo=status.HTTP_201_CREATED
            )
        except ValueError as e:
            return respuesta_error_validacion(mensaje=str(e))
        except Exception as e:
            return respuesta_error_general(manejar_excepcion(e, 'asignar_plazas'))

    @staticmethod
    def consultar(periodo: str):
        """Consulta ranking y asignaciones guardadas en BD."""
        try:
            resultado = RankingBusiness.consultar_ranking(periodo)
            return respuesta_exito(
                mensaje=f'{len(resultado)} entradas en el ranking para {periodo}.',
                datos={'periodo': periodo, 'total': len(resultado), 'ranking': resultado}
            )
        except Exception as e:
            return respuesta_error_general(manejar_excepcion(e, 'consultar_ranking'))

    @staticmethod
    def explicar(periodo: str, estudiante_id: str = None,
                 cedula: str = None, nombre: str = None):
        """
        Genera explicación SHAP para un estudiante.
        Resuelve el estudiante por UUID, cédula o nombre (en ese orden).
        Al menos uno de los tres parámetros de búsqueda es obligatorio.
        """
        try:
            # --- Resolver el UUID del estudiante según el parámetro recibido ---
            uuid_resuelto = RankingBusiness.resolver_estudiante(
                estudiante_id=estudiante_id,
                cedula=cedula,
                nombre=nombre,
            )

            servicio    = RankingBusiness()
            explicacion = servicio.explicar_estudiante(uuid_resuelto, periodo)
            return respuesta_exito(
                mensaje=(
                    f'Explicación SHAP generada para '
                    f'{explicacion.get("nombre_completo", uuid_resuelto)} '
                    f'— período {periodo}.'
                ),
                datos=explicacion
            )
        except ValueError as e:
            return respuesta_error_validacion(mensaje=str(e))
        except Exception as e:
            return respuesta_error_general(manejar_excepcion(e, 'explicar_shap'))