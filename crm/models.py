from django.db import models
from django.db.models import F, Sum
from django.core.validators import RegexValidator

from io import BytesIO
from django.http import HttpResponse
from django.template.loader import render_to_string
# import xlsxwriter
# from weasyprint import HTML
    
class Customer(models.Model):
    NATIONALITIES = [
        ('DZ', 'جزائري'),
        ('EG', 'مصري'),
        ('TN', 'تونسي'),
        ('LY', 'ليبي'),
        ('MA', 'مغربي'),
        ('SA', 'سعودي'),
        ('AE', 'إماراتي'),
    ]

    customer_code = models.CharField(max_length=20, primary_key=True)
    name = models.CharField(max_length=100)
    gender = models.CharField(max_length=10, choices=[('Male', 'Male'), ('Female', 'Female')])
    birth_date = models.DateField()
    address = models.CharField(max_length=255)
    nationality = models.CharField(max_length=100)
    phone_number = models.CharField(max_length=20, validators=[RegexValidator(r'^\+?1?\d{9,15}$', 'Enter a valid phone number.')])
    email = models.EmailField(unique=True)

    def __str__(self):
        return f"{self.customer_code} | {self.name}"

class Product(models.Model):
    product_code = models.CharField(max_length=20, primary_key=True)
    name = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    size = models.CharField(max_length=100, default='default_size', null=True, blank=True)
    sales_count = models.PositiveIntegerField(default=0, editable=False)

    def __str__(self):
        return f"{self.name}|{self.price}" 

class Invoice(models.Model):
    invoice_number = models.AutoField(primary_key=True)
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='invoices')
    issue_date = models.DateField()
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    def __str__(self):
        return f"Invoice #{self.invoice_number}"

    # Export Invoice with Orders as Excel
    def export_to_excel(self):
        output = BytesIO()
        workbook = xlsxwriter.Workbook(output)
        worksheet = workbook.add_worksheet()

        # Write header for the invoice
        worksheet.write(0, 0, "Invoice Number")
        worksheet.write(0, 1, "Customer Name")
        worksheet.write(0, 2, "Issue Date")
        worksheet.write(0, 3, "Total Amount")

        worksheet.write(1, 0, self.invoice_number)
        worksheet.write(1, 1, self.customer.name)  # assuming customer has 'name' field
        worksheet.write(1, 2, self.issue_date)
        worksheet.write(1, 3, self.total_amount)

        # Write header for the order details
        worksheet.write(3, 0, "Order ID")
        worksheet.write(3, 1, "Product")
        worksheet.write(3, 2, "Quantity")
        worksheet.write(3, 3, "Order Date")
        worksheet.write(3, 4, "Total Amount")

        row = 4
        for order in self.orders.all():  # Iterating through related orders
            worksheet.write(row, 0, order.id)
            worksheet.write(row, 1, order.product_code.name)  # assuming product has 'name' field
            worksheet.write(row, 2, order.quantity)
            worksheet.write(row, 3, order.order_date)
            worksheet.write(row, 4, order.product_code.price * order.quantity)
            row += 1

        workbook.close()
        output.seek(0)
        response = HttpResponse(output.read(), content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = f'attachment; filename=invoice_{self.invoice_number}.xlsx'
        return response

    # Export Invoice with Orders as PDF
    def export_to_pdf(self):
        # Rendering HTML to include invoice and its orders
        html_string = render_to_string('invoice_pdf_template.html', {'invoice': self})
        html = HTML(string=html_string)
        pdf = html.write_pdf()
        response = HttpResponse(pdf, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename=invoice_{self.invoice_number}.pdf'
        return response

class Order(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='orders')
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='orders', blank=True, null=True)
    product_code = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='orders')
    quantity = models.PositiveIntegerField()
    order_date = models.DateField()

    def save(self, *args, **kwargs):
        if self.pk:  # If it's an existing order, update the sales_count
            original_order = Order.objects.get(pk=self.pk)
            if original_order.quantity != self.quantity:
                product = self.product_code
                product.sales_count += self.quantity - original_order.quantity  # Adjust sales_count
                product.save()
        else:  # If it's a new order, update sales_count
            product = self.product_code
            product.sales_count += self.quantity
            product.save()

        if self.invoice:
            self.customer = self.invoice.customer
        # Save the Order
        super().save(*args, **kwargs)

        # Update the invoice's total amount
        if self.invoice:
            # Calculate the total for the current order
            order_total = self.product_code.price * self.quantity

            # Recalculate the total amount for the invoice by summing all orders
            total = Order.objects.filter(invoice=self.invoice).aggregate(
                total=Sum(F('product_code__price') * F('quantity'))
            )['total'] or 0

            # Update the invoice's total amount
            self.invoice.total_amount = total
            self.invoice.save()

    def __str__(self):
        return f'Order {self.id}'

