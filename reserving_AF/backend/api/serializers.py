from rest_framework import serializers
from django.contrib.auth.models import User
import pandas as pd
from .helpers import coveragesdf, generate_accident_year_quarters, calculate_max_age, calculate_paid_loss_triangle, calculate_case_incurred_loss_triangle, calculate_age_to_age_factors, calculate_average_factors, process_new_reserve_claim_files,find_max_date
from .models import DataLoss, Client, UserClientHistoricalData
import datetime
from io import BytesIO
from django.core.files.base import ContentFile
import logging
from django.templatetags.static import static
from django.conf import settings

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'password', 'first_name', 'last_name']
        extra_kwargs = {
            'password': {'write_only': True}
        }
    def create(self, validated_data):
        print(validated_data)
        user = User.objects.create_user(**validated_data)
        return user

class AppendHistoricalDataSerializer(serializers.ModelSerializer):
    client = serializers.SlugRelatedField(queryset=Client.objects.all(), slug_field='name')
    class Meta:
        model = UserClientHistoricalData
        fields = ['client', 'claims_file', 'reserves_file']
    def create(self, validated_data):
        user = self.context['request'].user
        client = validated_data.get('client')
        try:
            historical_data = UserClientHistoricalData.objects.get(user=user, client=client)
        except UserClientHistoricalData.DoesNotExist:
            raise serializers.ValidationError("Historical data not found for the user and client")
        reserves_file = validated_data.get('reserves_file')
        claims_file = validated_data.get('claims_file')
        print(historical_data.file)
        historical_df = pd.read_excel(historical_data.file, sheet_name=None, engine='openpyxl')
        df_dataloss_maria = historical_df.get('DatalossMaria')
        df_dataloss_irma = historical_df.get('DatalossIrma')
        df_dataloss_fiona = historical_df.get('DatalossFiona')
        df_dataloss_non_h = historical_df.get('Dataloss')
        df_dataloss_earthquake = historical_df.get('DatalossEarthquake')
        max_date_non_h = find_max_date(df_dataloss_non_h, 'Accounting (Closed) Date')
        max_date_maria = find_max_date(df_dataloss_maria, 'Accounting (Closed) Date')
        max_date_irma = find_max_date(df_dataloss_irma, 'Accounting (Closed) Date')
        max_date_fiona = find_max_date(df_dataloss_fiona, 'Accounting (Closed) Date')
        max_date_earthquake = find_max_date(df_dataloss_earthquake, 'Accounting (Closed) Date')
        max_date = max(max_date_non_h, max_date_maria, max_date_irma, max_date_fiona, max_date_earthquake)
        print(max_date)
        files = [reserves_file, claims_file]
        coverages = coveragesdf()
        catcodes = ["Maria", "Irma", "Fiona", "Non H", "Earthquake"]
        reserves_list, claims_list = process_new_reserve_claim_files(files, coverages, catcodes, max_date)
        df_reserves_maria = reserves_list.get("Maria")
        df_reserves_irma = reserves_list.get("Irma")
        df_reserves_fiona = reserves_list.get("Fiona")
        df_reserves_non_h = reserves_list.get("Non H")
        df_reserves_earthquake = reserves_list.get("Earthquake")
        df_claims_maria = claims_list.get("Maria")
        df_claims_irma = claims_list.get("Irma")
        df_claims_fiona = claims_list.get("Fiona")
        df_claims_non_h = claims_list.get("Non H")
        df_claims_earthquake = claims_list.get("Earthquake")
        df_combined_maria = pd.concat([df_dataloss_maria, df_reserves_maria, df_claims_maria], ignore_index=True)
        df_combined_irma = pd.concat([df_dataloss_irma, df_reserves_irma, df_claims_irma], ignore_index=True)
        df_combined_fiona = pd.concat([df_dataloss_fiona, df_reserves_fiona, df_claims_fiona], ignore_index=True)
        df_combined_non_h = pd.concat([df_dataloss_non_h, df_reserves_non_h, df_claims_non_h], ignore_index=True)
        df_combined_earthquake = pd.concat([df_dataloss_earthquake, df_reserves_earthquake, df_claims_earthquake], ignore_index=True)
        output = BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df_combined_maria.to_excel(writer, sheet_name='DatalossMaria', index=False)
            df_combined_irma.to_excel(writer, sheet_name='DatalossIrma', index=False)
            df_combined_fiona.to_excel(writer, sheet_name='DatalossFiona', index=False)
            df_combined_non_h.to_excel(writer, sheet_name='Dataloss', index=False)
            df_combined_earthquake.to_excel(writer, sheet_name='DatalossEarthquake', index=False)
        output.seek(0)
        historical_data.file.save(f"{user.username}_{client.name}_historical.xlsx", ContentFile(output.read()))
        historical_data.save()
        return historical_data


class ReplaceHistoricalDataSerializer(serializers.ModelSerializer):
    client = serializers.SlugRelatedField(queryset=Client.objects.all(), slug_field='name')
    class Meta:
        model = UserClientHistoricalData
        fields = [
            'client','claims_file', 'reserves_file',
            'upper_bound_update', 'lower_bound_update'
        ]
    def create(self, validated_data):
        user = self.context['request'].user
        client = validated_data.get('client')
        claims_file = validated_data.get('claims_file')
        reserves_file = validated_data.get('reserves_file')
        upper_bound_update = validated_data.get('upper_bound_update')
        lower_bound_update = validated_data.get('lower_bound_update')
        try:
            historical_data = UserClientHistoricalData.objects.get(user=user, client=client)
        except UserClientHistoricalData.DoesNotExist:
            raise serializers.ValidationError("Historical data not found for the user and client")
        df_dataloss_maria = pd.read_excel(historical_data.file, sheet_name='DatalossMaria')
        df_dataloss_irma = pd.read_excel(historical_data.file, sheet_name='DatalossIrma')
        df_dataloss_fiona = pd.read_excel(historical_data.file, sheet_name='DatalossFiona')
        df_dataloss_non_h = pd.read_excel(historical_data.file, sheet_name='Dataloss')
        df_dataloss_earthquake = pd.read_excel(historical_data.file, sheet_name='DatalossEarthquake')
        coverages = coveragesdf()
        catcodes = ["Maria", "Irma", "Fiona", "Non H", "Earthquake"]
        files = [reserves_file, claims_file]
        reserves_list,claims_list = process_new_reserve_claim_files(files, coverages, catcodes)
        df_reserves_maria = reserves_list.get("Maria")
        df_reserves_irma = reserves_list.get("Irma")
        df_reserves_fiona = reserves_list.get("Fiona")
        df_reserves_non_h = reserves_list.get("Non H")
        df_reserves_earthquake = reserves_list.get("Earthquake")
        df_claims_maria = claims_list.get("Maria")
        df_claims_irma = claims_list.get("Irma")
        df_claims_fiona = claims_list.get("Fiona")
        df_claims_non_h = claims_list.get("Non H")
        df_claims_earthquake = claims_list.get("Earthquake")
        df_dataloss_maria = df_dataloss_maria[(df_dataloss_maria['Accounting (Closed) Date'] < lower_bound_update) | (df_dataloss_maria['Accounting (Closed) Date'] > upper_bound_update)]
        df_dataloss_irma = df_dataloss_irma[(df_dataloss_irma['Accounting (Closed) Date'] < lower_bound_update) | (df_dataloss_irma['Accounting (Closed) Date'] > upper_bound_update)]
        df_dataloss_fiona = df_dataloss_fiona[(df_dataloss_fiona['Accounting (Closed) Date'] < lower_bound_update) | (df_dataloss_fiona['Accounting (Closed) Date'] > upper_bound_update)]
        df_dataloss_non_h = df_dataloss_non_h[(df_dataloss_non_h['Accounting (Closed) Date'] < lower_bound_update) | (df_dataloss_non_h['Accounting (Closed) Date'] > upper_bound_update)]
        df_dataloss_earthquake = df_dataloss_earthquake[(df_dataloss_earthquake['Accounting (Closed) Date'] < lower_bound_update) | (df_dataloss_earthquake['Accounting (Closed) Date'] > upper_bound_update)]
        df_combined_maria = pd.concat([df_dataloss_maria, df_reserves_maria, df_claims_maria], ignore_index=True)
        df_combined_irma = pd.concat([df_dataloss_irma, df_reserves_irma, df_claims_irma], ignore_index=True)
        df_combined_fiona = pd.concat([df_dataloss_fiona, df_reserves_fiona, df_claims_fiona], ignore_index=True)
        df_combined_non_h = pd.concat([df_dataloss_non_h, df_reserves_non_h, df_claims_non_h], ignore_index=True)
        df_combined_earthquake = pd.concat([df_dataloss_earthquake, df_reserves_earthquake, df_claims_earthquake], ignore_index=True)
        output = BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df_combined_maria.to_excel(writer, sheet_name='DatalossMaria', index=False)
            df_combined_irma.to_excel(writer, sheet_name='DatalossIrma', index=False)
            df_combined_fiona.to_excel(writer, sheet_name='DatalossFiona', index=False)
            df_combined_non_h.to_excel(writer, sheet_name='Dataloss', index=False)
            df_combined_earthquake.to_excel(writer, sheet_name='DatalossEarthquake', index=False)
        output.seek(0)
        historical_data.file.save(f"{user.username}_{client.name}_historical.xlsx", ContentFile(output.read()))
        historical_data.save()
        return historical_data 


class ClientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Client
        fields = ['id', 'name']


class DataLossSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)
    client = serializers.SlugRelatedField(queryset=Client.objects.all(), slug_field='name')
    class Meta:
        model = DataLoss
        fields = [
            'id', 'author', 'client', 'curr_quarter', 'current_year', 'paid_case',
            'created_at', 'excel_output'
        ]
        extra_kwargs = {
            'author': {'read_only': True},
            'excel_output': {'read_only': True}
        }
    def create(self, validated_data): 
        client = validated_data.get('client')
        curr_quarter = validated_data.get('curr_quarter')
        current_year = int(validated_data.get('current_year'))
        paid_case = validated_data.get('paid_case')
        user= self.context['request'].user
        try:
            historical_data = UserClientHistoricalData.objects.get(user=user, client=client)
        except UserClientHistoricalData.DoesNotExist:
            raise serializers.ValidationError("Historical data not found for the user and client")
        print(historical_data.file)
        df = pd.read_excel(historical_data.file, sheet_name='Dataloss')
        if curr_quarter == 'Q2':
             df = df[df['Accounting (Closed) Date'] <= pd.to_datetime(datetime.date(current_year, 6, 30))]
        elif curr_quarter == 'Q4':
             df = df[df['Accounting (Closed) Date'] <= pd.to_datetime(datetime.date(current_year, 12, 31))]
        start_quarter = 'Q1'
        end_year = current_year
        start_year = current_year - 10
        end_quarter = 'Q4'
        accident_year_quarters = generate_accident_year_quarters(start_year, start_quarter, end_year, end_quarter)
        max_ages = {accident: calculate_max_age(accident, end_year) for accident in accident_year_quarters}
        max_age_for_triangle = max(list(max_ages.values()))
        min_age_for_triangle = min(list(max_ages.values()))
        ages = list(range(min_age_for_triangle, max_age_for_triangle + 3, 3))
        if len(accident_year_quarters) > len(ages):
            raise ValueError("Generated accident_year_quarters exceed the ages range. Adjust the ranges accordingly.")
        loss_triangles = {}
        age_to_age_triangles = {}
        average_factors = {}
        for Tag in range(1, 25):
            if paid_case == 'paid':
                loss_triangle = calculate_paid_loss_triangle(df, ages, accident_year_quarters, Tag, max_ages)
            elif paid_case == 'case':
                loss_triangle = calculate_case_incurred_loss_triangle(df, ages, accident_year_quarters, Tag, max_ages)
            else:
                loss_triangle = pd.DataFrame()
            
            try:
                age_to_age_triangle = calculate_age_to_age_factors(loss_triangle, ages, accident_year_quarters)
                average_factor = calculate_average_factors(age_to_age_triangle, loss_triangle, ages)
            except Exception as e:
                logging.error("Error calculating triangles for Tag %s: %s", Tag, e, exc_info=True)
                age_to_age_triangle = pd.DataFrame()
                average_factor = pd.DataFrame()
            loss_triangles[Tag] = loss_triangle
            age_to_age_triangles[Tag] = age_to_age_triangle
            average_factors[Tag] = average_factor
        output = BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df.to_excel(writer, sheet_name='Dataloss', index=False)
            for Tag in range(1, 25):
                startrow = 0
                loss_triangles[Tag].to_excel(writer, sheet_name=f'Triangle_{Tag}', startrow=startrow, index=False)
                startrow += len(loss_triangles[Tag]) + 2  # Leave a couple of rows space
                age_to_age_triangles[Tag].to_excel(writer, sheet_name=f'Triangle_{Tag}', startrow=startrow, index=False)
                startrow += len(age_to_age_triangles[Tag]) + 2  # Leave a couple of rows space
                average_factors[Tag].to_excel(writer, sheet_name=f'Triangle_{Tag}', startrow=startrow, index=False)
        data_loss = DataLoss.objects.create(**validated_data)
        output.seek(0)
        data_loss.excel_output.save(f"{data_loss.client.name}_output.xlsx", ContentFile(output.read()))
        return data_loss
