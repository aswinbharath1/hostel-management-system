
from django.core.management.base import BaseCommand
from payments.services import generate_monthly_fees


class Command(BaseCommand):
    help = 'Generate monthly rent bills'

    def handle(self, *args, **options):
        try:
            count = generate_monthly_fees()

            self.stdout.write(
                self.style.SUCCESS(
                    f'{count} monthly rent bill(s) generated successfully.'
                )
            )

        except ValueError as error:
            self.stdout.write(
                self.style.ERROR(str(error))
            )
