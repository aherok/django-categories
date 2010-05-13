import re
from django.core.urlresolvers import reverse
from django.db.models import permalink
from django.db import models
from django.utils.encoding import force_unicode
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic
from django.utils.translation import ugettext as _

import mptt

from settings import RELATION_MODELS, RELATIONS

class Category(models.Model):
    parent = models.ForeignKey('self', 
        blank=True, 
        null=True, 
        related_name="children", 
        help_text="Leave this blank for an Category Tree", 
        verbose_name='Parent')
    name = models.CharField(max_length=100)
    full_name = models.CharField(max_length=500)
    order = models.IntegerField(blank=True, null=True)
    slug = models.SlugField()
    alternate_title = models.CharField(
        blank=True,
        default="",
        max_length=100,
        help_text="An alternative title to use on pages with this category."
    )
    description = models.TextField(blank=True, null=True)
    meta_keywords = models.CharField(
        blank=True,
        default="",
        max_length=255,
        help_text="Comma-separated keywords for search engines.")
    meta_extra = models.TextField(
        blank=True,
        default="",
        help_text="(Advanced) Any additional HTML to be placed verbatim in the &lt;head&gt;")
    
    
    def get_absolute_url(self):
        """Return a path"""
        prefix = reverse('categories_tree_list')
        ancestors = list(self.get_ancestors()) + [self,]
        return prefix + '/'.join([force_unicode(i.slug) for i in ancestors]) + '/'
        
    class Meta:
        verbose_name_plural = 'categories'
        unique_together = ('parent', 'name')
        ordering = ('tree_id','lft')

    def __unicode__(self):
        return self.full_name
    
    # overriden to update full_name if necessary
    def save(self, *args, **kwargs):
        super(Category, self).save(*args, **kwargs)
        self.update_name()
    
    # method checks if we need to update full_name
    def update_name(self):
        sep = ' > '
        if self.parent is not None:
            parent_name = self.parent.full_name + sep
        else:
            parent_name = ""
        
        if parent_name + self.name != self.full_name:
            self.full_name = parent_name + self.name
            self.save()
            for c in self.get_children():
                c.update_name()
        
try: mptt.register(Category, order_insertion_by=['name'])
except: pass

if RELATION_MODELS:
    category_relation_limits = reduce(lambda x,y: x|y, RELATIONS)
    class CategoryRelationManager(models.Manager):
        def get_content_type(self, content_type):
            qs = self.get_query_set()
            return qs.filter(content_type__name=content_type)
        
        def get_relation_type(self, relation_type):
            qs = self.get_query_set()
            return qs.filter(relation_type=relation_type)
    
    
    class CategoryRelation(models.Model):
        """Related story item"""
        story = models.ForeignKey(Category)
        content_type = models.ForeignKey(ContentType, limit_choices_to=category_relation_limits)
        object_id = models.PositiveIntegerField()
        content_object = generic.GenericForeignKey('content_type', 'object_id')
        relation_type = models.CharField(_("Relation Type"), 
            max_length="200", 
            blank=True, 
            null=True,
            help_text=_("A generic text field to tag a relation, like 'leadphoto'."))
        
        objects = CategoryRelationManager()
        
        def __unicode__(self):
            return u"CategoryRelation"
