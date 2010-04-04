from django import forms
from django.shortcuts import render_to_response
from django.template import RequestContext
from google.appengine.ext import db
from app import models, forms

import logging

def index(request):
	recentBars = models.Bar.get_recently_updated(10)
	return render_to_response('index.html', 
		{'recentbars': recentBars},
		context_instance=RequestContext(request))

def viewBar(request, id):
	bar = models.Bar.get_by_id(int(id))
	stocked_beers = bar.get_beer_in_stock()
	#stocked_beers = bar.stockedbeer_set.filter('currently_stocked =', True).order('-updated_on')

	return render_to_response('viewBar.html',
		{'bar': bar, 'stocked_beers': stocked_beers})

def addBar(request):
	if request.method == 'POST':
		form = forms.BarForm(data=request.POST)
		if form.is_valid():
			#add it to DS
			bar = form.save(commit=False)
			bar.update_location()
			bar.put()
	else:
		form = forms.BarForm()

	return render_to_response('addbar.html', {'form': form})

def addBeer(request):
	if request.method == 'POST':
		bar_id = request.POST.get('bar_id')
		bar = models.Bar.get_by_id(int(bar_id))
		form = forms.BeerForm(data=request.POST)
		if bar and form.is_valid():
			beer = form.save()
			stockedbeer = models.StockedBeer()
			stockedbeer.bar = bar
			stockedbeer.beer = beer
			stockedbeer.update_ref_values()
			stockedbeer.put()
			logging.info('Beer %s, Stocked at %s',stockedbeer.beer_name, stockedbeer.bar_name);

	else:
		form = forms.BeerForm()

	return render_to_response('addbeer.html', {'form': form})
			

def fixBeers(request):
	qry = models.Beer.all()
	logging.info('query count: %s', qry.count())

	for beer in qry:
		beer.update_name_parts()
		beer.put()


def fixBars(request):
	qry = models.Bar.all()
	logging.info('query count: %s', qry.count())

	for bar in qry:
		bar.update_name_parts()
		bar.put()
