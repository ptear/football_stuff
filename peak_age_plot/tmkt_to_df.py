import pandas as pd

def tmkt_to_df(html):

    df = pd.read_html(html)[0].dropna(subset=['Age']).drop(columns=['Nat.'])

    df['Player'] = df['Player'].str.replace('Defensive Midfield', 'Defensive-Midfield')
    df['Player'] = df['Player'].str.replace('Central Midfield', 'Central-Midfield')
    df['Player'] = df['Player'].str.replace('Attacking Midfield', 'Attacking-Midfield')
    df['Player'] = df['Player'].str.replace('Left Winger', 'Left-Winger')
    df['Player'] = df['Player'].str.replace('Right Winger', 'Right-Winger')

    # Function to calculate x based on the number of words
    def calculate_x(row):
        words = row['Player'].split()
        return len(words)

    # Calculate x for each row
    df['x'] = df.apply(calculate_x, axis=1)

    # Function to split the string based on the value of x
    def split_string(row):
        s = row['Player']
        x = row['x']
        words = s.split()
        if len(words) > x:
            first_x_words = ' '.join(words[:x])
            last_word = '-'.join(words[x:])
        else:
            first_x_words = ' '.join(words[:-1])
            last_word = words[-1] if words else ''
        return pd.Series([first_x_words, last_word])

    # Apply the function to the DataFrame
    df[['Name', 'Position']] = df.apply(split_string, axis=1)

    df = df.reset_index(drop=True)

    return df
