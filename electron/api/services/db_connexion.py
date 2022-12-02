import psycopg2

from electron.electron.settings import DATABASES

try:
    chaine =  "host="+ DATABASES["default"]["HOST"] +" port="+ DATABASES["default"]["PORT"] +" dbname="+ DATABASES["default"]["NAME"] +" user=" + DATABASES["default"]["USER"] \
    +" password="+ DATABASES["default"]["PASSWORD"]
    chaine_connexion = psycopg2.connect(chaine)
    print("Connexion établie")
except Exception as e:
    print(e)
    print("Echec de la connexion")


