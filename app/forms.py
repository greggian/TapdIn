from google.appengine.ext.db import djangoforms
from app import models



class BarForm(djangoforms.ModelForm):
	class Meta:
		model = models.Bar
		fields = ('name', 'remote_url', 'added_on', 'updated_on', 'location')


class BeerForm(djangoforms.ModelForm):
	class Meta:
		model = models.Beer
		exclude = ['name_parts']
