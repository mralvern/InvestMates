# InvestMates
Team Name:
InvestMates

Application Website:
https://investmates.onrender.com/

Feature testing and bug fixes:
https://docs.google.com/document/d/10zmWhCe5TISr3lnODhZNB2JDzhrppL2D2pE1DiUjQ4E/edit?usp=sharing

Proposed Level of Achievement:
Apollo 11

Project Scope (Summarised):
To create a web application where users are able to store and track their stocks on a dentralised dashboard where their profile is protected with their login details 

Project Scope (Expanded):
We want to create a web application that is easy to use where users are able to access data that they have previously keyed. This data will be tied to their individual accounts and can be editted to their preference. Users of the app should have the freedom to add, remove, and modify the stocks and the quantity of those stocks in their portfolio according to their preference. This is necessary as the stock market is ever changing and the liberity to change their portfolio is a key feature for investors.

The other platforms available right now only show the stocks that you have purchased through them. However, with InvestMates, stocks from every platform can be manually keyed into their account to track on a centralised platform.

The application would automatically help them calculate their total asset value and their Gain/Loss on their position. At a glance, users of the app should be able to see 2 key sets of information; how their stocks are performing and their total asset value.


Motivation: Being avid finance enthusiasts, justin and alvern have tried many financial applications to experiment with the stock market. During the covid-19 pandemic, there were many attractive promotions and deals for stock brokers, leading to us having stocks on multiple platforms. Furthermore with the boom in popularity of Cryptocurrency and most platforms not supporting it, it led to us having even more platforms where we track and store our investments. 

All was well and good for a while, until we realised that having investments across multiple platforms had its disadvantageous. Furthermore, with how much the markets fluctuate and given the risky nature of these investments, it has been increasingly more important for us investors to manage our investments. It became confusing toggling between so many applications to track your stocks, resulting in more work needed to be done to manage them. 


Vision:
InvestMate will be an application for investors to track all their investments that they own on their multiple platforms. They will be able to create and manage their portfolios. 

Investors will then be able to use their investments and portfolios to create personalised investment dashboards. They will be able to select what kind of data they would like to view and manage their investments accordingly. 

User stories:
 1. As an investor, I would like to have a single platform where I can track all my investments from different brokers
 2. As an investor, I would like to be able to view data and charts of my investments on a personalised dashboard
 3. As an investor, I would want to be able to view the real time prices of individual stocks and ETFs
 4. As an investor, I would like the ability to share my portfolio with other peers  
 5. As an investor, I would like to determine the performance of my stocks at a glance


Completed core features:
 1. User account authentication
InvestMate is a personalised portfolio application, hence each user would need to be authenticated with his/her unique account.

InvestMate requires the user to register with their email, as well as a unique username and valid password. Users would only be able to access the web page if they have a valid account.

Upon successful registration, the user will be redirected to the login page where they can login using the username and password they have chosen.

![image](https://github.com/mralvern/InvestMates/assets/100460765/9e0e27b5-187c-467b-8534-2366596a7bb5)


 2. Stock tracking
The stocks that the user owns would be displayed in a table form on the dashboard page. InvestMates uses Yahoo Finance! API in order to get the current prices of any stock on the US market. The current prices are displayed and updated in real time. 

InvestMates also automatically calculates the day gain/loss of stocks the user owns. Using Yahoo Finance! API, we fetch the current price as well as the open price of the stock. The difference in these prices will give us the day gain of the stock. The day gain/loss is calculated for each stock using the formula: day gain * stock quantity.
The total day gain/loss is calculated by summing the day gain/loss for each stock the user owns.


 3. Portfolio creation
Portfolio Creation 
Upon logging in to InvestMates, the user will now be able to add stocks to their portfolio. 
The required fields for the submission form are the stock’s ‘Stock Name’, ‘Quantity’, ‘Purchase Price’ and ‘Purchase Date’. 

Users are also able to use the import csv file function to import stock data they have exported from their different brokers. The formatting for the csv file would be ‘Stock Name’, ‘Purchase Price’ and ‘Purchase Date’. Users have to follow this exact format in order for the import function to work.

We use sqlalchemy to track each user’s data and the stocks they hold. Upon adding all the stocks the user owns, their portfolio will display the overall performance and value, providing overview of the user’s investments.


 4. Automatic calculation of total assets
Users can easily determine their total portfolio value at a glance 
- Upon rendering of the dashboard page, InvestMates will iterate through the list of stocks the user has and retrieve the quantity and current price with the formula: stock quantity * current stock price. 

- Total portfolio value would be calculated by the summation of the individual stocks in the portfolio


 5. Automatic calculation of Gain/Loss on their stocks
Users can easily determine thier Gain or Loss on each of their stocks.
- The yfinance api will fetch current price and the open price. The difference in these prices will give us the day gain price: open price - current price = day gain/loss

- the day gain/ loss for each ticker is then calculated with the formula: day gain * stock quantity

- The total day gain/loss is calcaulated by adding the day gain/ loss of each ticker


Application Use FlowChart
![image](https://github.com/mralvern/InvestMates/assets/100460765/c7e88eae-6107-4602-a9aa-e65689d55496)
