import re
from google.appengine.ext import db
from appengine_django.models import BaseModel
from django.db import models
from geo.geomodel import GeoModel

import logging

# Note, this is a GeoModel
class Bar(BaseModel, GeoModel):
	name = db.StringProperty(required=True)
	remote_url = db.LinkProperty()
	added_on = db.DateTimeProperty(auto_now_add=True)
	updated_on = db.DateTimeProperty(auto_now=True)

	name_parts = db.StringListProperty()

	#The following properties inherited from GeoModel
	#location = db.GeoPt()

	#The following properties set from StockedBeer reference
	#stockedbeer_set

	@staticmethod
	def get_recently_updated(limit):
		return db.GqlQuery("SELECT * FROM Bar ORDER BY updated_on DESC")

	@staticmethod
	def get_by_partial_name(partName):
		return db.GqlQuery("SELECT * FROM Bar where name >= :1 AND name < :2", partName, partName + u"\ufffd")

	@staticmethod
	def get_by_name(partName):
		parts = re.findall('[a-z]+', partName.lower())
		query = db.Query(Bar)
		for part in parts:
			query.filter('name_parts =', part)

		return query
	
	#TODO: move to StockedBeer?
	def get_beer_in_stock(self, beer_id=None):
		currentQry = self.stockedbeer_set.filter('currently_stocked =', True).order('-updated_on')
		if beer_id:
			return currentQry.filter('beer =', db.Key.from_path('Beer', beer_id)).get()
		else:
			return currentQry.order('-updated_on')


	def update_name_parts(self):
		self.name_parts = re.findall('[a-z]+', self.name.lower())

	@models.permalink
	def get_absolute_url(self):
        	return ('bar', [self.key().id()])



class Beer(BaseModel):
	brewery = db.StringProperty(required=False)
	name = db.StringProperty(required=True)
	remote_url = db.LinkProperty()
	added_on = db.DateTimeProperty(auto_now_add=True)
	updated_on = db.DateTimeProperty(auto_now=True)

	name_parts = db.StringListProperty()
	
	#The following properties set from StockedBeer reference
	#stockedbeer_set


	@models.permalink
	def get_absolute_url(self):
        	return ('beer', [self.key().id()])

	def update_name_parts(self):
		self.name_parts = re.findall('[a-z]+', self.name.lower())

	@staticmethod
	def get_by_partial_name(partName):
		return db.GqlQuery("SELECT * FROM Beer where name >= :1 AND name < :2", partName, unicode(partName) + u"\ufffd")

	@staticmethod
	def get_by_name(partName):
		parts = re.findall('[a-z]+', partName.lower())
		query = db.Query(Beer)
		for part in parts:
			query.filter('name_parts =', part)

		return query

class StockedBeer(BaseModel):
	beer = db.ReferenceProperty(Beer, required=True)
	beer_name = db.StringProperty()

	bar = db.ReferenceProperty(Bar, required=True)
	bar_name = db.StringProperty()

	currently_stocked = db.BooleanProperty(required=True, default=True)
	added_on = db.DateTimeProperty(auto_now_add=True)
	updated_on = db.DateTimeProperty(auto_now=True)


	def update_ref_values(self):
		self.beer_name = self.beer.name
		self.bar_name = self.bar.name
