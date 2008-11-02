from __future__ import with_statement
import datetime
import hashlib
import operator
import os
import time

from django.conf import settings
from django.contrib import admin
from django.core.cache import cache
from django.db import models
from django.db.models.query import Q


class MediaGroup(models.Model):
    parent = models.ForeignKey('self', related_name='children', null=True,
        blank=True)
    name = models.CharField(max_length=32, unique=True)
    full_name = models.CharField(max_length=64)
    canonical_name = models.CharField(max_length=256, editable=False)
    
    def canonicalize(self):
        if self.parent:
            return '%s.%s' % (self.name, self.parent.canonical_name)
        return self.name
    
    def __unicode__(self):
        return '%s (%s)' % (self.canonical_name, self.full_name)


class MediaAlias(models.Model):
    group = models.ForeignKey(MediaGroup, related_name='media_aliases',
        null=False)
    alias = models.CharField(max_length=32)
    canonical_name = models.CharField(max_length=256, editable=False)
    filename = models.FilePathField(path=settings.MEDIA_ROOT)
    last_modified = models.DateTimeField(editable=False)
    filesize = models.PositiveIntegerField(editable=False)
    hashed = models.CharField(max_length=40, editable=False)
    
    def open(self, mode='r'):
        return open(self.filename, mode=mode)
    
    def read(self, from_cache=True, invalidate=False):
        if invalidate:
            data = self.read(from_cache=False)
            cache.set('media_alias_%s' % (self.hashed,), data, 3600)
            return data
        if from_cache:
            data = cache.get('media_alias_%s' % (self.hashed,))
            if not data:
                data = self.read(invalidate=True)
            return data
        else:
            with self.open() as fp:
                data = fp.read()
            self.save()
            return data
    
    def canonicalize(self):
        return '%s.%s' % (self.alias, self.group.canonical_name)
    
    def get_hash(self):
        return hashlib.new('sha1', '%s:%s:%d' % (self.canonical_name,
            self.last_modified.isoformat(), self.filesize)).hexdigest()
    
    def __unicode__(self):
        return '%s (%s)' % (self.canonical_name, self.filename)
    
    class Meta(object):
        verbose_name = 'Media alias'
        verbose_name_plural = 'Media aliases'
        unique_together = (('group', 'alias'),)


## Signals ##
def update_group_cache(sender, instance, *args, **kwargs):
    instance.canonical_name = instance.canonicalize()
models.signals.pre_save.connect(update_group_cache, sender=MediaGroup)

def update_alias_cache(sender, instance, *args, **kwargs):
    instance.canonical_name = instance.canonicalize()
    instance.last_modified = datetime.datetime.fromtimestamp(
        os.path.getmtime(instance.filename))
    instance.filesize = os.path.getsize(instance.filename)
    instance.hashed = instance.get_hash()
models.signals.pre_save.connect(update_alias_cache, sender=MediaAlias)


## Admin site registration ##
admin.site.register(MediaGroup)
admin.site.register(MediaAlias)
