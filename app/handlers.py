import logging
import re
import operator
from google.appengine.ext import db
from django.shortcuts import redirect
from piston.handler import BaseHandler
from piston.utils import rc, throttle
from appengine_django.auth import models as authModels
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



class UserHandler(BaseHandler):
    allowed_methods = ('GET')
    fields = ('resource_uri', 'username')
    viewname = 'user_detail'
    model = authModels.User

    def read(self, request, user_id):
	if user_id:
		user = authModels.User.get_by_username(user_id)
		return {'user': user}


    @staticmethod
    def resource_uri(user):
	user_id = user.username
        return ('user', [user_id])


class BeerSubscriberHandler(BaseHandler):
    allowed_methods = ('GET', 'DELETE')
    fields = ('resource_uri', 'beer_name')
    viewname = 'beersubscriber_detail'
    model = models.BeerSubscriber

    def read(self, request, user_id, beer_id):
	if user_id:
		user = authModels.User.get_by_username(user_id)
                subscriber = user.beersubscriber_set.filter('beer =', db.Key.from_path('Beer', int(beer_id))).get() 
		return {'subscriber': subscriber}

    def delete(self, request, user_id, beer_id):
        logging.info('BeerSubscriber.delete')
        if user_id and beer_id:
		user = authModels.User.get_by_username(user_id)
                subscriber = user.beersubscriber_set.filter('beer =', db.Key.from_path('Beer', int(beer_id))).get() 
                subscriber.delete()

                return rc.DELETED
        else:
                return rc.BAD_REQUEST

    @staticmethod
    def resource_uri(beersubscriber):
	user_id = beersubscriber.user.username
	beer_id = beersubscriber.beer.key().id()
        return ('beersubscriber', [user_id, beer_id])



class BeerSubscriberListHandler(BaseHandler):
    allowed_methods = ('GET', 'POST')
    viewname = 'beersubscriber_list'

    def read(self, request, user_id):
	if user_id:
		user = authModels.User.get_by_username(user_id)
		subscribers = user.beersubscriber_set
		return {'subscribers': subscribers}

    def create(self, request, user_id):

        #TODO: check for duplicates before adding
        beer_id = request.POST['beer_id']
        if user_id and beer_id:
                logging.info('user_id: %s | beer_id: %s',user_id, beer_id)
		user = authModels.User.get_by_username(user_id)
                beer = models.Beer.get_by_id(int(beer_id))
                beersubscriber = models.BeerSubscriber(beer=beer, user=user)
                beersubscriber.update_ref_values()
                beersubscriber.put()

                return rc.CREATED
		#subscribers = user.beersubscriber_set
		#return {'subscribers': subscribers}
        else:
                logging.info('no user_id or beer_id')
                return rc.BAD_REQUEST

class BarSubscriberHandler(BaseHandler):
    allowed_methods = ('GET', 'DELETE')
    fields = ('resource_uri', 'bar_name', 'user_name')
    viewname = 'barsubscriber_detail'
    model = models.BarSubscriber

    def read(self, request, user_id, bar_id):
	if user_id and bar_id:
		user = authModels.User.get_by_username(user_id)
                subscriber = user.barsubscriber_set.filter('bar =', db.Key.from_path('Bar', int(bar_id))).get() 
		return {'subscriber': subscriber}


    def delete(self, request, user_id, bar_id):
        logging.info('BarSubscriber.delete')
        if user_id and bar_id:
		user = authModels.User.get_by_username(user_id)
                subscriber = user.barsubscriber_set.filter('bar =', db.Key.from_path('Bar', int(bar_id))).get() 
                subscriber.delete()

                return rc.DELETED
        else:
                return rc.BAD_REQUEST

    @staticmethod
    def resource_uri(barsubscriber):
	user_id = barsubscriber.user.username
	bar_id = barsubscriber.bar.key().id()
        return ('barsubscriber', [user_id, bar_id])



class BarSubscriberListHandler(BarSubscriberHandler):
    allowed_methods = ('GET', 'POST')
    viewname = 'barsubscriber_list'

    def read(self, request, user_id):
	if user_id:
		user = authModels.User.get_by_username(user_id)
		subscribers = user.barsubscriber_set
		return {'subscribers': subscribers}


    def create(self, request, user_id):
        bar_id = request.POST['bar_id']
        if user_id and bar_id:
                logging.info('user_id: %s | bar_id: %s',user_id, bar_id)
		user = authModels.User.get_by_username(user_id)
                bar = models.Bar.get_by_id(int(bar_id))
                barsubscriber = models.BarSubscriber(bar=bar, user=user)
                barsubscriber.update_ref_values()
                barsubscriber.put()

                return rc.CREATED
		#subscribers = user.barsubscriber_set
		#return {'subscribers': subscribers}
        else:
                logging.info('no user_id or bar_id')
                return rc.BAD_REQUEST


