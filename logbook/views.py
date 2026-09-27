from rest_framework import viewsets
from .models import DailyLog
from .serializers import DailyLogSerializer

class DailyLogViewSet(viewsets.ModelViewSet):
    queryset = DailyLog.objects.all().prefetch_related('entries')
    serializer_class = DailyLogSerializer
