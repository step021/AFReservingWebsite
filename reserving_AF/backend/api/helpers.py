import pandas as pd
import numpy as np
import datetime
from datetime import date
pd.options.mode.chained_assignment = None  # default='warn'

def find_max_date(df, date_column):
    """
    Finds the maximum date in the specified date column of the DataFrame.

    Args:
        df (pd.DataFrame): The DataFrame containing the date column.
        date_column (str): The name of the date column.

    Returns:
        pd.Timestamp: The maximum date in the specified column.
    """
    df[date_column] = pd.to_datetime(df[date_column], errors='coerce')
    max_date = df[date_column].max()
    max_date_formatted = datetime.date(max_date.year, max_date.month, max_date.day)
    return pd.to_datetime(max_date_formatted, errors='coerce')


def coveragesdf():
    """
    Creates a DataFrame with the coverage types and their corresponding tags.

    Returns:
         a DataFrame containing the coverage types and their corresponding tags.
    """
    return pd.DataFrame({
        'Coverage': ["Casualty", "CMP - Casualty", "CMP - Property", "Commercial Motor - Auto Liability",
                 "Commercial Motor - Auto Liability - SRO", "Commercial Motor - Auto Physical Damage",
                 "Commercial Motor - GAP", "Commercial Motor - Single Interest",
                 "Domestic Motor - Auto Liability", "Domestic Motor - Auto Liability - SRO",
                 "Domestic Motor - Auto Phys Dam", "Domestic Motor - Auto Phys Dam Assumed",
                 "Fronting", "Group A&H", "Households", "Inland Marine - Travel",
                 "Marine Cargo", "Marine Hull", "Marine Hull - Single Interest",
                 "Marine Liability", "Professional Indemnity", "Property", "Surety",
                 "Suspense", "All"],
    'Tag': range(1, 26)
    })


def process_new_reserve_claim_files(files, Coverages, catcodes, max_date):
    """
    Processes new reserve and claim files to create a dictionary of DataFrames for each category.

    Args:
        files (list): A list of file paths to the reserve and claim files.
        Coverages (pd.DataFrame): A DataFrame containing the coverage types and their corresponding tags.
        catcodes (list): A list of category codes.
        max_date (pd.Timestamp): The maximum date to filter the data.

    Returns:
        dict: A dictionary containing DataFrames for each category.
    """
    reserves_list = {}
    claims_list = {}
    for file in files:
        #Reserves
        if file == files[0]:
            PaidLosses = pd.read_excel(file, engine='openpyxl', sheet_name='Sheet1')
            current_list = reserves_list
        #Claims
        elif file == files[1]:
            PaidLosses = pd.read_excel(file, engine='openpyxl', sheet_name='DATA')
            current_list = claims_list
        PaidLosses.columns = PaidLosses.columns.str.strip()
        # Convert columns to uppercase
        PaidLosses['Type'] = PaidLosses['Type'].str.upper()
        # Merge with Coverages
        PaidLosses = pd.merge(PaidLosses, Coverages, left_on='LOBCoverage', right_on='Coverage')
        # Convert columns to numeric
        numeric_columns = ['LossesPaid', 'ALAEPaid', 'DCCPaid', 'LossReserves', 'ALAEReserves', 'AnticipatedReserves', 'SalvageCollected']
        PaidLosses[numeric_columns] = PaidLosses[numeric_columns].apply(pd.to_numeric, errors='coerce').fillna(0)
        # Convert dates
        PaidLosses['AccountingDate'] = pd.to_datetime(PaidLosses['AccountingDate'])
        PaidLosses['LossDate'] = pd.to_datetime(PaidLosses['LossDate'])
        # Subset data after PriorAnalysisDate
        if max_date:
            PaidLosses = PaidLosses[PaidLosses['AccountingDate'] > max_date]
        # Group by CatCode
        for cat in catcodes:
            if cat == "Maria":
                DataBase = PaidLosses[PaidLosses['CatCode'] == 1170920]
            elif cat == "Irma":
                DataBase = PaidLosses[PaidLosses['CatCode'] == 1170906]
            elif cat == "Earthquake":
                DataBase = PaidLosses[PaidLosses['CatCode'] == 1200107]
            elif cat == "Fiona":
                DataBase = PaidLosses[PaidLosses['CatCode'] == 1220917]
            else:  # NonHurricane/Earthquakes
                DataBase = PaidLosses[(PaidLosses['CatCode'] != 1170920) & (PaidLosses['CatCode'] != 1170906) & (PaidLosses['CatCode'] != 1220917)]
            DataBase['LossDate'] = pd.to_datetime(DataBase['LossDate'], errors='coerce')
            DataBase['AccountingDate'] = pd.to_datetime(DataBase['AccountingDate'], errors='coerce')
            # Convert dates to quarters and extract year
            DataBase['Quarter'] = DataBase['LossDate'].dt.to_period('Q').astype(str)
            DataBase['quarter'] = DataBase['LossDate'].dt.quarter
            DataBase['Year'] = DataBase['LossDate'].dt.year
            # Creating the UniqueID
            DataBase['UniqueID'] = (DataBase['Type'].astype(str) + " " +
                                    DataBase['LOB'].astype(str) + " " +
                                    DataBase['LOBCoverage'].astype(str) + " " +
                                    DataBase['Quarter'].astype(str))
            DataBaseGrouped = DataBase.groupby(['UniqueID', 'Quarter', 'quarter', 'Year', 'Type', 'LOB', 'LOBCoverage', 'AccountingDate']).agg({
                'LossesPaid': 'sum',
                'ALAEPaid': 'sum',
                'DCCPaid': 'sum',
                'LossReserves': 'sum',
                'ALAEReserves': 'sum',
                'AnticipatedReserves': 'sum',
                'SalvageCollected': 'sum'
            }).reset_index()
            # Assigning to which quarter the LossDate belongs
            DataBaseGrouped['LossDate'] = np.where(DataBaseGrouped['quarter'] == 1,
                                                   DataBaseGrouped['Year'].astype(str) + '/3/31',
                                                   np.where(DataBaseGrouped['quarter'] == 2,
                                                            DataBaseGrouped['Year'].astype(str) + '/6/30',
                                                            np.where(DataBaseGrouped['quarter'] == 3,
                                                                     DataBaseGrouped['Year'].astype(str) + '/9/30',
                                                                     DataBaseGrouped['Year'].astype(str) + '/12/31')))
            DataBaseGrouped['LossDate'] = pd.to_datetime(DataBaseGrouped['LossDate'], errors='coerce')
            DataBaseGrouped['CAT and LL'] = ''
            DataBaseGrouped['Reinsurer'] = ''
            DataBaseGrouped['Paid Losses (Gross)'] = np.where(DataBaseGrouped['Type'] == "GROSS", DataBaseGrouped['LossesPaid'], 0)
            DataBaseGrouped['ALAE (Gross)'] = np.where(DataBaseGrouped['Type'] == "GROSS", DataBaseGrouped['ALAEPaid'], 0)
            DataBaseGrouped['DCC Paid (Gross)'] = np.where(DataBaseGrouped['Type'] == "GROSS", DataBaseGrouped['DCCPaid'], 0)
            DataBaseGrouped['Salvage and Subrogations (Gross)'] = np.where(DataBaseGrouped['Type'] == "GROSS", DataBaseGrouped['SalvageCollected'], 0)
            DataBaseGrouped['Paid Losses (Ceded)'] = np.where(DataBaseGrouped['Type'] == "CEDED", DataBaseGrouped['LossesPaid'], 0)
            DataBaseGrouped['ALAE (Ceded)'] = np.where(DataBaseGrouped['Type'] == "CEDED", DataBaseGrouped['ALAEPaid'], 0)
            DataBaseGrouped['DCC Paid (Ceded)'] = np.where(DataBaseGrouped['Type'] == "CEDED", DataBaseGrouped['DCCPaid'], 0)
            DataBaseGrouped['Salvage and Subrogations (Ceded)'] = np.where(DataBaseGrouped['Type'] == "CEDED", DataBaseGrouped['SalvageCollected'], 0)
            DataBaseGrouped['Paid Losses (Equator Re)'] = np.where(DataBaseGrouped['Type'] == "EQ", DataBaseGrouped['LossesPaid'], 0)
            DataBaseGrouped['ALAE (Equator Re)'] = np.where(DataBaseGrouped['Type'] == "EQ", DataBaseGrouped['ALAEPaid'], 0)
            DataBaseGrouped['DCC Paid (Equator Re)'] = np.where(DataBaseGrouped['Type'] == "EQ", DataBaseGrouped['DCCPaid'], 0)
            DataBaseGrouped['Salvage and Subrogations (Equator Re)'] = np.where(DataBaseGrouped['Type'] == "EQ", DataBaseGrouped['SalvageCollected'], 0)
            DataBaseGrouped['Case Reserves (Gross)'] = np.where(DataBaseGrouped['Type'] == "GROSS", DataBaseGrouped['LossReserves'], 0)
            DataBaseGrouped['Case ALAE (Gross)'] = np.where(DataBaseGrouped['Type'] == "GROSS", DataBaseGrouped['ALAEReserves'], 0)
            DataBaseGrouped['Case Reserves (Ceded)'] = np.where(DataBaseGrouped['Type'] == "CEDED", DataBaseGrouped['LossReserves'], 0)
            DataBaseGrouped['Case ALAE (Ceded)'] = np.where(DataBaseGrouped['Type'] == "CEDED", DataBaseGrouped['ALAEReserves'], 0)
            DataBaseGrouped['Case Reserves (Equator Re)'] = np.where(DataBaseGrouped['Type'] == "EQ", DataBaseGrouped['LossReserves'], 0)
            DataBaseGrouped['Case ALAE (Equator Re)'] = np.where(DataBaseGrouped['Type'] == "EQ", DataBaseGrouped['ALAEReserves'], 0)
            DataBaseGrouped['Case Reserves (S&S Gross)'] = np.where(DataBaseGrouped['Type'] == "GROSS", DataBaseGrouped['AnticipatedReserves'], 0)
            DataBaseGrouped['Case ALAE (S&S Gross)'] = 0
            DataBaseGrouped['Case Reserves (S&S Ceded)'] = np.where(DataBaseGrouped['Type'] == "CEDED", DataBaseGrouped['AnticipatedReserves'], 0)
            DataBaseGrouped['Case ALAE (S&S Ceded)'] = 0
            DataBaseGrouped = DataBaseGrouped.drop(columns=['Year'])
            DataBaseGrouped = DataBaseGrouped.drop(columns=['LossesPaid'])
            DataBaseGrouped = DataBaseGrouped.drop(columns=['ALAEPaid'])
            DataBaseGrouped = DataBaseGrouped.drop(columns=['DCCPaid'])
            DataBaseGrouped = DataBaseGrouped.drop(columns=['LossReserves'])
            DataBaseGrouped = DataBaseGrouped.drop(columns=['ALAEReserves'])
            DataBaseGrouped = DataBaseGrouped.drop(columns=['AnticipatedReserves'])
            DataBaseGrouped = DataBaseGrouped.drop(columns=['quarter'])
            DataBaseGrouped = pd.merge(DataBaseGrouped, Coverages, left_on='LOBCoverage', right_on='Coverage')
            DataBaseGrouped['Paid & ALAE, Gross of S&S (Gross)'] = DataBaseGrouped[['Paid Losses (Gross)', 'ALAE (Gross)', 'DCC Paid (Gross)']].sum(axis=1, skipna=True)
            DataBaseGrouped['Case and ALAE (Gross)'] = DataBaseGrouped[['Case Reserves (Gross)', 'Case ALAE (Gross)']].sum(axis=1, skipna=True)
            DataBaseGrouped['Paid & ALAE, Gross of S&S (Ceded)'] = DataBaseGrouped[['Paid Losses (Ceded)', 'ALAE (Ceded)', 'DCC Paid (Ceded)']].sum(axis=1, skipna=True)
            DataBaseGrouped['Case and ALAE (Ceded)'] = DataBaseGrouped[['Case Reserves (Ceded)', 'Case ALAE (Ceded)']].sum(axis=1, skipna=True)
            DataBaseGrouped['Paid & ALAE, Gross of S&S (Equator Re)'] = DataBaseGrouped[['Paid Losses (Equator Re)', 'ALAE (Equator Re)', 'DCC Paid (Equator Re)']].sum(axis=1, skipna=True)
            DataBaseGrouped['Case and ALAE (Equator Re)'] = DataBaseGrouped[['Case Reserves (Equator Re)', 'Case ALAE (Equator Re)']].sum(axis=1, skipna=True)
            DataBaseGrouped['Salvage and Subrogation (Gross)'] = DataBaseGrouped['Salvage and Subrogations (Gross)']
            DataBaseGrouped['Salvage and Subrogation (Ceded)'] = DataBaseGrouped['Salvage and Subrogations (Ceded)']
            DataBaseGrouped['Salvage and Subrogation (Equator Re)'] = DataBaseGrouped['Salvage and Subrogations (Equator Re)']
            DataBaseGrouped['Case and ALAE (S&S Gross)'] = DataBaseGrouped[['Case Reserves (S&S Gross)', 'Case ALAE (S&S Gross)']].sum(axis=1, skipna=True)
            DataBaseGrouped['Case and ALAE (S&S Ceded)'] = DataBaseGrouped[['Case Reserves (S&S Ceded)', 'Case ALAE (S&S Ceded)']].sum(axis=1, skipna=True)
            DataBaseGrouped['Age'] = ((np.ceil(DataBaseGrouped['AccountingDate'].dt.month / 3) +
                                       (DataBaseGrouped['AccountingDate'].dt.year - DataBaseGrouped['LossDate'].dt.year) * 4) -
                                      np.ceil(DataBaseGrouped['LossDate'].dt.month / 3)) * 3 + 3
            DataBaseGrouped['Key1 (Paid Loss, Age)'] = (DataBaseGrouped['Tag'].astype(str) +
                                                        DataBaseGrouped['Quarter'].astype(str) +
                                                        DataBaseGrouped['Age'].astype(str))
            DataBaseGrouped['Key2 (Paid Loss by AY)'] = (DataBaseGrouped['Tag'].astype(str) +
                                                         DataBaseGrouped['Quarter'].astype(str))
            DataBaseGrouped['Key3 (Case Reserve)'] = (DataBaseGrouped['Key2 (Paid Loss by AY)'].astype(str) +
                                                      DataBaseGrouped['AccountingDate'].astype(str))
            DataBaseGrouped['Key4 (Case Reserve, Age)'] = (DataBaseGrouped['Tag'].astype(str) +
                                                           DataBaseGrouped['Quarter'].astype(str) +
                                                           DataBaseGrouped['Age'].astype(str))
            DataBaseGrouped['Modified'] = ''
            DataBaseGrouped = DataBaseGrouped.drop(columns=['Quarter'])
            DataBaseGrouped = DataBaseGrouped.drop(columns=['SalvageCollected'])
            DataBaseGrouped = DataBaseGrouped.drop(columns=['UniqueID'])
            DataBaseGrouped = DataBaseGrouped.drop(columns=['Coverage'])
            DataBaseFinal = pd.concat([DataBaseGrouped], axis=0)
            DataBaseFinal['Accident Year and Quarter'] = DataBaseFinal['LossDate'].dt.to_period('Q')
            DataBaseFinal['Accounting (Closed) year'] = DataBaseFinal['AccountingDate'].dt.year
            DataBaseFinal['Accounting (Closed) Dates'] = DataBaseFinal['AccountingDate']
            DataBaseFinal['Treaty'] = 0
            DataBaseFinal.rename(columns={
                'LOBCoverage': 'Coverage Type',
                'AccountingDate': 'Accounting (Closed) Date',
                'LossDate': 'Date of Loss',
            }, inplace=True)
            DataBaseFinal = DataBaseFinal[[
                'Accident Year and Quarter', 'Accounting (Closed) year', 'Accounting (Closed) Dates',
                'Tag', 'Type', 'LOB', 'Coverage Type', 'Accounting (Closed) Date', 'Treaty', 'Date of Loss'
            ] + [col for col in DataBaseFinal.columns if col not in [
                'Accident Year and Quarter', 'Accounting (Closed) year', 'Accounting (Closed) Dates',
                'Tag', 'Type', 'LOB', 'Coverage Type', 'Accounting (Closed) Date', 'Treaty', 'Date of Loss']]]
            current_list[cat] = DataBaseFinal  # Add DataBaseFinal to the dictionary with the cat as the key
    return reserves_list, claims_list


def generate_accident_year_quarters(start_year, start_quarter, end_year, end_quarter):
    """
    Generates a list of accident year and quarters based on the specified start and end years and quarters.
    
    Args:
        start_year (int): The start year.
        start_quarter (str): The start quarter.
        end_year (int): The end year.
        end_quarter (str): The end quarter.

    Returns:
        list: A list of accident year and quarters.
    """
    quarters = ['Q1', 'Q2', 'Q3', 'Q4']
    accident_year_quarters = []
    for year in range(start_year, end_year + 1):
        for quarter in quarters:
            if (year == start_year and quarter < start_quarter) or (year == end_year and quarter > end_quarter):
                continue
            accident_year_quarters.append(f'{year}{quarter}')
    return accident_year_quarters


def calculate_max_age(input_quarter, end_year):
    """
    Calculates the maximum age in months based on the input quarter and end year.

    Args:
        input_quarter (str): The input quarter.
        end_year (int): The end year.

    Returns:
        int: The maximum age in months.
    """
    end_year = end_year
    end_quarter = 4
    input_year = int(input_quarter[:4])
    input_quarter_num = int(input_quarter[5])
    year_diff = end_year - input_year
    quarter_diff = end_quarter - input_quarter_num
    total_quarters = year_diff * 4 + quarter_diff
    max_age_months = total_quarters * 3
    return max_age_months + 3


def calculate_paid_loss_triangle(df, ages, accident_year_quarters, Tag, max_ages):
    """
    Calculates the Cumulative Paid Losses triangle.

    Args:
        df (pd.DataFrame): The DataFrame containing the data.
        ages (list): A list of ages.
        accident_year_quarters (list): A list of accident year and quarters.
        Tag (int): The tag of the accident.
        max_ages (dict): A dictionary containing the maximum ages for each accident year and quarter.

    Returns:
        pd.DataFrame: A DataFrame containing the Cumulative Paid Losses triangle.
    """
    df_new = pd.DataFrame({
        '': [Tag] * len(accident_year_quarters),
        ' ': ['Gross'] * len(accident_year_quarters),
        'Accident Quarter': accident_year_quarters
    })
    filtered_df = df[(df['Tag'] == Tag)]
    for age in ages:
        df_new[f'{age}'] = ''
    for idx, accident in enumerate(accident_year_quarters):
        cumsum_value = 0
        max_age = max_ages[accident]
        for age in ages:
            if age <= max_age:
                sum_value = filtered_df[(filtered_df['Accident Year and Quarter'] == accident) & (filtered_df['Age'] == age)]['Paid & ALAE, Gross of S&S (Gross)'].sum()
                
                cumsum_value +=sum_value
                df_new.at[idx, f'{age}'] = round(cumsum_value)
            else:
                break
    return df_new


def calculate_case_incurred_loss_triangle(df,ages,accident_year_quarters,Tag,max_ages):
    """
    Calculates the Cumulative Case Incurred Losses and ALAE, Gross of Reinsurance and Salvage and Subrogation triangle.
    
    Args:
        df (pd.DataFrame): The DataFrame containing the data.
        ages (list): A list of ages.
        accident_year_quarters (list): A list of accident year and quarters.
        Tag (int): The tag of the accident.
        max_ages (dict): A dictionary containing the maximum ages for each accident year and quarter.
        
    Returns:
        pd.DataFrame: A DataFrame containing the Cumulative Case Incurred Losses and ALAE, Gross of Reinsurance and Salvage and Subrogation triangle.
    """
    df_case = pd.DataFrame({
        '': [Tag] * len(accident_year_quarters),
        ' ': ['Gross'] * len(accident_year_quarters),
        'Accident Quarter': accident_year_quarters
    })
    filtered_df_1 = df[(df['Tag'] == Tag)]
    for age in ages:
        df_case[f'{age}'] = ''
    for idx, accident in enumerate(accident_year_quarters):
        cumsum_value = 0
        max_age = max_ages[accident]
        for age in ages:
            if age <= max_age:
                sum_value = filtered_df_1[(filtered_df_1['Accident Year and Quarter'] == accident) & (filtered_df_1['Age'] == age)]['Paid & ALAE, Gross of S&S (Gross)'].sum()
                cumsum_value +=sum_value
                df_case.at[idx, f'{age}'] = round(cumsum_value + filtered_df_1[(filtered_df_1['Accident Year and Quarter'] == accident) & (filtered_df_1['Age'] == age)]['Case and ALAE (Gross)'].sum())
            else:
                break
    return df_case


def calculate_age_to_age_factors(df, ages, accident_year_quarters):
    """
    Calculates the age-to-age factors triangle.

    Args:
        df (pd.DataFrame): The DataFrame containing the data.
        ages (list): A list of ages.
        accident_year_quarters (list): A list of accident year and quarters.

    Returns:
        pd.DataFrame: A DataFrame containing the age-to-age factors triangle.
    """
    age_ranges = [f'{ages[i]}-{ages[i+1]}' for i in range(len(ages) - 1)]
    df_age_to_age_factors = pd.DataFrame(columns=['Accident Quarter'] + age_ranges)
    for idx, accident in enumerate(accident_year_quarters):
        factors = []
        for i in range(len(ages) - 1):
            denominator = df.at[idx, str(ages[i])]
            numerator = df.at[idx, str(ages[i+1])]
            if denominator != '' and numerator != '':
                if denominator == 0:
                    factor = 1
                else:
                    factor = round(numerator / denominator, 3)
            else:
                factor = ''
            factors.append(factor)
        df_age_to_age_factors.loc[idx] = [accident] + factors
    return df_age_to_age_factors


def calculate_Wavg(df, curr_col_idx, next_col_idx, second_last_quarter, index, ages, metric):
    """
    Calculates the Weighted Average factor.

    Args:
        df (pd.DataFrame): The DataFrame containing the data.
        curr_col_idx (str): The current column index.
        next_col_idx (str): The next column index.
        second_last_quarter (str): The second last quarter.
        index (int): The index.
        ages (list): A list of ages.
        metric (int): The metric.

    Returns:
        float: The Weighted Average factor.
    """
    positions = df.stack().eq(next_col_idx).index.tolist()
    next_col_position = None
    for position in positions:
       if position[1] == str(ages[index+1]) and df.loc[position[0], 'Accident Quarter'] == second_last_quarter:
           next_col_position = position
           break
    row = next_col_position[0] - index
    next_col = next_col_position[1]
    if not next_col_position:
        return 1
    positions = df.stack().eq(curr_col_idx).index.tolist()
    curr_col_position = None
    for position in positions:
        if position[1] == str(ages[index]) and df.loc[position[0], 'Accident Quarter'] == second_last_quarter:
            curr_col_position = position
            break
    if not curr_col_position:
      return 1
    curr_col = curr_col_position[1]
    sum_offset_1 = df[curr_col].iloc[-metric-index:row+1].sum()
    sum_offset_2 = df[next_col].iloc[-metric-index:row+1].sum()
    if sum_offset_2 == 0:
        div_result = 0
    else:
        div_result = sum_offset_2 / sum_offset_1
    result = abs(div_result)
    return round(result,3)


def calculate_average_factors(age_to_age_df, triangle_df, ages):
    """
    Calculates the average factors for the specified age ranges.

    Args:
        age_to_age_df (pd.DataFrame): The age-to-age factors DataFrame.
        triangle_df (pd.DataFrame): The triangle DataFrame.
        ages (list): A list of ages.

    Returns:
        pd.DataFrame: A DataFrame containing the average factors for the specified age ranges.
    """
    age_ranges = [f'{ages[i]}-{ages[i+1]}' for i in range(len(ages) - 1)]
    summary_df = pd.DataFrame(columns=['Metric'] + age_ranges)
    metrics = ['All YR Avg', '5 YR WAvg', '3 YR WAvg', 'ExclHighLow', 'Industry', 'Prior Selection']
    second_last_quarter = triangle_df['Accident Quarter'].iloc[-2]
    for metric in metrics:
        summary_row = [metric]
        for i in range(len(ages) - 1):
            column_values = pd.to_numeric(age_to_age_df[age_ranges[i]], errors='coerce')
            if metric == 'All YR Avg':
                summary_row.append(round(column_values.mean(), 3))
            elif metric == '5 YR WAvg':
                five_yr_Wavg = calculate_Wavg(triangle_df, str(ages[i]), str(ages[i+1]), second_last_quarter,i,ages,21)
                summary_row.append(five_yr_Wavg)
            elif metric == '3 YR WAvg':
                three_yr_Wavg = calculate_Wavg(triangle_df, str(ages[i]), str(ages[i+1]), second_last_quarter,i,ages,13)
                summary_row.append(three_yr_Wavg)
            elif metric == 'ExclHighLow':
                if column_values.count() <= 2:
                  result = 1.000
                else:
                  total_sum = column_values.sum()
                  max_value = column_values.max()
                  min_value = column_values.min()
                  adjusted_sum = total_sum - max_value - min_value
                  result = adjusted_sum / (column_values.count()-2)
                  result = round(result, 3)
                summary_row.append(result)
            elif metric == 'Industry':
                summary_row.append(0)
            elif metric == 'Prior Selection':
                summary_row.append(0)
        summary_df.loc[len(summary_df)] = summary_row
    return summary_df

