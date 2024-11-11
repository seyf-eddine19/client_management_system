from django.contrib import admin
from import_export.admin import ImportExportModelAdmin
from import_export import resources
from .models import Customer, Order, Product, Invoice
from django.db.models.functions import TruncMonth
from django.db.models import Count, Sum, F
from django.utils.timezone import now

# Define the resources for each model

class CustomerResource(resources.ModelResource):
    class Meta:
        model = Customer

class OrderResource(resources.ModelResource):
    class Meta:
        model = Order

class ProductResource(resources.ModelResource):
    class Meta:
        model = Product

class InvoiceResource(resources.ModelResource):
    class Meta:
        model = Invoice


class CustomAdminSite(admin.AdminSite):
    site_title = 'CRM Admin'
    site_header = 'CRM Administration'
    index_title = 'CRM Dashboard'

    def index(self, request, extra_context=None):
        # Extra context for most sold products and premium customers
        extra_context = extra_context or {}

        # Most sold products (using Sum to get total quantity ordered for each product)
        most_sold_products = Product.objects.annotate(total_sold=Sum('orders__quantity')).order_by('-total_sold')[:5]
        extra_context['most_sold_products'] = most_sold_products

        # Premium customers (e.g., based on total number of orders or invoices)
        premium_customers = Customer.objects.annotate(total_orders=Sum('orders__quantity')).order_by('-total_orders')[:5]
        extra_context['premium_customers'] = premium_customers
        # Product inventory
        products = Product.objects.all()
        extra_context['products'] = products

        # Sales trends (monthly sales total)
        current_year = now().year
        sales_data = Order.objects.filter(order_date__year=current_year).annotate(month=TruncMonth('order_date')).values('month').annotate(total_sales=Sum(F('product_code__price') * F('quantity'))).order_by('month')
        extra_context['sales_data'] = sales_data

        return super().index(request, extra_context)

# Instantiate the custom admin site
admin.site = CustomAdminSite(name='custom_admin')
admin.site.index_template = 'admin/dashboard.html'

class OrderInline(admin.TabularInline):
    model = Order
    extra = 1
    fields = ['product_code', 'quantity', 'order_date']
    
    # Override save_formset to set the customer automatically
    def save_formset(self, request, form, formset, change):
        instances = formset.save(commit=False)
        for instance in instances:
            if isinstance(instance, Order):
                instance.customer = form.instance  # Set customer from the parent instance (Customer)
            instance.save()
        formset.save_m2m()

class CustomerAdmin(ImportExportModelAdmin):
    resource_class = CustomerResource
    list_display = ['customer_code', 'name', 'gender', 'birth_date', 'address', 'phone_number', 'email']
    search_fields = ['name', 'email']
    filter = ['gender']
    inlines = [OrderInline]

class OrderAdmin(ImportExportModelAdmin):
    resource_class = OrderResource
    list_display = ['id', 'customer', 'product_code', 'quantity', 'order_date']
    search_fields = ['id', 'product_code']

class ProductAdmin(ImportExportModelAdmin):
    resource_class = ProductResource
    list_display = ['product_code', 'name', 'price', 'quantity']
    search_fields = ['product_code', 'name']

class InvoiceAdmin(ImportExportModelAdmin):
    resource_class = InvoiceResource
    list_display = ['invoice_number', 'customer', 'issue_date', 'total_amount']
    search_fields = ['invoice_number', 'customer']
    inlines = [OrderInline]
    

admin.site.register(Customer, CustomerAdmin)
admin.site.register(Product, ProductAdmin)
admin.site.register(Order, OrderAdmin)
admin.site.register(Invoice, InvoiceAdmin)
