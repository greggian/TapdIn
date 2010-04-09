import piston.emitters
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render_to_response
from django.template import RequestContext

class HTMLTemplateEmitter(piston.emitters.Emitter):
	
	def render(self, request):
                if isinstance(self.data, HttpResponse):
                        referrer = request.META.get('HTTP_REFERER')
                        if referrer:
                                return HttpResponseRedirect(referrer)

		return render_to_response(
			template_name = '%s.html' % self.handler.viewname.lower(),
			dictionary = self.data,#self.construct(),
			context_instance = RequestContext(request)
		)

#register out HTML Emitter with piston
piston.emitters.Emitter.register('html', HTMLTemplateEmitter, 'text/html')
