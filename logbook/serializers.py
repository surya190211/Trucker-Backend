from rest_framework import serializers
from .models import DailyLog, StatusEntry
from datetime import datetime, date

class StatusEntrySerializer(serializers.ModelSerializer):
    class Meta:
        model = StatusEntry
        fields = '__all__'

class DailyLogSerializer(serializers.ModelSerializer):
    entries = StatusEntrySerializer(many=True)
    summary = serializers.SerializerMethodField()

    class Meta:
        model = DailyLog
        fields = '__all__'

    def get_summary(self, obj):
        totals = {1: 0.0, 2: 0.0, 3: 0.0, 4: 0.0}
        dummy_date = date.today()

        for entry in obj.entries.all():
            start = datetime.combine(dummy_date, entry.start_time)
            end = datetime.combine(dummy_date, entry.end_time)
            delta_hours = (end - start).total_seconds() / 3600.0
            totals[entry.duty_status] += delta_hours

        active_hours = totals[3] + totals[4]
        total_24 = sum(totals.values())

        return {
            'off_duty': round(totals[1], 2),
            'sleeper_berth': round(totals[2], 2),
            'driving': round(totals[3], 2),
            'on_duty': round(totals[4], 2),
            'combined_active': round(active_hours, 2),
            'total_hours': round(total_24, 2)
        }

    def validate(self, data):
        entries_data = data.get('entries', [])
        if not entries_data:
            return data

        # Check for overlaps and 24-hour total
        entries_data.sort(key=lambda x: x['start_time'])
        total_seconds = 0
        dummy_date = date.today()

        for i in range(len(entries_data)):
            start = datetime.combine(dummy_date, entries_data[i]['start_time'])
            end = datetime.combine(dummy_date, entries_data[i]['end_time'])
            
            total_seconds += (end - start).total_seconds()
            
            if i > 0:
                prev_end = datetime.combine(dummy_date, entries_data[i-1]['end_time'])
                if start < prev_end:
                    raise serializers.ValidationError("Overlapping time entries detected.")

        if total_seconds != 86400: # 24 hours * 60 * 60
            raise serializers.ValidationError(f"Total time must equal exactly 24 hours. Currently: {total_seconds / 3600.0} hours.")

        return data

    def create(self, validated_data):
        entries_data = validated_data.pop('entries')
        daily_log = DailyLog.objects.create(**validated_data)
        for entry_data in entries_data:
            StatusEntry.objects.create(daily_log=daily_log, **entry_data)
        return daily_log
