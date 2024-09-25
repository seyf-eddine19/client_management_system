from django.db import models
from django.db.models import F, Sum

class Customer(models.Model):
    customer_code = models.CharField(max_length=20, primary_key=True)
    name = models.CharField(max_length=100)
    gender = models.CharField(max_length=10, choices=[('Male', 'Male'), ('Female', 'Female')])
    birth_date = models.DateField()
    address = models.CharField(max_length=255)
    phone_number = models.CharField(max_length=20)
    email = models.EmailField()

    def __str__(self):
        return self.name

class Product(models.Model):
    product_code = models.CharField(max_length=20, primary_key=True)
    name = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField()

    def __str__(self):
        return f"{self.name}|{self.price}" 

class Invoice(models.Model):
    invoice_number = models.AutoField(primary_key=True, default=1)
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='invoices')
    issue_date = models.DateField()
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    def __str__(self):
        return f"{self.invoice_number}" 
    
class Order(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='orders')
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='orders', blank=True, null=True)
    product_code = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='orders')
    quantity = models.PositiveIntegerField()
    order_date = models.DateField()

    def save(self, *args, **kwargs):
        # Update product quantity
        if not self.pk:
            self.product_code.quantity = F('quantity') - self.quantity
            self.product_code.save()

        if self.invoice:
            self.customer = self.invoice.customer
        # Save the Order
        super().save(*args, **kwargs)

        # Update total amount for the related invoice
        if self.invoice:
            # Calculate total for the current order
            order_total = self.product_code.price * self.quantity

            # Recalculate the total amount for the invoice by summing all orders
            total = Order.objects.filter(invoice=self.invoice).aggregate(total=Sum(F('product_code__price') * F('quantity')))['total'] or 0
            
            # Update the invoice's total amount
            self.invoice.total_amount = total
            self.invoice.save()

    def __str__(self):
        return f'Order {self.id}'
