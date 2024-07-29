import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np


def plot_peak_age(df, club_name):

    # Define peak age ranges for each position
    peak_age_ranges = {
        'Goalkeeper': (26.5, 29.5),
        'Centre-Back': (25.5, 28.5),
        'Left-Back': (23.5, 26.5),
        'Right-Back': (23.5, 26.5),
        'Defensive-Midfield': (23.5, 27.5),
        'Central-Midfield': (23.5, 27.5),
        'Attacking-Midfield': (24.5, 27.5),
        'Left-Winger': (24.5, 27.5),
        'Right-Winger': (24.5, 27.5),
        'Centre-Forward': (25.5, 28.5)
    }

    # Plot settings
    plt.figure(figsize=(15, 10))
    sns.set_theme(style="whitegrid")

    # Adjust y positions to add padding
    y_positions = np.arange(len(df)) + 0.5

    # Plot the players' ages with adjusted y positions
    for i, (position, group) in enumerate(df.groupby('Position')):
        idx = group.index
        y_vals = y_positions[idx]
        plt.scatter(group['Age'], y_vals, label=position)
        
        # Add peak age ranges with padding
        start, end = peak_age_ranges[position]
        plt.fill_betweenx([y_vals.min() - 0.25, y_vals.max() + 0.25], start, end, alpha=0.1, color='red')

    # Determine x-axis limits and ticks dynamically based on data
    age_min = df['Age'].min()
    age_max = df['Age'].max()
    age_range = age_max - age_min
    age_padding = 1  # Padding on both sides

    plt.xlim(age_min - age_padding, age_max + age_padding)
    plt.xticks(np.arange(int(age_min), int(age_max) + 1, 1))

    # Add labels and title
    plt.yticks(y_positions, df['Name'])
    plt.xlabel('Age')
    plt.ylabel('Name')
    plt.title(f'{club_name} squad compared to peak age across positions')
    plt.legend(loc='upper right')

    # Show plot
    plt.gca().invert_yaxis()
    plt.savefig(f"{club_name.replace(' ', '_')}.png")
    plt.show()
