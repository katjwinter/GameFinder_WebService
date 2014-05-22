NOTE: Additional requirements for this project are LXML and BS4 (Beautiful Soup).

This is a web service written in Python on the bottle framework and to be hosted on Google App Engine (thus the app.yaml file). It's purpose is to query the Best Buy BBY API service and to scrape gamestop.com, both in order to gather game pricing and location availability information for a specified game.

I wrote the web service to serve as the back end to an IPhone App (GameFinder_IPhoneApp) and not to serve as a standalone web app. 

IMPORTANT: Gamestop has made some code changes on their site which has broken some of the scraping I do. This was originally written as a school project and so I hard coded some of the site interaction due to time constraints (esp since the purpose of the project was the IPhone app, so I could only spend but so much time on the supporting web service). In any case, right now the web service should be considered non-functional.
