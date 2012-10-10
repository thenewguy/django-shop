from django.conf import settings
from django.db import models
from django.db.models.base import ModelBase

from shop.util.loader import load_class

MODEL_PK_MAP = getattr(settings, 'SHOP_MODEL_PK_MAP', {})
MODEL_PK_MAP_DEFAULT = getattr(settings, 'SHOP_MODEL_PK_MAP_DEFAULT', None)
class ShopModelBaseClass(ModelBase):
    def _prepare(self):
        if self._meta.pk is None:
            data = MODEL_PK_MAP.get(self.__name__, MODEL_PK_MAP_DEFAULT)
            if data is not None:
                if isinstance(data, basestring):
                    data = {"class": data}
                args = data.get("args",[])
                kwargs = {
                    "verbose_name": "ID",
                    "primary_key": True
                }
                kwargs.update(data.get("kwargs", {}))
                field = load_class(data["class"])(*args, **kwargs)
                self.add_to_class('id', field)
        super(ShopModelBaseClass, self)._prepare()

class ShopModelBase(models.Model):
    class Meta:
        abstract = True
    __metaclass__ = ShopModelBaseClass
    