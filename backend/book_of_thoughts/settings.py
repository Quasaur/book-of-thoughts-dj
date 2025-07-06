import os 
from pathlib import Path 
from dotenv import load_dotenv 

load_dotenv() 

BASE_DIR = Path(__file__).resolve().parent.parent 
SECRET_KEY = os.getenv('SECRET_KEY', 'your-secret-key-here') 
DEBUG = os.getenv('DEBUG', 'False').lower() == 'true' 
ALLOWED_HOSTS = ['localhost', '127.0.0.1', '0.0.0.0'] 

INSTALLED_APPS = [ 'django.contrib.admin', 'django.contrib.auth', 'django.contrib.contenttypes', 'django.contrib.sessions', 'django.contrib.messages', 'django.contrib.staticfiles', 'rest_framework', 'corsheaders', 'thoughts_api', 'graph_app', 'topics',
] 

MIDDLEWARE = [ 'corsheaders.middleware.CorsMiddleware', 'django.middleware.security.SecurityMiddleware', 'django.contrib.sessions.middleware.SessionMiddleware', 'django.middleware.common.CommonMiddleware', 'django.middleware.csrf.CsrfViewMiddleware', 'django.contrib.auth.middleware.AuthenticationMiddleware', 'django.contrib.messages.middleware.MessageMiddleware', 'django.middleware.clickjacking.XFrameOptionsMiddleware', 
] 

ROOT_URLCONF = 'book_of_thoughts.urls' 

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'book_of_thoughts' / 'templates'],
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

WSGI_APPLICATION = 'book_of_thoughts.wsgi.application' 

# Database - using default SQLite for Django admin, sessions, etc. 
# Neo4j is handled separately via driver 
DATABASES = { 
	'default': { 
	'ENGINE': 'django.db.backends.sqlite3', 
	'NAME': BASE_DIR / 'db.sqlite3', 
	} 
} 

# Neo4j Configuration 
NEO4J_URI = os.getenv('NEO4J_URI') 
NEO4J_USERNAME = os.getenv('NEO4J_USERNAME') 
NEO4J_PASSWORD = os.getenv('NEO4J_PASSWORD') 
NEO4J_DATABASE = os.getenv('NEO4J_DATABASE', 'neo4j') 

AUTH_PASSWORD_VALIDATORS = [ 
	{ 'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator', }, 
	{ 'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator', }, 
	{ 'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator', }, 
	{ 'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator', }, 
] 

LANGUAGE_CODE = 'en-us' 
TIME_ZONE = 'UTC' 
USE_I18N = True 
USE_TZ = True 

STATIC_URL = '/static/' 
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATICFILES_DIRS = [
    BASE_DIR / 'book_of_thoughts' / 'static',
] 

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField' 

# REST Framework Configuration 
REST_FRAMEWORK = { 
	'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination', 
	'PAGE_SIZE': 20, 
	'DEFAULT_RENDERER_CLASSES': [ 'rest_framework.renderers.JSONRenderer', ], 
	'DEFAULT_PARSER_CLASSES': [ 'rest_framework.parsers.JSONParser', ], 
} 
# CORS Configuration for React frontend 
CORS_ALLOWED_ORIGINS = [ 
	"http://localhost:3000", 
	"http://127.0.0.1:3000", 
] 

CORS_ALLOW_CREDENTIALS = True