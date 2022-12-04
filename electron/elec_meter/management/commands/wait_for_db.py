"""
Commande pour attendre que la base de données lance avant l'application
"""

import time

from psycopg2 import OperationalError as Psycopg2OpError

from django.db.utils import OperationalError
from django.core.management.base import BaseCommand

class Command(BaseCommand):
    """Commande pour attendre le demarrage de la base de données"""

    def handle(self, *args, **options):
        """Point d'entrée de la commande"""
        self.stdout.write("Attente de la bse de données")
        db_up = True
        while db_up is False:
            try:
                self.check(databases=['default'])
                db_up = True
            except(Psycopg2OpError,OperationalError):
                self.stdout.write('Base de données indisponible, Merci de patienter...')
                time.sleep(1)
        self.stdout.write(self.style.SUCCESS('Database déja opérationnelle!'))