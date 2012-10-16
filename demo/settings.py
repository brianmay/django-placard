DEBUG=True
TEMPLATE_DEBUG = DEBUG

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.admin',
    'django.contrib.staticfiles',
    'placard',
    'placard.lusers',
    'placard.lgroups',
    'andsome',
    'andsome.layout',
)

LDAP_USE_TLS=False
LDAP_URL = 'ldap://localhost:38911'

LDAP_ADMIN_PASSWORD="password"
LDAP_BASE="dc=python-ldap,dc=org"
LDAP_ADMIN_USER="cn=Manager,dc=python-ldap,dc=org"
LDAP_USER_BASE='ou=People, %s' % LDAP_BASE
LDAP_GROUP_BASE='ou=Group, %s' % LDAP_BASE
LDAP_ATTRS = 'demo.ldap_attrs'

LDAP_PASSWD_SCHEME = 'ssha'
TEST_RUNNER='andsome.test_utils.xmlrunner.run_tests'

ROOT_URLCONF = 'demo.urls'

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'andsome.middleware.threadlocals.ThreadLocals',
    'django.middleware.doc.XViewMiddleware',
    'tldap.middleware.TransactionMiddleware',
)

DATABASE_ENGINE = 'sqlite3'           # 'postgresql_psycopg2', 'postgresql', 'mysql', 'sqlite3' or 'oracle'.
DATABASE_NAME = 'placard.db'          # Or path to database file if using sqlite3.
DATABASE_USER = 'placard'             # Not used with sqlite3.
DATABASE_HOST = 'db.vpac.org'         # Set to empty string for localhost. Not used with sqlite3.
DATABASE_PORT = ''             # Set to empty string for default. Not used with sqlite3.
