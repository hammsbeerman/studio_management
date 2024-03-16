"""
Django settings for studio_management project.

Generated by 'django-admin startproject' using Django 4.2.8.

For more information on this file, see
https://docs.djangoproject.com/en/4.2/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/4.2/ref/settings/
"""

import os
from pathlib import Path

# LOGGING = {
#     "version": 1,
#     "disable_existing_loggers": False,
#     "handlers": {
#         "file": {
#             "level": "DEBUG",
#             "class": "logging.FileHandler",
#             "filename": "/home/adam/logs/debug.log",
#         },
#     },
#     "loggers": {
#         "django": {
#             "handlers": ["file"],
#             "level": "WARNING",
#             "propagate": True,
#         },
#     },
# }

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

#Allow SSL Change if domain name changes
CSRF_TRUSTED_ORIGINS = ["https://staging.lkdesignstudios.com", "http://staging.lkdesignstudios.com", 
                        "https://studiomanagement.lkdesignstudios.com", "http://studiomanagement.lkdesignstudios.com"]
#CSRF_TRUSTED_ORIGINS = []


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/4.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get('SECRET_KEY', 'django-insecure-x8b(_)4hn$na81seyn%ffeu=ngkw1+tb3d7-hlrhl1^adk4#ex')
#print(SECRET_KEY)

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = str(os.environ.get('DEBUG')) == "1"


ALLOWED_HOSTS = ['localhost', '10.6.83.220', '10.6.83.230', 'studiomanagement.lkdesignstudios.com', '10.6.83.229', 'staging.lkdesignstudios.com']
#ALLOWED_HOSTS += os.environ.get('ALLOWED_HOST').split(',')
# if not DEBUG:
#     ALLOWED_HOSTS += os.environ.get('ALLOWED_HOST').split(',')
# else:
#     ALLOWED_HOSTS += ['localhost', '10.6.83.220']



#print(ALLOWED_HOSTS)


# Application definition

DEFAULT_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
]

THIRD_PARTY_APPS = [
    'localflavor',
    'django_htmx',
    'widget_tweaks',
    'crispy_forms',
    'crispy_bootstrap5',
    'import_export',
]

LOCAL_APPS = [
    
    'accounts',
    'controls',
    'customers',
    'dashboard',
    'inventory',
    'finance',
    'krueger',
    'pdf',
    'pricesheet',
    #'vendors',
    'workorders',
    
]

INSTALLED_APPS = DEFAULT_APPS + LOCAL_APPS + THIRD_PARTY_APPS

CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap5"

CRISPY_TEMPLATE_PACK = "bootstrap5"

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django_htmx.middleware.HtmxMiddleware',
]

ROOT_URLCONF = 'studio_management.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / "templates",],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'studio_management.wsgi.application'


# Database
# https://docs.djangoproject.com/en/4.2/ref/settings/#databases

TESTING = str(os.environ.get('TESTING')) == "1"
if not TESTING:
    #Production database
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.mysql',
            'OPTIONS': {
        	        'read_default_file': '/etc/mysql/my.cnf',
    	},
        }
    }
else:
    #Development database
    DATABASES = {
        'default': {
            'ENGINE': os.environ.get('ENGINE'),
            'NAME': BASE_DIR / os.environ.get('NAME'),
        }
    }


# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.sqlite3',
#         'NAME': BASE_DIR / 'db.sqlite3',
#     }
# }


# DATABASES = {
#     'default': {
#         'ENGINE': os.environ.get('ENGINE'),
#         'NAME': BASE_DIR / os.environ.get('NAME'),
#         'USER': os.environ.get('USER'),
#         'PASSWORD': os.environ.get('HOST'),
#         'HOST': os.environ.get('HOST'),
#         'PORT': os.environ.get('PORT'),
#     }
# }

# DATABASES = {
#     'default' : os.environ.get('DB')
# }


# Password validation
# https://docs.djangoproject.com/en/4.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/4.2/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'America/Chicago'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.2/howto/static-files/

STATIC_URL = '/static/'

STATIC_ROOT = BASE_DIR / "staticfiles"
#STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles/') 


# STATICFILES_DIRS = [
#     #BASE_DIR / "static",
#     BASE_DIR / "templates/static",
# ]

STATICFILES_DIRS = (
    os.path.join(BASE_DIR, 'static'),
)

FIXTURE_DIRS = (
    os.path.join(BASE_DIR, 'fixtures'),
)

# Media Files
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

MEDIA_URL = '/media/'

# Default primary key field type
# https://docs.djangoproject.com/en/4.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
