"""Deprecated legacy command.

The managed `patients` table is created via migrations in `praxi_backend.patients`.
"""

from django.core.management.base import BaseCommand


class Command(BaseCommand):  # pragma: no cover
	help = "DEPRECATED (single DB): patients table is created via migrations."

	def handle(self, *args, **options):
		self.stdout.write(
			self.style.WARNING(
				"Deprecated: patients table is created via migrations (single DB)."
			)
		)


