from __future__ import with_statement
import hashlib
import os
import warnings

from django.core.cache import cache
from django.http import HttpResponse, Http404
from django.utils.http import http_date

from mediacat.models import MediaAlias


def cat(request):
    aliases = []
    for canon_name in request.GET.keys():
        try:
            aliases.append(MediaAlias.objects.get(canonical_name=canon_name))
        except MediaAlias.DoesNotExist:
            warnings.warn('Alias not found: %s' % (canon_name,))
    if not aliases:
        raise Http404
    e_tag = hashlib.new('sha1', ''.join(alias.hashed for alias in
                    sorted(aliases,
                        key=(lambda a: a.canonical_name)))).hexdigest()
    last_modified = max(alias.last_modified for alias in aliases)
    response = HttpResponse()
    # Write response information, and client-side caching information.
    response['Date'] = http_date()
    response['ETag'] = e_tag
    response['Last-Modified'] = last_modified.strftime(
        '%a, %d %b %Y %H:%M:%S GMT') # RFC 1123 date format for HTTP
    response['Content-Length'] = sum(alias.filesize for alias in aliases)
    # Client-side cache checks:
    if_modified_since = request.META.get('HTTP_IF_MODIFIED_SINCE', None)
    client_e_tag = request.META.get('HTTP_IF_NONE_MATCH', None)
    if client_e_tag == e_tag:
        response.status_code = 304
        return response
    elif last_modified == if_modified_since:
        response.status_code = 304
        return response
    # If the user does not have a valid cache:
    for alias in aliases:
        response.write(alias.read())
    return response