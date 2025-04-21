from datetime import datetime, timedelta

def build_flight_objects(df, worker_rules):

    """
    Transforms a DataFrame of flight data into a list of structured flight dictionaries (Example at the end). A dictionary is easily to access.
    
    Parameters:
        df (DataFrame): Flight data with columns ['ID', 'Airport', 'Day', 'Departure Time', 'Operation Type']
        worker_rules (dict): Dictionary of role-based pre/post rules per operation type.
    
    Returns:
        list: A list of dictionaries, one per flight, with role-specific time windows.
    """

    def create_flight(row):
        """
        Builds the dictionary for a single flight using the row data and worker_rules.
        Calculates the time window for each role involved in the operation.
        """
        # Combine day, time, adn operation
        departure_datetime = datetime.combine(row['Day'], row['Departure Time'])
        operation_type = str(row['Operation Type']).strip().upper()

        workers = {}

        # Loop through roles and check if apply
        for role, op_rules in worker_rules.items():
            if operation_type in op_rules: 
                # Get pre/post minutes
                pre = op_rules[operation_type]['pre']
                post = op_rules[operation_type]['post']
                # Time window
                workers[role] = {
                    'start': departure_datetime - timedelta(minutes=pre),
                    'end': departure_datetime + timedelta(minutes=post)
                }

        # return object
        return {
            'id': row['ID'],
            'airport': row['Airport'],
            'departure': departure_datetime,
            'operation_type': operation_type,
            'workers': workers  # solo si el rol aplica a ese tipo de operación. Diccionario con todos los trabajadores para este vuelo
        }

    flights = df.apply(create_flight, axis=1).tolist()
    return flights # Lista final de vuelos


'''
Ejemplo final estructura de datos
[
    {
        'id': 'FLT1018',
        'airport': 'BCN',
        'departure': datetime(2025, 4, 1, 14, 0),  # 1 de abril de 2025, 14:00h
        'operation_type': 'ARR/DEP',
        'workers': {
            'SPV PAX': {
                'start': datetime(2025, 4, 1, 11, 45),  # 135 minutos antes
                'end': datetime(2025, 4, 1, 14, 45)     # 45 minutos después
            },
            'CHECKIN': {
                'start': datetime(2025, 4, 1, 11, 45),
                'end': datetime(2025, 4, 1, 14, 30)
            },
            'AG PAX': {
                'start': datetime(2025, 4, 1, 12, 15),
                'end': datetime(2025, 4, 1, 14, 30)
            },
            'COORDI': {
                'start': datetime(2025, 4, 1, 12, 0),
                'end': datetime(2025, 4, 1, 14, 45)
            },
            'SPV RAMP': {
                'start': datetime(2025, 4, 1, 11, 45),
                'end': datetime(2025, 4, 1, 14, 45)
            },
            'DRIV': {
                'start': datetime(2025, 4, 1, 11, 45),
                'end': datetime(2025, 4, 1, 14, 45)
            },
            'OPE_A': {
                'start': datetime(2025, 4, 1, 12, 0),
                'end': datetime(2025, 4, 1, 14, 30)
            },
            'OPE_B': {
                'start': datetime(2025, 4, 1, 12, 15),
                'end': datetime(2025, 4, 1, 14, 30)
            }
        }
    },
    ...
]
'''