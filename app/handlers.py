import logging
import re
import operator
from django.shortcuts import redirect
from piston.handler import BaseHandler
from piston.utils import rc, throttle
from app import models, forms


class SearchHandler(BaseHandler):
    allowed_methods = ('GET')#, 'PUT', 'DELETE')
    viewname = 'search_results'
    
    def read(self, request, query=None):
	logging.info('passed: %s', query)
	if not query or len(query) == 0:
		query = request.GET.get('q')
	
	logging.info('picked: %s', query)
	barQry = models.Bar.get_by_name(query)
	beerQry = models.Beer.get_by_name(query)

	results = list(barQry) + list(beerQry)
	results.sort(key=operator.attrgetter('name'))
	return {'results':  results}

class BarHandler(BaseHandler):
    allowed_methods = ('GET')#, 'PUT', 'DELETE')
    fields = ('name', 'remote_url', 'location')
    model = models.Bar
    viewname = 'bar_detail'


    #@staticmethod
    #def resource_uri(bar):
    #    return bar.get_absolute_uri()


    def read(self, request, bar_id=None):
	if bar_id:
		bar = models.Bar.get_by_id(int(bar_id))
		return {
			'bar': bar,
			}


class BarListHandler(BarHandler):
    fields = ('resource_uri', 'name')
    viewname = 'bar_list'

    def read(self, request):
	return models.Bar.all()



class BeerHandler(BaseHandler):
    allowed_methods = ('GET')
    model = models.Beer
    viewname = 'beer_detail'
    
    def read(self, request, beer_id):
	if beer_id:
		beer = models.Beer.get_by_id(int(beer_id))
		return {'beer': beer}

    #@staticmethod
    #def resource_uri(beer):
#	return beer.get_absolute_url()

class StockedBeerHandler(BaseHandler):
    allowed_methods = ('GET', 'DELETE') #, 'POST', 'PUT')
    fields = ('resource_uri', 'name', 'brewery')
    viewname = 'stockedbeer_detail'
    model = models.StockedBeer

    def read(self, request, bar_id, beer_id):
	if bar_id and beer_id:
		bar = models.Bar.get_by_id(int(bar_id))
		beer = bar.get_beer_in_stock(int(beer_id))
		return {'beer': beer}

    def delete(self, request, bar_id, beer_id):
	if bar_id and beer_id:
		bar = models.Bar.get_by_id(int(bar_id))
		beer = bar.get_beer_in_stock(int(beer_id))
		beer.delete()
		#return {'beer': beer}
		return rc.DELETED
	else:
		return rc.BAD_REQUEST

    @staticmethod
    def resource_uri(stockedbeer):
        bar_id = stockedbeer.bar.key().id()
	beer_id = stockedbeer.beer.key().id()
        return ('stockedbeer', [bar_id, beer_id])


    @staticmethod
    def name(stockedbeer):
	return stockedbeer.beer_name

    @staticmethod
    def brewery(stockedbeer):
	return stockedbeer.beer.brewery

    @staticmethod
    def stocked(stockedbeer):
	return stockedbeer.currently_stocked




class StockedBeerListHandler(StockedBeerHandler):
    allowed_methods = ('GET', 'POST')
    fields = ('resource_uri', 'stocked', 'brewery', 'name')
    viewname = 'beer_list'

    def read(self, request, bar_id):
	if bar_id:
		bar = models.Bar.get_by_id(int(bar_id))
		beers = bar.get_beer_in_stock()
		return {'stockedbeers': beers}

    def create(self, request, bar_id):
	logging.info('bar_id: %s', bar_id)
	logging.info('content_type: %s', request.content_type)
	
	data = request.POST
	logging.info('data: %s', data)
	if bar_id: #request.content_type:
		bar = models.Bar.get_by_id(int(bar_id))
	
		form = forms.BeerForm(data)
		beer = form.save(commit=False)
		beer.name_parts =  re.findall('[a-z]+', beer.name.lower())
		logging.info('Beer name parts: %s', beer.name_parts)
		beer.put()
		
		stockedbeer = models.StockedBeer(beer=beer, bar=bar)
		stockedbeer.update_ref_values()
		stockedbeer.put()
		logging.info('Beer %s, Stocked at %s',stockedbeer.beer_name, stockedbeer.bar_name)

		return {'stockedbeers': bar.get_beer_in_stock()}
	else:
		super(models.StockedBeer, self).create(request)
