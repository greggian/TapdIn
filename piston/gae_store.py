import oauth

from gae_models import Nonce, Token, Consumer
from gae_models import generate_random, VERIFIER_SIZE


class DataStore(oauth.OAuthDataStore):
    """Layer between Python OAuth and Django database."""
    def __init__(self, oauth_request):
        self.signature = oauth_request.parameters.get('oauth_signature', None)
        self.timestamp = oauth_request.parameters.get('oauth_timestamp', None)
        self.scope = oauth_request.parameters.get('scope', 'all')
    
    def lookup_consumer(self, key):
        # try:
        #     self.consumer = Consumer.objects.get(key=key)
        #     return self.consumer
        # except Consumer.DoesNotExist:
        #     return None
        self.consumer = Consumer.all().filter('consumer_key =', key).get()
        return self.consumer
    
    def lookup_token(self, token_type, token):
        if token_type == 'request':
            token_type = Token.REQUEST
        elif token_type == 'access':
            token_type = Token.ACCESS
        # try:
        #     self.request_token = Token.objects.get(key=token, 
        #                                            token_type=token_type)
        #     return self.request_token
        # except Token.DoesNotExist:
        #     return None
        self.request_token = Token.all().filter('token_key =', token).filter('token_type =', token_type).get()
        return self.request_token
    
    def lookup_nonce(self, oauth_consumer, oauth_token, nonce):
        if oauth_token is None:
            return None
        # nonce, created = Nonce.objects.get_or_create(consumer_key=oauth_consumer.key, 
        #                                              token_key=oauth_token.key,
        #                                              key=nonce)
        # if created:
        #     return None
        # else:
        #     return nonce.key
        lookup_nonce = Nonce.all().filter('consumer_key =', oauth_consumer.key).filter('token_key =', oauth_token.key).filter('nonce_key =', nonce).get()
        if lookup_nonce: #If not created (i.e. found)
            return lookup_nonce.nonce_key
        else:
            lookup_nonce = Nonce(
                consumer_key=oauth_consumer.key,
                token_key=oauth_token.key,
                nonce_key=nonce
            )
            lookup_nonce.put()
            return None
    
    def fetch_request_token(self, oauth_consumer, oauth_callback):
        if oauth_consumer.key == self.consumer.consumer_key:
            # self.request_token = Token.objects.create_token(consumer=self.consumer,
            #                                                 token_type=Token.REQUEST,
            #                                                 timestamp=self.timestamp)
            self.request_token = Token.create_token(
                consumer=self.consumer,
                token_type=Token.REQUEST,
                timestamp=self.timestamp
            )
            if oauth_callback:
                self.request_token.set_callback(oauth_callback)
            return self.request_token
        return None
    
    def fetch_access_token(self, oauth_consumer, oauth_token, oauth_verifier):
        if oauth_consumer.key == self.consumer.consumer_key \
        and oauth_token.key == self.request_token.token_key \
        and oauth_verifier == self.request_token.verifier \
        and self.request_token.is_approved:
            # self.access_token = Token.objects.create_token(consumer=self.consumer,
            #                                                token_type=Token.ACCESS,
            #                                                timestamp=self.timestamp,
            #                                                user=self.request_token.user)
            self.access_token = Token.create_token(
                consumer=self.consumer,
                token_type=Token.ACCESS,
                timestamp=self.timestamp,
                user=self.request_token.user
            )
            return self.access_token
        return None
    
    def authorize_request_token(self, oauth_token, user):
        if oauth_token.key == self.request_token.token_key:
            # authorize the request token in the store
            self.request_token.is_approved = True
            self.request_token.user = user
            self.request_token.verifier = generate_random(VERIFIER_SIZE)
            self.request_token.put()
            return self.request_token
        return None
    

