#-*- coding: utf-8 -*-
from django.core.urlresolvers import reverse
from django.contrib import admin
from django.contrib.admin.options import ModelAdmin
from django.utils.translation import ugettext_lazy as _
from django.conf import settings
from shop.admin.mixins import LocalizeDecimalFieldsMixin
from shop.models.ordermodel import (Order, OrderItem,
        OrderExtraInfo, ExtraOrderPriceField, OrderPayment,
        ExtraOrderItemPriceField)


class OrderExtraInfoInline(admin.TabularInline):
    model = OrderExtraInfo
    extra = 0


class OrderPaymentInline(LocalizeDecimalFieldsMixin, admin.TabularInline):
    model = OrderPayment
    extra = 0


class ExtraOrderPriceFieldInline(LocalizeDecimalFieldsMixin, admin.TabularInline):
    model = ExtraOrderPriceField
    extra = 0


class OrderItemInline(LocalizeDecimalFieldsMixin, admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ("ExtraOrderItemPriceFieldList",)
    
    def ExtraOrderItemPriceFieldList(self, obj):
        qs = ExtraOrderItemPriceField.objects.filter(order_item=obj)
        html = "<ul>"
        for eoipf in qs:
            html += """
                <li>
                    %(label)s, %(adjustment)s
                </li>
            """ % {
                'label': eoipf.label,
                'adjustment': '$(%s)' % abs(eoipf.value) if eoipf.value < 0 else '$%s' % eoipf.value
            }
        html += "</ul>"
        html += """
            <a href="%s">Edit Line Extras</a>
        """ % reverse("admin:%s_%s_change" % (obj._meta.app_label, obj._meta.module_name), args=(obj.pk,))
        return html
    ExtraOrderItemPriceFieldList.allow_tags = True
    ExtraOrderItemPriceFieldList.short_description = 'Line Extras'

class ExtraOrderItemPriceFieldInline(LocalizeDecimalFieldsMixin, admin.TabularInline):
    model = ExtraOrderItemPriceField
    extra = 0
    
class OrderItemAdmin(LocalizeDecimalFieldsMixin, ModelAdmin):
    inlines = (ExtraOrderItemPriceFieldInline,)

class OrderAdmin(LocalizeDecimalFieldsMixin, ModelAdmin):
    list_display = ('id', 'user', 'status', 'order_total', 'created')
    list_filter = ('status', 'user')
    search_fields = ('id', 'shipping_address_text', 'user__username')
    date_hierarchy = 'created'
    inlines = (OrderItemInline, OrderExtraInfoInline,
            ExtraOrderPriceFieldInline, OrderPaymentInline)
    readonly_fields = ('created', 'modified',)
    fieldsets = (
            (None, {'fields': ('user', 'status', 'order_total',
                'order_subtotal', 'created', 'modified')}),
            (_('Shipping'), {
                'fields': ('shipping_address_text',),
                }),
            (_('Billing'), {
                'fields': ('billing_address_text',)
                }),
            )


ORDER_MODEL = getattr(settings, 'SHOP_ORDER_MODEL', None)
if not ORDER_MODEL:
    admin.site.register(Order, OrderAdmin)
    admin.site.register(OrderItem, OrderItemAdmin)
