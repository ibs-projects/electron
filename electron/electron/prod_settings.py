import dj_database_url

from .settings import *

ALLOWED_HOSTS = ['.herokuapp.com']

TEMPLATE_DEBUG = False

SECRET_KEY = '68_d6fe@+6_=#ul2yg1fjr7cb&u+x@m=18o_k%frg037a_)&l*'

DATABASES['default'] = dj_database_url.config()

MIDDLEWARE += ['whitenoise.middleware.WhiteNoiseMiddleware']

STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'