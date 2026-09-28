from django.db import models
from django.contrib.auth.models import User

class Driver(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True)
    driver_id = models.CharField(max_length=50, unique=True)
    full_name = models.CharField(max_length=100)
    phone = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    license_number = models.CharField(max_length=50, blank=True)
    license_expiry = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=[
        ('Available', 'Available'), ('Driving', 'Driving'), 
        ('Off Duty', 'Off Duty'), ('On Duty', 'On Duty'), ('Inactive', 'Inactive')
    ], default='Available')
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.full_name} ({self.driver_id})"

class Truck(models.Model):
    truck_number = models.CharField(max_length=50, unique=True)
    make = models.CharField(max_length=50, blank=True)
    model = models.CharField(max_length=50, blank=True)
    year = models.IntegerField(null=True, blank=True)
    vin = models.CharField(max_length=50, blank=True)
    current_mileage = models.IntegerField(default=0)
    status = models.CharField(max_length=20, choices=[
        ('Available', 'Available'), ('In Use', 'In Use'), 
        ('Maintenance', 'Maintenance'), ('Inactive', 'Inactive')
    ], default='Available')
    assigned_driver = models.ForeignKey(Driver, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_trucks')
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.truck_number

class Trip(models.Model):
    trip_number = models.CharField(max_length=50, unique=True)
    driver = models.ForeignKey(Driver, on_delete=models.CASCADE, related_name='trips')
    truck = models.ForeignKey(Truck, on_delete=models.CASCADE, related_name='trips')
    origin = models.CharField(max_length=100)
    destination = models.CharField(max_length=100)
    distance = models.FloatField(default=0.0)
    load_description = models.TextField(blank=True)
    pickup_datetime = models.DateTimeField(null=True, blank=True)
    delivery_datetime = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=[
        ('Planned', 'Planned'), ('Assigned', 'Assigned'), 
        ('In Transit', 'In Transit'), ('Delivered', 'Delivered'), ('Cancelled', 'Cancelled')
    ], default='Planned')
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Trip {self.trip_number}"

class MaintenanceRecord(models.Model):
    truck = models.ForeignKey(Truck, on_delete=models.CASCADE, related_name='maintenance_records')
    maintenance_type = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    service_date = models.DateField()
    mileage = models.IntegerField()
    next_service_date = models.DateField(null=True, blank=True)
    next_service_mileage = models.IntegerField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=[
        ('Scheduled', 'Scheduled'), ('Completed', 'Completed'), 
        ('Due Soon', 'Due Soon'), ('Overdue', 'Overdue')
    ], default='Scheduled')
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)

    def __str__(self):
        return f"{self.truck.truck_number} - {self.maintenance_type}"

class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications', null=True, blank=True)
    title = models.CharField(max_length=100)
    message = models.TextField()
    notification_type = models.CharField(max_length=20, choices=[
        ('HOS', 'HOS'), ('Trip', 'Trip'), 
        ('Maintenance', 'Maintenance'), ('System', 'System')
    ], default='System')
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)

    def __str__(self):
        return self.title

class DailyLog(models.Model):
    date = models.DateField()
    driver_name = models.CharField(max_length=100) # Kept for backward compatibility
    driver = models.ForeignKey(Driver, on_delete=models.CASCADE, null=True, blank=True, related_name='logs')
    tractor_number = models.CharField(max_length=50)
    trailer_number = models.CharField(max_length=50, blank=True)
    shipper_commodity = models.CharField(max_length=100, blank=True)
    total_miles_driven = models.IntegerField(default=0)
    signature = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)

    def __str__(self):
        return f"{self.date} - {self.driver_name}"

class StatusEntry(models.Model):
    daily_log = models.ForeignKey(DailyLog, related_name='entries', on_delete=models.CASCADE)
    start_time = models.TimeField()
    end_time = models.TimeField()
    duty_status = models.IntegerField(choices=[
        (1, 'Off Duty'),
        (2, 'Sleeper Berth'),
        (3, 'Driving'),
        (4, 'On Duty')
    ])
    location = models.CharField(max_length=100, blank=True)
    remarks = models.CharField(max_length=200, blank=True)

    def __str__(self):
        return f"{self.get_duty_status_display()} ({self.start_time} - {self.end_time})"
