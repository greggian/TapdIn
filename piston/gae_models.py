import urllib, time, urlparse

# Django imports
from django.db.models.signals import post_save, post_delete
from django.contrib.auth.models import User
from django.core.mail import send_mail, mail_admins

from google.appengine.ext import db

# Piston imports
# from managers import TokenManager, ConsumerManager, ResourceManager
from signals import consumer_post_save, consumer_post_delete

KEY_SIZE = 18
SECRET_SIZE = 32
VERIFIER_SIZE = 10

CONSUMER_STATES = (
    ('pending', 'Pending'),
    ('accepted', 'Accepted'),
    ('canceled', 'Canceled'),
    ('rejected', 'Rejected')
)
CONSUMER_STATES_LIST = [s[0] for s in CONSUMER_STATES]

def make_random_password(
        self,
        length=10,
        allowed_chars='abcdefghjkmnpqrstuvwxyzABCDEFGHJKLMNPQRSTUVWXYZ23456789'
    ):
    """
    Generates a random password with the given length and given allowed_chars.
    Lifted from django.contrib.auth.models.UserManager
    """
    # Note that default value of allowed_chars does not have "I" or letters
    # that look like it -- just to avoid confusion.
    from random import choice
    return ''.join([choice(allowed_chars) for i in range(length)])

def generate_random(length=SECRET_SIZE):
    return make_random_password(length=length)


class KeyManager(object):
    @classmethod
    def get_or_create(cls, *args, **kwargs):
        created = False
        query = cls.all()
        for key, value in kwargs.items():
            query = query.filter('%s =' % key, value)
        object = query.get()
        if object is None:
            object = cls(**kwargs)
            object.put()
            created = True
        return object, created
    
    @classmethod
    def generate_random_codes(cls, keyprop='key', secretprop='secret'):
        key = make_random_password(length=KEY_SIZE)
        secret = make_random_password(length=SECRET_SIZE)
        while cls.all().filter('%s =' % keyprop, key).filter('%s =' % secretprop, secret).get():
            secret = make_random_password(length=SECRET_SIZE)
        return key, secret
    

class Nonce(db.Model):
    # token_key = models.CharField(max_length=KEY_SIZE)
    # consumer_key = models.CharField(max_length=KEY_SIZE)
    # key = models.CharField(max_length=255)
    token_key = db.StringProperty(required=True)
    consumer_key = db.StringProperty(required=True)
    nonce_key = db.StringProperty(required=True)
    
    def __unicode__(self):
        return u"Nonce %s for %s" % (self.nonce_key, self.consumer_key)

class Consumer(db.Model, KeyManager):
    # name = models.CharField(max_length=255)
    # description = models.TextField()
    # 
    # key = models.CharField(max_length=KEY_SIZE)
    # secret = models.CharField(max_length=SECRET_SIZE)
    # 
    # status = models.CharField(max_length=16, choices=CONSUMER_STATES, default='pending')
    # user = models.ForeignKey(User, null=True, blank=True, related_name='consumers')
    # 
    # objects = ConsumerManager()
    name = db.StringProperty(required=True)
    description = db.TextProperty(require=True)
    consumer_key = db.StringProperty(required=True)
    secret = db.StringProperty(required=True)
    status = db.StringProperty(
        required=True, default='pending', choices=CONSUMER_STATES_LIST
    )
    user = db.ReferenceProperty(
        reference_class=User, collection_name='consumers', required=False
    )
    
    def __unicode__(self):
        return u"Consumer %s with key %s" % (self.name, self.consumer_key)
    
    @classmethod
    def create_consumer(cls, name, description=None, user=None):
        """
        Shortcut to create a consumer with random key/secret.
        """
        consumer, created = cls.get_or_create(name=name)
        if consumer is None:
            return None
        if user:
            consumer.user = user
        if description:
            consumer.description = description
        if created:
            consumer.consumer_key, consumer.secret = cls.generate_random_codes(
                keyprop='consumer_key'
            )
        consumer.put()
        return consumer
    

class Token(db.Model, KeyManager):
    REQUEST = 1
    ACCESS = 2
    TOKEN_TYPES = ((REQUEST, u'Request'), (ACCESS, u'Access'))
    TOKEN_TYPES_LIST = [t[0] for t in TOKEN_TYPES]
    
    # key = models.CharField(max_length=KEY_SIZE)
    # secret = models.CharField(max_length=SECRET_SIZE)
    # verifier = models.CharField(max_length=VERIFIER_SIZE)
    # token_type = models.IntegerField(choices=TOKEN_TYPES)
    # timestamp = models.IntegerField(default=long(time.time()))
    # is_approved = models.BooleanField(default=False)
    # 
    # user = models.ForeignKey(User, null=True, blank=True, related_name='tokens')
    # consumer = models.ForeignKey(Consumer)
    # 
    # callback = models.CharField(max_length=255, null=True, blank=True)
    # callback_confirmed = models.BooleanField(default=False)
    # 
    # objects = TokenManager()
    token_key = db.StringProperty(required=True)
    secret = db.StringProperty(required=True)
    verifier = db.StringProperty(required=True)
    token_type = db.IntegerProperty(required=True, choices=TOKEN_TYPES_LIST)
    timestamp = db.IntegerProperty(required=False)
    is_approved = db.BooleanProperty(required=False, default=False)
    user = db.ReferenceProperty(
        reference_class=User, collection_name='tokens', required=False
    )
    consumer = db.ReferenceProperty(reference_class=Consumer)
    callback = db.StringProperty(required=False)
    callback_confirmed = db.BooleanProperty(required=False, default=False)
    
    def __unicode__(self):
        return u"%s Token %s for %s" % (
            self.get_token_type_display(), self.token_key, self.consumer
        )
    
    def to_string(self, only_key=False):
        token_dict = {
            'oauth_token': self.token_key, 
            'oauth_token_secret': self.secret,
            'oauth_callback_confirmed': 'true',
        }
        if self.verifier:
            token_dict.update({'oauth_verifier' : self.verifier})
        if only_key:
            del token_dict['oauth_token_secret']
        return urllib.urlencode(token_dict)
    
    # -- OAuth 1.0a stuff
    def get_callback_url(self):
        if self.callback and self.verifier:
            # Append the oauth_verifier.
            parts = urlparse.urlparse(self.callback)
            scheme, netloc, path, params, query, fragment = parts[:6]
            if query:
                query = '%s&oauth_verifier=%s' % (query, self.verifier)
            else:
                query = 'oauth_verifier=%s' % self.verifier
            return urlparse.urlunparse((scheme, netloc, path, params,
                query, fragment))
        return self.callback
    
    def set_callback(self, callback):
        if callback != "oob": # out of band, says "we can't do this!"
            self.callback = callback
            self.callback_confirmed = True
            self.put()
    
    @classmethod
    def create_token(cls, consumer, token_type, timestamp, user=None):
        """
        Shortcut to create a token with random key/secret.
        """
        token, created = cls.get_or_create(
            consumer=consumer,
            token_type=token_type,
            timestamp=timestamp,
            user=user
        )
        if created:
            token.token_key, token.secret = cls.generate_random_codes(
                keyprop='token_key'
            )
            token.put()
        return token
    


# Attach our signals
post_save.connect(consumer_post_save, sender=Consumer)
post_delete.connect(consumer_post_delete, sender=Consumer)
