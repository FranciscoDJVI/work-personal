"""Service for search in database using ORM"""

from django.db.models import Q
from psysmysql.models import Clients


class Search:
    @staticmethod
    def search_default(model: type):
        return model.objects.all()

    @staticmethod
    def filter(model: type, field: str, value):
        filter_kwargs = {field: value}
        return model.objects.filter(**filter_kwargs)

    @staticmethod
    def get(model: type, field: str, value):
        filter_kwargs = {field: value}
        return model.objects.get(**filter_kwargs)

    @staticmethod
    def values(model: type, value: str):
        return model.objects.values(value)

    @staticmethod
    def search_clients_by_email(query):
        if not query:
            return []

        return Clients.objects.filter(Q(email__icontains=query)).distinct()
