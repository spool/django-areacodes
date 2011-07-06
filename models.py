from django.contrib.gis.db import models
from ipums.models import PUMA
from phone_numbers import phone_data
from fips import US_STATE_CHAR2FIPS, CONTINENTAL_CHARS

# Create your models here.

class USAreaCodeManager(models.GeoManager):

    def get_query_set(self):
            return super(USAreaCodeManager, self).get_query_set().exclude(npa__in=phone_data.CARRIBEAN_AREACODES \
                    + phone_data.CANADIAN_AREACODES)

class ContinentalUSAreaCodeManager(models.GeoManager):

    def get_query_set(self):
        return super(ContinentalUSAreaCodeManager, self).get_query_set().filter(state__in=CONTINENTAL_CHARS)

class USExchangeManager(models.GeoManager):

    def get_query_set(self):
            return super(USExchangeManager, self).get_query_set().filter(area_codes__in=AreaCode.us.all()).distinct()

class ContinentalUSExchangeManager(models.GeoManager):

    def get_query_set(self):
            return super(ContinentalUSExchangeManager, self).get_query_set().filter(area_codes__in=AreaCode.cont_us.all()).distinct()

class AreaCode(models.Model):
    npa = models.IntegerField()
    nxx = models.IntegerField()
    exchange = models.ForeignKey('Exchange', related_name="area_codes")
    state = models.CharField(max_length=2) # TODO: switch to FIPSCodeField
    city = models.CharField(max_length=30)
    TYPE_CHOICES = (
            ('L', 'Land'),
            ('W', 'Wire Center'),
            ('?', 'Unknown'),
            )
    type = models.CharField(max_length=1, choices=TYPE_CHOICES)
    objects = models.GeoManager()
    us = USAreaCodeManager()
    cont_us = ContinentalUSAreaCodeManager()

    def __unicode__(self):
        return '(%d) - %d: %s, %s (%s)' % \
                (self.npa, self.nxx, self.city, self.state, self.type)

    def strip_city(self):
        self.city = self.city.strip()
        self.save()

    def set_exchange(self):
        exchange, created = Exchange.objects.get_or_create(coordinates=self.coordinates)
        self.exchange = exchange
        self.save()

class Exchange(models.Model):
    coordinates = models.PointField()
    puma = models.ForeignKey('ipums.PUMA', blank=True, null=True, related_name='exchanges')
    fixed_puma = models.BooleanField()

    objects = models.GeoManager()
    us = USExchangeManager()
    cont_us = ContinentalUSExchangeManager()

    def dates(self):
        return self.area_codes.filter(phone_numbers__node_time_points).values_list('date', flat=True).unique()

    def states(self):
        return self.area_codes.values_list('state', flat=True)

    #def set_tract(self):
    #    try:
    #        self.tract = Tract.objects.get(geom__contains=self.coordinates)
    #    except Tract.DoesNotExist:
    #        try:
    #            tracts = Tract.objects.filter(puma=self.puma)
    #            self.tract = tracts.distance(self.coodinates).order_by('distance')[0]
    #            self.fixed_tract = True
    #            print 'Nearest in-puma tract to %s is %s %s' % (self, self.tract, self.tract.geom.centroid)
    #        except Tract.DoesNotExist:
    #            try:
    #                tracts = Tract.objects.filter(state=self.state)
    #                self.tract = tracts.distance(self.coordinates).order_by('distance')[0]
    #                self.fixed_tract = True
    #                print 'Nearest in-state tract to %s is %s %s' % (self, self.tract, self.tract.geom.centroid)
    #            except:
    #                print "Error with %s" % self
    #                return self
    #    self.save()

    def set_puma(self):
        try:
            self.puma = PUMA.objects.get(geom__contains=self.coordinates)
        except PUMA.DoesNotExist:
            try:
                qs = PUMA.objects.filter(state__in=self.states)
                self.puma = qs.distance(self.coordinates).order_by('distance')[0]
                self.fixed_puma = True
                print 'Nearest in-state PUMA to %s is %s %s' % (self, self.puma, self.puma.geom.centroid)
            except:
                print "Error with %s" % self
                return self
        self.save()

    def __unicode__(self):
        return '(%f, %f) %s' % (self.coordinates.coords[1], self.coordinates.coords[0], self.area_codes.all()[0])


