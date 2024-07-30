import pandas as pd

def tmkt_to_df(html):

    df = pd.read_html(html)[0].dropna(subset=['Age']).drop(columns=['Nat.'])

    df['Player'] = df['Player'].str.replace('Defensive Midfield', 'Defensive-Midfield')
    df['Player'] = df['Player'].str.replace('Central Midfield', 'Central-Midfield')
    df['Player'] = df['Player'].str.replace('Attacking Midfield', 'Attacking-Midfield')
    df['Player'] = df['Player'].str.replace('Left Winger', 'Left-Winger')
    df['Player'] = df['Player'].str.replace('Right Winger', 'Right-Winger')

    # Function to split the string based on the value of x
    def split_string(row):
        words = row['Player'].split()
        first_x_words = ' '.join(words[:-1])
        last_word = words[-1]
        return pd.Series([first_x_words, last_word])

    # Apply the function to the DataFrame
    df[['Name', 'Position']] = df.apply(split_string, axis=1)

    df = df.reset_index(drop=True)

    return df
