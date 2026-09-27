from django.db import models
from django.core.exceptions import ValidationError
from datetime import datetime, date, timedelta

class DailyLog(models.Model):
    date = models.DateField()
    driver_name = models.CharField(max_length=255)
    tractor_number = models.CharField(max_length=100)
    trailer_number = models.CharField(max_length=100, blank=True, null=True)
    shipper_commodity = models.CharField(max_length=255)
    total_miles_driven = models.PositiveIntegerField(default=0)
    signature = models.CharField(max_length=255)

    def __str__(self):
        return f"{self.date} - {self.driver_name}"

class StatusEntry(models.Model):
    STATUS_CHOICES = [
        (1, 'Off Duty'),
        (2, 'Sleeper Berth'),
        (3, 'Driving'),
        (4, 'On Duty (Not Driving)'),
    ]

    daily_log = models.ForeignKey(DailyLog, related_name='entries', on_delete=models.CASCADE)
    start_time = models.TimeField()
    end_time = models.TimeField()
    duty_status = models.IntegerField(choices=STATUS_CHOICES)
    location = models.CharField(max_length=255)
    remarks = models.CharField(max_length=500, blank=True, null=True)

    def __str__(self):
        return f"{self.get_duty_status_display()} ({self.start_time} - {self.end_time})"

    def clean(self):
        super().clean()
        if self.start_time >= self.end_time:
            raise ValidationError("End time must be after start time.")
