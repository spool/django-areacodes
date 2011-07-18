from models import AreaCode, Exchange
from phone_numbers import phone_data
from django.conf import settings
from nhgis.models import dataset
import os

DATA_PATH = os.path.join(settings.PROJECT_PATH, 'area_codes', 'data')
FILENAME = 'npanxx98.txt'

# This function is obsolete with new AreaCode Models
#def data_import(filename=FILENAME, path=DATA_PATH, delete=False):
#    
#    if delete:
#        AreaCode.objects.all().delete()
#    file = os.path.join(path,filename)
#    with open(file, 'r') as f:
#        for s in f.readlines():
#            l = s.split(' ')
#            a = AreaCode(npa=l[0], nxx=l[1], latitude=l[2], longitude=l[3],
#                    type=l[4], state=l[5], city=l[6])
#            a.save()

def city_fix(filename=FILENAME, path=DATA_PATH):
    file = os.path.join(path,filename)
    with open(file, 'r') as f:
        for s in f.readlines()[1:]:
            l = s.split(' ')
            a = AreaCode.objects.get(npa=l[0], nxx=l[1], type=l[4], state=l[5])
            a.city = ' '.join(l[6:])
            a.save()

#def map_tracts(area_codes=AreaCode.us.filter(tract__isnull=True)):
#    errors = []
#    for a in area_codes:
#        try:
#            a.set_tract()
#        except:
#            errors.append(a)
#    return errors
    
def city_var(exchanges=Exchange.objects.all()):
    errors = []
    for e in exchanges:
        ref = e.area_codes.all()[0]
        for a in e.area_codes.all()[1:]:
            if ref.city != a.city: 
                errors.append(e)
                break
    return errors

def state_var(exchanges=Exchange.objects.all()):
    errors = []
    for e in exchanges:
        ref = e.area_codes.all()[0]
        for a in e.area_codes.all()[1:]:
            if ref.state != a.state: 
                errors.append(e)
                break
    return errors

def type_var(exchanges=Exchange.objects.all()):
    errors = []
    for e in exchanges:
        ref = e.area_codes.all()[0]
        for a in e.area_codes.all()[1:]:
            if ref.type != a.type: 
                errors.append(e)
                break
    return errors

def country_var(exchanges=Exchange.objects.all()):
    errors = []
    us_exchanges = Exchange.objects.filter(area_codes__in=AreaCode.us.all())
    for e in us_exchanges:
        for a in e.area_codes.all()[1:]:
            if a.npa in phone_data.CARRIBEAN_AREACODES + phone_data.CARRIBEAN_AREACODES:
                errors.append(e)
                break
    return errors

def set_pumas(exchanges=Exchange.us.all()):
    errors = []
    for e in exchanges:
        if e.set_puma(): # Will return None if no error
            errors.append(e)
    return errors

def set_tracts(exchanges=Exchange.us.all()):
    errors = []
    for e in exchanges:
        if e.set_tract(): # Will return None if no error
            errors.append(e)
    return errors

DATAVAR_SKIP = ['BLOCKGR']

def exchange_areas(exchanges=Exchange.cont_us.all()):
    errors = []
    data_dict = {}
    variables = dataset.variables
    for exchange in exchanges:
        try:
            d = {}
            for var in set(variables) - set(exchanges):
                d[var] = sum([t.data[var] for t in exchange.tracts.all()])
            data_dict[e.id] = d
        except:
            errors.append(exchange)
    return errors, data_dict
