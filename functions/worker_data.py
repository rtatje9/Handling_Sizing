import pandas as pd

def load_worker_shift_rules(file_path):
    """
    Loads an Excel file containing pre/post time rules by role and operation type.
    
    Returns a dictionary in the format:
    {
        'SPV PAX': {
            'ARR/DEP': {'pre': 135, 'post': 45},
            'DEP': {'pre': 100, 'post': 30},
            ...
        },
        ...
    }
    """
    # read excel file
    df = pd.read_excel(file_path)
    # Clean columns
    df.columns = [col.strip() for col in df.columns]
    # Rename
    df = df.rename(columns={df.columns[0]: 'Role', df.columns[1]: 'Operation Type', df.columns[2]: 'Pre', df.columns[3]: 'Post'})
    df = df.dropna(subset=['Role', 'Operation Type', 'Pre', 'Post']) # Elimina columnas onde falte alguno de los campos

    # Iterate through rows
    rules = {}
    for _, row in df.iterrows():
        role = row['Role'].strip().upper()
        op_type = row['Operation Type'].strip().upper()
        pre = int(row['Pre'])
        post = int(row['Post'])

        if role not in rules:
            rules[role] = {}
        
        # Store values
        rules[role][op_type] = {'pre': pre, 'post': post}
    return rules
