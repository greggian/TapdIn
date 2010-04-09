# Copyright 2008 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from django.conf.urls.defaults import *
#from piston.resource import Resource
from app import handlers, emitters, resource

bar_resource = resource.Resource(handler=handlers.BarHandler)
bar_list_resource = resource.Resource(handler=handlers.BarListHandler)

beer_resource = resource.Resource(handler=handlers.BeerHandler)

stockedbeer_resource = resource.Resource(handler=handlers.StockedBeerHandler)
stockedbeer_list_resource = resource.Resource(handler=handlers.StockedBeerListHandler)

search_resource = resource.Resource(handler=handlers.SearchHandler)

user_resource = resource.Resource(handler=handlers.UserHandler)
beersubscriber_list_resource = resource.Resource(handler=handlers.BeerSubscriberListHandler)
beersubscriber_resource = resource.Resource(handler=handlers.BeerSubscriberHandler)
barsubscriber_list_resource = resource.Resource(handler=handlers.BarSubscriberListHandler)
barsubscriber_resource = resource.Resource(handler=handlers.BarSubscriberHandler)

urlpatterns = patterns('',
	(r'^$', 'app.views.index'),
	(r'^addBar/$', 'app.views.addBar'),
	(r'^addBeer/$', 'app.views.addBeer'),

	(r'^fixBeers/$', 'app.views.fixBeers'),
	(r'^fixBars/$', 'app.views.fixBars'),

	url(r'^search/(?P<query>[^/]+)?/?$', search_resource, name='search'),
	
	url(r'^users/(?P<user_id>[^/]+)/$', user_resource, name='user'),
	url(r'^users/(?P<user_id>[^/]+)/beer/$', beersubscriber_list_resource),
	url(r'^users/(?P<user_id>[^/]+)/beer/(?P<beer_id>[^/]+)/$', beersubscriber_resource, name='beersubscriber'),
	url(r'^users/(?P<user_id>[^/]+)/bar/$', barsubscriber_list_resource),
	url(r'^users/(?P<user_id>[^/]+)/bar/(?P<bar_id>[^/]+)/$', barsubscriber_resource, name='barsubscriber'),

	url(r'^bar/(?P<bar_id>[^/]+)/$', bar_resource, name='bar'),
	url(r'^bar/$', bar_list_resource),

	url(r'^beer/(?P<beer_id>[^/]+)/$', beer_resource, name='beer'),
	
	url(r'^bar/(?P<bar_id>[^/]+)/beer/(?P<beer_id>[^/]+)/$', stockedbeer_resource, name='stockedbeer'),
	url(r'^bar/(?P<bar_id>[^/]+)/beer/$', stockedbeer_list_resource),
)
