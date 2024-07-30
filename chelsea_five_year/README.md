### How to

#### 1. Get data
Here, the data is taken from transfermarkt. But it can be any data source, you just need the names, ages and positions. You could do it manually using wikipedia, for example.

To get the data from transfermarkt: 
1. Navigate to the page (e.g. https://www.transfermarkt.co.uk/fc-chelsea/kader/verein/631/saison_id/2024)
2. Inspect element
3. Find where the table element is
4. Copy (copy outer html) and paste into a blank html file (e.g. chelsea.html)

You could also try directly using pandas with read_html on the url itself.

#### 2. Process data
Use the tmkt_to_df function (https://github.com/ptear/football_stuff/blob/main/peak_age_plot/tmkt_to_df.py).

In the function we:
- drop useless rows and columns
- join position strings by dashes so that we can correctly split the name of the player from the position
- select the first n-1 'words' (space separated) as the player name, and the last 'word' as the player position
- reset the index

#### 3. Copy and manually modify the csv
After saving the csv (as "data.csv"), make a copy (i.e. copy and paste data.csv).

Then, add any rows of players that are not in the original data that you know of. Players that are missing from the transfermarkt are usually youth prospects. For instance, Estevao.

#### 4. Plot the data
Read in the modified csv, then use the plot_peak_age function (https://github.com/ptear/football_stuff/blob/main/peak_age_plot/plot_peak_age.py).

In the function we:
- define the peak age bands
- plot each position group at a time
- use fill between to create the peak age boxes (using alpha to make the box translucent)
- modify axes and other styling
- invert y axis so goalkeepers are at the top
- save figure and display