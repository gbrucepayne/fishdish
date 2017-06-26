# fishdish
Raspberry Pi project for using Fish Dish from Pi Supply for headless operation with shutdown button.
Initializes the Fish Dish GPIO board
Flashes the green LED and plays a tune on start-up
Waits for a button press to trigger graceful shutdown after playing a tune and flashing the red LED
Tune definition is done by parsing a RTTL ringtone file
