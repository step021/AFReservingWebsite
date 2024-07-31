from django.urls import path
from . import views

urlpatterns = [
    path("dataloss/", views.DataLossListCreate.as_view(), name="dataloss-list"),
    path("dataloss/delete/<int:pk>/", views.DataLossDelete.as_view(), name="delete-dataloss"),
    path("dataloss/download/<int:pk>/", views.FileDownloadView.as_view(), name="download-dataloss"),
    path('historical-data/append/', views.AppendHistoricalDataView.as_view(), name='append-historical-data'),
    path('historical-data/replace/', views.ReplaceHistoricalDataView.as_view(), name='replace-historical-data')
]