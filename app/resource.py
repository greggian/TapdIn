import re
import mimeparse
import piston.resource
from piston.emitters import Emitter
import logging

class Resource(piston.resource.Resource):
    """Chooses an emitter based on mime types."""
   
    mime_regex = re.compile('[/;]')
 
    def determine_emitter(self, request, *args, **kwargs):
        # First look for a format hardcoded into the URLconf
        em = kwargs.pop('emitter_format', None)
        
        # Then look for ?format=json
        if not em:
            em = request.GET.get('format', None)
        
        # Then try the accept header
        if not em and 'HTTP_ACCEPT' in request.META:
            mimetypes = [mime for klass, mime in Emitter.EMITTERS.values()]
	    mime = mimeparse.best_match(mimetypes,
                                        request.META['HTTP_ACCEPT'])
            if mime:
                em = self.mime_regex.split(mime)[1]
 
        # Finally fall back on HTML
        return em #or 'html'

