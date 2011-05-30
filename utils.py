from models import AreaCode
from django.conf import settings
import os

DATA_PATH = os.path.join(settings.PROJECT_PATH, 'area_codes', 'data')
FILENAME = 'npanxx98.txt'

def data_import(filename=FILENAME, path=DATA_PATH, delete=False):
    if delete:
        AreaCode.objects.all().delete()
    file = os.path.join(path,filename)
    with open(file, 'r') as f:
        for s in f.readlines()[1:]:
            l = s.split(' ')
            a = AreaCode(npa=l[0], nxx=l[1], latitude=l[2], longitude=l[3],
                    type=l[4], state=l[5], city=l[6])
            a.save()

def map_tracts(area_codes=AreaCode.us.filter(tract__isnull=True)):
    errors = []
    for a in area_codes:
        try:
            a.set_tract()
        except:
            errors.append(a)
    return errors
    
