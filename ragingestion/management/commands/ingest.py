from django.core.management.base import BaseCommand

from ragingestion.services.vector_db_storing import Ingestor


class Command(BaseCommand):
    help = "Ingest data into the vector database."

    def handle(self, *args, **options):
        self.stdout.write("Starting ingest...")
        ingestor = Ingestor()
        ingestor.ingest()
        self.stdout.write(self.style.SUCCESS("Ingest completed."))
