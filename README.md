# Twitter-Scraper
This is not a perfect scraper, so feel free to add improvements if you find any.

IMPROVEMENTS:
- Improved error handling so that tweets are not rejected if certain fields are null, etc...
- Leveraged the `WebDriverAwait` class to enable better detection of desired load states
- Each record is saved while scraping instead of all at the end; minimizing data loss for a failed session.

NOTES AND THINGS TO THINK ABOUT:
- Twitter will block you from logging in via the webdriver if you log in too many times in a single day.
- The `scroll_down_page` function has an argument for `num_seconds_to_load` that represents the num of
seconds that the program will wait until attempting to scroll again. I'm currently making 5 attemps with
a pause between. You could also increase the number of max attempts and decrease the `num_seconds_to_load`.
This could possibly speed up the scraping as you would be more likely to get to a successfull scroll down
quicker.
-  The `collect_all_tweets_from_current_view` function has a `lookback_limit` argument that controls how
many tweets are processed from each scroll. I've written more about this in the function docstring.
- I've implemented `WebDriverWait` in several sections of this updated code. I think this is a much
better solution than a hard-coded `sleep` call because it will only timeout after a certain period of
time if specific conditions are not met. There are many other sections of this code that could be
improved, I'm sure, by leveraging this class.
- Feel free to replace the `save_tweet_data_to_csv` function with any other `io` option you want, such
as a database save via `pyodbc`, `sqlite3`, or whatever you want really.
- I encourage you to explore the "Advanced Search" functionality. Try adding your criteria and see how the url
 is built. You can then leverage this to make your searches more customized... with date ranges, special keywords,
 etc...  --> https://twitter.com/search-advanced?
