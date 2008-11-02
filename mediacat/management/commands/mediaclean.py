from django.core.management.base import BaseCommand

from mediacat.models import MediaAlias


class Command(BaseCommand):
    help = 'Refresh cache for django-mediacat.'
    args = '[alias1, [alias2, ...]]'
    
    def handle(self, *args):
        if args:
            for alias_canon_name in args:
                try:
                    alias = MediaAlias.get(canonical_name=alias_canon_name)
                except MediaAlias.DoesNotExist:
                    print 'Skipping "%s": alias not found' % (alias_canon_name,)
                    continue
                print 'Invalidating cache for alias "%s"' % (alias_canon_name,)
                alias.read(invalidate=True)
                alias.save()
        else:
            for alias in MediaAlias.objects.all():
                print 'Invalidating cache for alias "%s"' % (
                    alias.canonical_name,)
                alias.read(invalidate=True)
                alias.save()
