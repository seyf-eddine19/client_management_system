# management/commands/generate_random_data.py
from django.core.management.base import BaseCommand
from faker import Faker
from crm.models import Customer, Product, Invoice, Order
import random
from datetime import datetime, timedelta

class Command(BaseCommand):
    help = 'Generate random data for the database'

    def handle(self, *args, **kwargs):
        fake = Faker()

        # Create 50 random customers
        # self.stdout.write(self.style.SUCCESS('Creating 50 customers...'))
        # for _ in range(50):
        #     nationality = random.choice(['DZ', 'EG', 'TN', 'LY', 'MA', 'SA', 'AE'])
        #     customer = Customer.objects.create(
        #         customer_code=fake.unique.bothify(text='????###'),
        #         name=fake.name(),
        #         gender=random.choice(['Male', 'Female']),
        #         birth_date=fake.date_of_birth(minimum_age=18, maximum_age=80),
        #         address=fake.address(),
        #         nationality=nationality,
        #         phone_number=fake.phone_number(),
        #         email=fake.email()
            # )

        # # Create 50 random products
        # self.stdout.write(self.style.SUCCESS('Creating 50 products...'))
        # for _ in range(50):
        #     product = Product.objects.create(
        #         product_code=fake.unique.bothify(text='P#######'),
        #         name=fake.word(),
        #         price=random.uniform(10, 1000),
        #         size=fake.random_element(elements=('Small', 'Medium', 'Large', 'Extra Large')),
        #         sales_count=random.randint(0, 100)
        #     )

        # # Create 50 random invoices
        # self.stdout.write(self.style.SUCCESS('Creating 50 invoices...'))
        # for _ in range(50):
        #     customer = random.choice(Customer.objects.all())
        #     invoice = Invoice.objects.create(
        #         customer=customer,
        #         issue_date=fake.date_this_year(),
        #         total_amount=random.uniform(100, 5000)
        #     )

        # Create 50 random orders
        self.stdout.write(self.style.SUCCESS('Creating 50 orders...'))
        for _ in range(50):
            customer = random.choice(Customer.objects.all())
            print(customer)
            product = random.choice(Product.objects.all())
            # invoice = random.choice(Invoice.objects.all())
            quantity = random.randint(1, 5)
            order_date = fake.date_this_year()

            order = Order.objects.create(
                customer=customer,
                # invoice=invoice,
                product_code=product,
                quantity=quantity,
                order_date=order_date
            )

            # Update sales_count for the product
            product.sales_count += quantity
            product.save()

        self.stdout.write(self.style.SUCCESS('Successfully added 50 random data entries in each model!'))
