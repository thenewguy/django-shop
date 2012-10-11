#-*- coding: utf-8 -*-
from django.http import HttpResponseRedirect
from django.shortcuts import redirect
from django.core.urlresolvers import reverse
from django.contrib import admin
from django.contrib.admin.options import ModelAdmin
from django.contrib.admin.util import unquote
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
    
    fields = ("order_pk", "line_item")
    readonly_fields = fields
    
    def order_pk(self, obj):
        return obj.order.pk
    order_pk.short_description = 'order'
    
    def line_item(self, obj):
        for i, pk in enumerate(OrderItem.objects.filter(order=obj.order).values_list('pk', flat=True), start=1):
            if pk == obj.pk:
                return u"%s" % i
        return u"Unknown"
    
    
    def get_model_perms(self, request):
        """
        Return empty perms dict thus hiding the model from admin index.
        """
        return {}
    
    def change_view(self, request, object_id, extra_context=None):
        item = self.get_object(request, unquote(object_id))
        order = item.order
        OrderOpts = order._meta
        has_change_permission_for_order =  request.user.has_perm(OrderOpts.app_label + '.' + OrderOpts.get_change_permission())
        context = {
            'OrderItem': item,
            'Order': order,
            'OrderOpts': OrderOpts,
            'has_change_permission_for_order': has_change_permission_for_order,
            'line_item': self.line_item(item)
        }
        context.update(extra_context or {})
        
        response = super(OrderItemAdmin, self).change_view(request, object_id, extra_context=context)
        
        if isinstance(response, HttpResponseRedirect):
            if item:
                order = item.order
                to = reverse("admin:%s_%s_change" % (
                        order._meta.app_label,
                        order._meta.module_name
                     ),
                     args=(order.pk,)
                )
                response = redirect(to)
        
        return response


class OrderAdmin(LocalizeDecimalFieldsMixin, ModelAdmin):
    list_display = ('pk', 'user', 'status', 'order_total', 'created')
    list_filter = ('status', 'user')
    search_fields = ('pk', 'shipping_address_text', 'user__username')
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
