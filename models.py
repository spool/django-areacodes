from django.contrib.gis.db import models
from census1990.models import CensusTract
from ipums.models import PUMA
from phone_numbers import phone_data
from ipums.fips import US_STATE_CHAR2FIPS

# Create your models here.

class USAreaCodeManager(models.GeoManager):

    def get_query_set(self):
            return super(USAreaCodeManager, self).get_query_set().exclude(npa__in=phone_data.CARRIBEAN_AREACODES + phone_data.CANADIAN_AREACODES)

class AreaCode(models.Model):
    npa = models.IntegerField()
    nxx = models.IntegerField()
    exchange = models.ForeignKey('Exchange', related_name="area_codes", blank=True, null=True)
    latitude = models.CharField(max_length=5)
    longitude = models.CharField(max_length=6)
    state = models.CharField(max_length=2)
    city = models.CharField(max_length=30)
    TYPE_CHOICES = (
            ('L', 'Land'),
            ('W', 'Wire Center'),
            ('?', 'Unknown'),
            )
    type = models.CharField(max_length=1, choices=TYPE_CHOICES)
    coordinates = models.PointField(blank=True, null=True)
    tract = models.ForeignKey('census1990.CensusTract', blank=True, null=True, related_name="area_codes")
    puma = models.ForeignKey('ipums.PUMA', blank=True, null=True, related_name="area_codes")
    fixed_puma = models.BooleanField(default=False)
    objects = models.GeoManager()
    us = USAreaCodeManager()

    def __unicode__(self):
        return '(%d) - %d: %s, %s (%s)' % \
                (self.npa, self.nxx, self.city, self.state, self.type)

    def set_tract(self):
        self.tract = CensusTract.objects.get(geom__contains=self.coordinates)
        self.save()

    def set_puma(self):
        try:
            self.puma = PUMA.objects.get(geom__contains=self.coordinates)
        except PUMA.DoesNotExist:
            try:
                qs = PUMA.objects.filter(statefip=US_STATE_CHAR2FIPS[self.state])
                self.puma = qs.distance(self.coordinates).order_by('distance')[0]
                self.fixed_puma = True
                print 'Nearest instate to %s %s is %s %s' % (self, self.coordinates, self.puma, self.puma.geom.centroid)
            except IndexError:
                print "Could not find PUMA for %s" % self
        self.save()

    def strip_city(self):
        self.city = self.city.strip()
        self.save()

    def set_coordinates(self):
        self.coordinates = 'POINT(-%s %s)' % (self.longitude, self.latitude)
        self.save()

    def set_exchange(self):
        exchange, created = Exchange.objects.get_or_create(coordinates=self.coordinates)
        self.exchange = exchange
        self.save()

class Exchange(models.Model):
    coordinates = models.PointField()

    objects = models.GeoManager()

    def __unicode__(self):
        return '%s' % self.coordinates
