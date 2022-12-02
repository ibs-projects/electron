from django.apps import AppConfig


class ElecMeterConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'elec_meter'

    def ready(self):
        import elec_meter.signals
