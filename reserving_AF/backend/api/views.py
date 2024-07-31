from django.contrib.auth.models import User
from rest_framework import generics
from .models import DataLoss
from .serializers import UserSerializer, AppendHistoricalDataSerializer, ReplaceHistoricalDataSerializer, DataLossSerializer
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.http import FileResponse
from django.shortcuts import get_object_or_404





class CreateUserView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [AllowAny]

class AppendHistoricalDataView(generics.CreateAPIView):
    serializer_class = AppendHistoricalDataSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        if serializer.is_valid():
            serializer.save()
        else:
            print(serializer.errors)

class ReplaceHistoricalDataView(generics.CreateAPIView):
    serializer_class = ReplaceHistoricalDataSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        if serializer.is_valid():
            serializer.save()
        else:
            print(serializer.errors)

class DataLossListCreate(generics.ListCreateAPIView):
    serializer_class = DataLossSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return DataLoss.objects.filter(author=user)

    def perform_create(self, serializer):
        if serializer.is_valid():
            serializer.save(author=self.request.user)
        else:
            print(serializer.errors)

class DataLossDelete(generics.DestroyAPIView):
    serializer_class = DataLossSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return DataLoss.objects.filter(author=user)

class FileDownloadView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        dataloss_instance = get_object_or_404(DataLoss, pk=pk)
        if dataloss_instance.excel_output:
            excel_file = dataloss_instance.excel_output
            response = FileResponse(excel_file.open('rb'), as_attachment=True, filename=excel_file.name)
            return response
        return Response({'error': 'Excel file not found'}, status=status.HTTP_404_NOT_FOUND)
    
