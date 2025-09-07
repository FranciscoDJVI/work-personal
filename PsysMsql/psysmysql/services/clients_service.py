from ..models import Clients
from ..logging_config import get_clients_logger, log_execution_time, LogOperation
from ..services.search_orm import Search


class RegisterClients:

    @staticmethod
    @log_execution_time(get_clients_logger())
    def register_client(
        name,
        email,
        direction,
        telephone,
        nit,
        country,
        departament,
        city,
    ):

        logger = get_clients_logger()

        with LogOperation(f"Creando cliente: {name}", logger):
            if Search.filter(Clients, "name", name).exists():
                logger.warning(f"No es posible crear el cliente: {name}")
                raise ValueError("El cliente ya existe")

        new_client = Clients.objects.create(
            name=name,
            email=email,
            direction=direction,
            telephone=telephone,
            nit=nit,
            country=country,
            departament=departament,
            city=city,
        )
        logger.info(f"Cliente creado exitosamente: {name}")

        return new_client


class GertAllClients:

    @staticmethod
    @log_execution_time(get_clients_logger())
    def get_all_clients():
        logger = get_clients_logger()
        with LogOperation("Obteniendo todos los clientes", logger):

            all_clients = Search.search_default(Clients).order_by("name")
            total_clients = Search.search_default(Clients).count()
            logger.info(f"Total de clientes obtenidos: {total_clients}")

            all_clients_dict: dict = {}

            for cliente_detail in all_clients:
                all_clients_dict[cliente_detail.id] = {
                    "name": cliente_detail.name,
                    "email": cliente_detail.email,
                    "direction": cliente_detail.direction,
                    "telephone": cliente_detail.telephone,
                    "nit": cliente_detail.nit,
                    "country": cliente_detail.country,
                    "departament": cliente_detail.departament,
                    "city": cliente_detail.city,
                }
        return all_clients
