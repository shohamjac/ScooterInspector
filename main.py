import logging
from dotenv import load_dotenv
from bird_scrapper import BirdScrapper
import os
import sys
import pandas as pd

# Configure logging in the main file
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

if __name__ == '__main__':
    logger.info('Starting')

    load_dotenv()
    date_file = os.getenv('DATA_FILE')

    scrapper = BirdScrapper(email=os.getenv('EMAIL'),guid=os.getenv('GUID'),
                            access_token=os.getenv('ACCESS_TOKEN'),
                            refresh_token=os.getenv('REFRESH_TOKEN'))

    # This is a bad way to introduce those constants. fix later.
    # Initial point for TLV (longitude, latitude)
    start_lat = 32.093195
    start_long = 34.759387
    # Grid dimensions for TLV
    rows = 7
    cols = 7
    # Distance between points (in meters)
    spacing = 700
    radius = 500  # should be a bit less than spacing/sqrt(2)

    grid = scrapper.create_grid(start_lat, start_long, rows, cols, spacing)

    df = scrapper.get_city_scooters(grid, radius=radius)
    new_scooters = len(df)

    try:
        old_df = pd.read_csv(date_file)
        df = pd.concat([old_df, df])
    except FileNotFoundError:
        pass
    df.to_csv(date_file, index=False)
    logger.info(f'Finished, found {new_scooters} scooter locations in TLV')
