from django.contrib import admin
from import_export.admin import ImportExportModelAdmin
from import_export import resources
from .models import Customer, Order, Product, Invoice
from django.db.models.functions import TruncMonth
from django.db.models import Count, Sum, F
from django.utils.timezone import now
from datetime import datetime
from django.urls import path
from django.shortcuts import redirect, get_object_or_404
from django import forms
from django.forms import DateInput

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


class CustomerForm(forms.ModelForm):
    birth_date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'vTextField'})
    )
    class Meta:
        model = Customer
        fields = '__all__'

class OrderForm(forms.ModelForm):
    order_date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'vTextField'})
    )
    class Meta:
        model = Order
        fields = '__all__'

class OrderInline(admin.TabularInline):
    model = Order
    form = OrderForm
    extra = 1
    fields = ['product_code', 'quantity']

    # Override save_formset to set the customer automatically
    def save_formset(self, request, form, formset, change):
        instances = formset.save(commit=False)
        for instance in instances:
            if isinstance(instance, Order):
                instance.customer = form.instance  # Set customer from the parent instance (Customer)
            instance.save()
        formset.save_m2m()

class CustomerAdmin(ImportExportModelAdmin):
    form = CustomerForm
    resource_class = CustomerResource
    list_display = ['customer_code', 'name', 'gender', 'birth_date', 'address', 'nationality', 'phone_number', 'email']
    search_fields = ['customer_code', 'phone_number', 'name']  # البحث باستخدام الكود ورقم الهاتف
    list_filter = ['address', 'nationality', 'gender']  # فلتر حسب العنوان والجنس
    inlines = [OrderInline]
    
class OrderAdmin(ImportExportModelAdmin):
    resource_class = OrderResource
    form = OrderForm
    list_display = ['id', 'customer', 'product_code', 'quantity', 'order_date']
    list_filter = ['product_code', 'customer']
    search_fields = ['id', 'product_code', 'customer']
    autocomplete_fields = ['customer'] 

class ProductAdmin(ImportExportModelAdmin):
    resource_class = ProductResource
    list_display = ['product_code', 'name', 'price', 'size', 'sales_count']
    search_fields = ['product_code', 'name']

class InvoiceAdmin(ImportExportModelAdmin):
    resource_class = InvoiceResource
    list_display = ['invoice_number', 'customer', 'issue_date', 'total_amount']
    search_fields = ['invoice_number', 'customer']
    inlines = [OrderInline]
    change_form_template = 'admin/crm/invoice_change_form.html'

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('export_invoice/<int:invoice_id>/excel/', self.export_invoice_excel),
            path('export_invoice/<int:invoice_id>/pdf/', self.export_invoice_pdf),
        ]
        return custom_urls + urls

    def export_invoice_excel(self, request, invoice_id):
        invoice = Invoice.objects.get(pk=invoice_id)
        return invoice.export_to_excel()

    def export_invoice_pdf(self, request, invoice_id):
        invoice = Invoice.objects.get(pk=invoice_id)
        return invoice.export_to_pdf()
    
class InvoiceAdmin1(ImportExportModelAdmin):
    resource_class = InvoiceResource
    list_display = ['invoice_number', 'customer', 'issue_date', 'total_amount']
    search_fields = ['invoice_number', 'customer']
    inlines = [OrderInline]
    change_form_template = 'admin/crm/invoice_change_form.html'

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('export_invoice/<int:invoice_id>/excel/', self.export_invoice_excel),
            path('export_invoice/<int:invoice_id>/pdf/', self.export_invoice_pdf),
        ]
        return custom_urls + urls

    def export_invoice_excel(self, request, invoice_id):
        invoice = get_object_or_404(Invoice, pk=invoice_id)
        return invoice.export_to_excel()

    def export_invoice_pdf(self, request, invoice_id):
        invoice = get_object_or_404(Invoice, pk=invoice_id)
        return invoice.export_to_pdf()

    def add_view(self, request, form_url='', extra_context=None):
        last_invoice = Invoice.objects.order_by('invoice_number').last()
        invoice_number = (last_invoice.invoice_number + 1) if last_invoice else 1
        invoice = Invoice.objects.create(invoice_number=invoice_number)
        # self.change_view(request, object_id=None, form_url=form_url, extra_context=extra_context)
        return redirect('admin:crm_invoice_change', object_id=invoice.pk)
    
    def change_view(self, request, object_id=None, form_url='', extra_context=None):
        if extra_context is None:
            extra_context = {}

        customers = Customer.objects.all()
        products = Product.objects.all()
        print(object_id)
        if not object_id:
            invoice = None
            orders = []
            orders_with_totals = []
            last_invoice = Invoice.objects.order_by('invoice_number').last()
            invoice_number = (last_invoice.invoice_number + 1) if last_invoice else 1
        else: 
            invoice = get_object_or_404(Invoice, pk=object_id)
            orders = invoice.orders.all() 
            orders_with_totals = [
                {
                    'order': order,
                    'order_total': order.product_code.price * order.quantity
                }
                for order in orders
            ]

        extra_context.update({
            'customers': customers,
            'products': products,
            'invoice': invoice,
            'orders_with_totals': orders_with_totals,
        })
            
        if request.method == 'POST':
            customer_id = request.POST.get('id_customer')
            issue_date = request.POST.get('issue_date')
            total_amount = request.POST.get('total_amount')
            order_ids = request.POST.getlist('order_ids')
            product_codes = request.POST.getlist('product_codes')
            quantities = request.POST.getlist('quantities')
    
            customer = get_object_or_404(Customer, pk=customer_id)

            if not invoice:
                # invoice_number = request.POST.get('invoice_number')

                last_invoice = Invoice.objects.order_by('invoice_number').last()
                invoice_number = (last_invoice.invoice_number + 1) if last_invoice else 1

                invoice = Invoice.objects.create(
                    invoice_number=invoice_number,
                    customer=customer,
                    issue_date=issue_date,
                    total_amount=total_amount
                )
            else:
                invoice.customer = customer
                invoice.issue_date = issue_date
                invoice.total_amount = total_amount
                invoice.save()
    
            for order_id, product_code, quantity in zip(order_ids, product_codes, quantities):
                product = get_object_or_404(Product, pk=product_code)
                quantity = int(quantity) if quantity.isdigit() else 1  # Fallback to 1 if not valid
        
                if not order_id:
                    order = Order.objects.create(
                        invoice=invoice,
                        customer=customer,
                        product_code=product,
                        quantity=quantity,
                        order_date=issue_date
                    )
                else:
                    order = Order.objects.get(pk=order_id)
                    order.customer=customer
                    order.product_code = product  
                    order.quantity = quantity
                    order.order_date=issue_date
                    order.save()

            return redirect('admin:crm_invoice_change', object_id=invoice.pk)
    
        return super().change_view(request, object_id, form_url, extra_context=extra_context)

class InvoiceAdmin(ImportExportModelAdmin):
    resource_class = InvoiceResource
    list_display = ['invoice_number', 'customer', 'issue_date', 'total_amount']
    search_fields = ['invoice_number', 'customer']
    inlines = [OrderInline]
    change_form_template = 'admin/crm/invoice_change_form.html'

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('export_invoice/<int:invoice_id>/excel/', self.export_invoice_excel),
            path('export_invoice/<int:invoice_id>/pdf/', self.export_invoice_pdf),
        ]
        return custom_urls + urls

    def export_invoice_excel(self, request, invoice_id):
        invoice = get_object_or_404(Invoice, pk=invoice_id)
        return invoice.export_to_excel()

    def export_invoice_pdf(self, request, invoice_id):
        invoice = get_object_or_404(Invoice, pk=invoice_id)
        return invoice.export_to_pdf()

    def add_view(self, request, form_url='', extra_context=None):
        if extra_context is None:
            extra_context = {}

        customers = Customer.objects.all()
        products = Product.objects.all()
        orders_with_totals = []
        invoice = None
        last_invoice = Invoice.objects.order_by('invoice_number').last()
        invoice_number = (last_invoice.invoice_number + 1) if last_invoice else 1

        extra_context.update({
            'invoice': invoice,
            'customers': customers,
            'products': products,
            'orders_with_totals': orders_with_totals,
            'invoice_number': invoice_number,
        })

        if request.method == 'POST':
            customer_id = request.POST.get('id_customer')
            issue_date = request.POST.get('issue_date')
            total_amount = request.POST.get('total_amount')
            order_ids = request.POST.getlist('order_ids')
            product_codes = request.POST.getlist('product_codes')
            quantities = request.POST.getlist('quantities')

            customer = get_object_or_404(Customer, pk=customer_id)

            invoice = Invoice.objects.create(
                invoice_number=invoice_number,
                customer=customer,
                issue_date=issue_date,
                total_amount=total_amount
            )
            for order_id, product_code, quantity in zip(order_ids, product_codes, quantities):
                product = get_object_or_404(Product, pk=product_code)
                quantity = int(quantity) if quantity.isdigit() else 1

                order = Order.objects.create(
                    invoice=invoice,
                    customer=customer,
                    product_code=product,
                    quantity=quantity,
                    order_date=issue_date
                )

            return redirect('admin:crm_invoice_change', object_id=invoice.pk)

        return super().change_view(request, object_id=None, form_url=form_url, extra_context=extra_context)

    def change_view(self, request, object_id=None, form_url='', extra_context=None):
        if extra_context is None:
            extra_context = {}

        customers = Customer.objects.all()
        products = Product.objects.all()
        invoice = get_object_or_404(Invoice, pk=object_id)
        orders = invoice.orders.all()
        orders_with_totals = [
            {
                'order': order,
                'order_total': order.product_code.price * order.quantity
            }
            for order in orders
        ]

        extra_context.update({
            'invoice': invoice,
            'customers': customers,
            'products': products,
            'orders_with_totals': orders_with_totals,
        })

        if request.method == 'POST':
            customer_id = request.POST.get('id_customer')
            issue_date = request.POST.get('issue_date')
            total_amount = request.POST.get('total_amount')
            order_ids = request.POST.getlist('order_ids')
            product_codes = request.POST.getlist('product_codes')
            quantities = request.POST.getlist('quantities')

            customer = get_object_or_404(Customer, pk=customer_id)

            invoice.customer = customer
            invoice.issue_date = issue_date
            invoice.total_amount = total_amount
            invoice.save()

            for order_id, product_code, quantity in zip(order_ids, product_codes, quantities):
                product = get_object_or_404(Product, pk=product_code)
                quantity = int(quantity) if quantity.isdigit() else 1  # Fallback to 1 if not valid

                if not order_id:
                    order = Order.objects.create(
                        invoice=invoice,
                        customer=customer,
                        product_code=product,
                        quantity=quantity,
                        order_date=issue_date
                    )
                else:
                    order = Order.objects.get(pk=order_id)
                    order.customer = customer
                    order.product_code = product
                    order.quantity = quantity
                    order.order_date = issue_date
                    order.save()

            return redirect('admin:crm_invoice_change', object_id=invoice.pk)

        return super().change_view(request, object_id, form_url, extra_context=extra_context)


class CustomAdminSite(admin.AdminSite):
    site_title = 'CRM Admin'
    site_header = 'CRM Administration'
    index_title = 'CRM Dashboard'
    formfield_overrides = {
        forms.DateField: {'widget': DateInput(attrs={'type': 'date', 'class':'date'})},
        forms.DateTimeField: {'widget': DateInput(attrs={'type': 'datetime-local'})},
    }
    
    def index(self, request, extra_context=None):
        # Get the current month and year
        current_month = now().month
        current_year = now().year

        month_filter = int(request.GET.get('month_filter', current_month))
        year_filter = int(request.GET.get('year_filter', current_year))  # Default to current year
        # nationality_filter = request.GET.get('nationality_filter', 'All')  # Default to show all nationalities

        # Most sold products (using Sum to get total quantity ordered for each product)
        most_sold_products = Product.objects.annotate(
            total_sold=Sum('orders__quantity')
        ).order_by('-total_sold')[:10]

        # Premium customers (e.g., based on total number of orders or invoices)
        premium_customers = Customer.objects.annotate(
            total_orders=Count('orders')
            ).order_by('-total_orders')[:10]

        # Filter to show Products Sales by Month and Year
        products = Product.objects.annotate(
            total_sold=Sum('orders__quantity')
        ).filter(
            # orders__customer__nationality=nationality_filter,
            orders__order_date__month=month_filter,
            orders__order_date__year=year_filter 
        ).order_by('-total_sold')

        # Sales Trends (filtered by year)
        sales_data = Order.objects.filter(
            # customer__nationality=nationality_filter,
            order_date__year=year_filter
        ).annotate(
            month=TruncMonth('order_date')
        ).values('month').annotate(
            total_sales=Sum(F('quantity'))
        ).order_by('month')


        # Sales by Address (grouped by customer nationality)
        
        sales_by_address = Order.objects.values('customer__address').filter(
            order_date__month=month_filter,
            order_date__year=year_filter 
        ).annotate(
            total_sales=Sum(F('quantity'))
        ).order_by('-total_sales')
            
        months = [(i, datetime(2024, i, 1).strftime('%B')) for i in range(1, 13)]
        # unique_nationalities = Customer.objects.values_list(F('nationality'), flat=True).distinct()

        extra_context = extra_context or {}
        extra_context['most_sold_products'] = most_sold_products
        extra_context['premium_customers'] = premium_customers
        extra_context['products'] = products
        extra_context['sales_data'] = sales_data
        extra_context['sales_by_address'] = sales_by_address
        
        extra_context['month_filter'] = month_filter 
        extra_context['year_filter'] = year_filter
        # extra_context['nationality_filter'] = nationality_filter
        extra_context['months'] = months #list(range(1, 13))  # 1 to 12 for months
        extra_context['years'] = list(range(current_year - 5, current_year + 1))
        # extra_context['unique_nationalities'] = unique_nationalities

        return super().index(request, extra_context=extra_context)

# Instantiate the custom admin site
admin.site = CustomAdminSite(name='custom_admin')
admin.site.index_template = 'admin/dashboard.html'

admin.site.register(Customer, CustomerAdmin)
admin.site.register(Product, ProductAdmin)
admin.site.register(Order, OrderAdmin)
admin.site.register(Invoice, InvoiceAdmin)
