# ============================================================
# CONTROLLERS.PY — App Ranking (Capa 3: Orquestación)
# Actualizado para modelos compatibles con Innotech BD.
# El ranking ahora se persiste en RankingInternado.
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
        """
        Ejecuta XGBoost, registra logs en ia.log_prediccion
        y retorna el ranking. No persiste en ranking_internado.
        """
        try:
            servicio    = RankingBusiness()
            ranking     = servicio.generar_ranking()
            importancia = servicio.importancia_variables()
            return respuesta_exito(
                mensaje='Ranking generado exitosamente con XGBoost.',
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
        """
        Genera ranking, persiste en ranking_internado,
        asigna plazas y guarda asignaciones en BD.
        """
        try:
            servicio  = RankingBusiness()
            ranking   = servicio.generar_ranking(periodo_codigo=periodo)

            # Persistir ranking en practicas.ranking_internado
            RankingBusiness.persistir_ranking(ranking, periodo)

            # Asignar plazas
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
        """Consulta el ranking y asignaciones guardadas en BD."""
        try:
            resultado = RankingBusiness.consultar_ranking(periodo)
            return respuesta_exito(
                mensaje=f'{len(resultado)} entradas en el ranking para {periodo}.',
                datos={'periodo': periodo, 'total': len(resultado), 'ranking': resultado}
            )
        except Exception as e:
            return respuesta_error_general(manejar_excepcion(e, 'consultar_ranking'))