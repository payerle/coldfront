from django.apps import AppConfig


class OrganizationConfig(AppConfig):
    name = 'coldfront.core.organization'
    verbose_name = 'Organization'

    #def ready(self):
    #    import coldfront.core.organization.signals
