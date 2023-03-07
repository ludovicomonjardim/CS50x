import os
import re
import datetime
import requests

from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.security import check_password_hash, generate_password_hash
from helpers import apology, login_required, lookup, usd
from functools import wraps


# Configure application
app = Flask(__name__)

# Custom filter
app.jinja_env.filters["usd"] = usd

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///finance.db")

# Make sure API key is set
if not os.environ.get("API_KEY"):
    raise RuntimeError("API_KEY not set")


@app.after_request
def after_request(response):
    """ Ensure responses aren't cached """
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


@app.route("/login", methods=["GET", "POST"])
def login():
    """ Log user in """

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure password was submitted
        if not request.form.get("password"):
            return apology("must provide password", 403)

        # Query users.db for username
        rows = db.execute("SELECT * FROM users WHERE username = ?",
                          request.form.get("username"))

        if not user_pass_ok("password", rows):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """ Log user out """

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


@app.route("/register", methods=["GET", "POST"])
def register():
    """ Register user """

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 400)

        # Ensure password was submitted
        if not request.form.get("password"):
            return apology("must provide password", 400)

        # Ensure confirmation was submitted
        if not request.form.get("confirmation"):
            return apology("must provide password confirmation", 400)

        # Ensure password and confirmation are the same
        if request.form.get("password") != request.form.get("confirmation"):
            return apology("confirmation failed", 400)

        # Ensure username does NOT exists
        rows = db.execute("SELECT * FROM users WHERE username = ?", request.form.get("username"))
        if len(rows) > 0:
            return apology("invalid username", 400)

        # Ensure password meets mandatory conditions
        """ if not valid_password(request.form.get("password")):
            return apology("invalid password", 999) """

        # Save user in database
        db.execute("INSERT INTO users (username, hash) VALUES (?, ?)",
                   request.form.get("username"), generate_password_hash(request.form.get("password")))

        # Redirect user to home page
        return redirect("/"), 200

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("register.html"), 200


@app.route("/change_pass", methods=["GET", "POST"])
def change_pass():
    """ Change user password """

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 400)

        # Ensure OLD password was submitted
        if not request.form.get("old_password"):
            return apology("provide actual password", 400)

        if not user_pass_ok("old_password"):
            return apology("invalid username and/or password", 400)

        # Ensure NEW password was submitted
        if not request.form.get("password"):
            return apology("must provide new password", 400)

        # Ensure confirmation was submitted
        if not request.form.get("confirmation"):
            return apology("must provide password confirmation", 400)

        # Ensure password and confirmation are the same
        if request.form.get("password") != request.form.get("confirmation"):
            return apology("confirmation failed", 400)

        # Ensure password meets mandatory conditions
        if not valid_password(request.form.get("password")):
            return apology("invalid new password", 400)

        # Save user in database
        db.execute("UPDATE users SET hash=? WHERE username=?",
                   generate_password_hash(request.form.get("password")), request.form.get("username"))

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("change_pass.html")


symbol = ""


@app.route("/quote", methods=["GET", "POST"])
@login_required
def quote():
    """ Get quote. """

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure a symbol was submitted
        if not request.form.get("symbol"):
            return apology("must provide a symbol", 400)

        quote = lookup(request.form.get("symbol"))

        global symbol
        symbol = request.form.get("symbol")

        # Ensure a valid symbol was submitted
        if quote == None:
            return apology("invalid symbol", 400)

        now = datetime.datetime.now()
        time = now.strftime("at %H:%M:%S on %Y-%m-%d")
        return render_template("quote_refresh.html", quote=quote, time=time)

    # User reached route via GET (as by clicking a link or via redirect)
    return render_template("quote.html")


@app.route('/get_time')
def get_time():
    now = datetime.datetime.now()
    date_time = now.strftime("at %H:%M:%S on %Y-%m-%d")
    price = usd(lookup(symbol)["price"])
    return [date_time, price]


@app.route("/quote_refresh", methods=["GET"])
def quote_refresh():
    """ Get quote. """
    return render_template("quote.html")


@app.route("/add_cash", methods=["GET", "POST"])
@login_required
def add_cash():
    """Add additional cash to user's account"""

    # Get users cash
    cash = get_cash()

    # User reached route via POST
    if request.method == "POST":

        # Ensure cash was submitted
        if not request.form.get("cash"):
            return apology("must provide cash", 400)

        # Update user's cash
        db.execute("UPDATE users SET cash=? WHERE id=?;",
                   cash + float(request.form.get("cash")), session["user_id"])

        flash("Current available cash: $" +
              usd(cash + float(request.form.get("cash"))))

    # User reached route via GET
    else:
        flash("Current available cash: $" + usd(cash))

    return render_template("add_cash.html")


@app.route("/history")
@login_required
def history():
    """Show history of transactions"""
    rows = db.execute(
        "SELECT * FROM transactions WHERE user = ?", session["user_id"])
    return render_template("history.html", rows=rows)


@app.route("/symbols")
@login_required
def symbols():
    # Contact API

    try:
        api_key = os.environ.get("API_KEY")
        url = f"https://api.iex.cloud/v1/data/CORE/REF_DATA?token={api_key}"
        response = requests.get(url)
        response.raise_for_status()
    except requests.RequestException:
        return redirect("/")

    # Parse response
    try:
        symbols = response.json()

        rows = []
        for symbol in symbols:
            rows.append({"symbol": symbol["symbol"],
                         "name": symbol["name"],
                         "exchange": symbol["exchange"],
                         "exchangeName": symbol["exchangeName"],
                         "type": symbol["type"],
                         "region": symbol["region"],
                         "currency": symbol["currency"],
                         "isEnabled": symbol["isEnabled"]})

    except (KeyError, TypeError, ValueError):
        return redirect("/")

    return render_template("symbols.html", rows=rows)


@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    """Sell shares of stock"""
    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        message = validate_tosell(request.form.get("shares"), request.form.get("symbol"))
        if message != "":
            return apology(message, 400)

        save_sell(int(request.form.get("shares")), request.form.get("symbol"))

        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    symbols = db.execute("SELECT symbol FROM stock;")
    return render_template("sell.html", symbols=symbols)


@app.route("/", methods=["GET", "POST"])
@login_required
def index():
    """Show portfolio of stocks"""

    if request.method == "POST":
        values = request.form
        for value in values:
            if value[0:7] != "shares_":
                # Ensure shares were submitted
                if not request.form.get("shares_"+value):
                    return apology("must provide shares", 400)

                # Ensure shares are a number
                try:
                    shares = int(request.form.get("shares_"+value))
                except:
                    return apology("invalid shares", 400)

                symbol = value
                break

        if shares == 0:
            return apology("missing shares")
        elif shares > 0:
            message = validate_tobuy(shares, symbol)
            if message != "":
                return apology(message, 400)
            else:
                save_buy(shares, symbol)
        else:
            message = validate_tosell(abs(shares), symbol)
            if message != "":
                return apology(message, 400)
            else:
                save_sell(abs(shares), symbol)

    # Get user's cash
    cash = get_cash()

    # Get available credit
    credit = get_credit(cash)

    # Lookup for PRICE and COMPANY name
    rows = db.execute("SELECT * FROM stock WHERE user = ?", session["user_id"])
    for row in rows:
        quote = lookup(row["symbol"])
        row["price"] = quote["price"]
        row["company"] = quote["name"]

    return render_template("index.html", rows=rows, credit=credit, cash=cash)


@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    """Buy shares of stock"""

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        message = validate_tobuy(request.form.get("shares"), request.form.get("symbol"))
        if message != "":
            return apology(message, 400)

        shares = int(request.form.get("shares"))
        symbol = request.form.get("symbol").upper()

        save_buy(shares, symbol)

    # Get available credit and flash it
    credit = get_credit(get_cash())
    flash("Available credit: $" + usd(credit))

    if request.method == "POST":
        return redirect("/")

    return render_template("buy.html")


##########################################
# UDF
##########################################

# Returns USER's CASH
def get_cash():
    return db.execute("SELECT cash FROM users WHERE id = ?", session["user_id"])[0]["cash"]


# Returns USERs CREDIT
def get_credit(cash):
    rows = db.execute("SELECT * FROM stock WHERE user=?", session["user_id"])
    spent = 0
    for row in rows:
        price = lookup(row["symbol"])["price"]
        spent += (row["shares"] * price)
    return cash - spent


# Effectively saves the sale
def save_sell(shares, symbol):
    # Lookup for the symbol to get the price
    quote = lookup(symbol)

    # Save sale in database
    db.execute("INSERT INTO transactions (price, shares, user, symbol) VALUES (?, ?, ?, ?);",
               quote["price"],
               shares*(-1),
               session["user_id"],
               symbol)

    # Get current share stock
    shares_in_stock = int(db.execute("SELECT shares FROM stock WHERE user=? AND symbol=?",
                                     session["user_id"], symbol)[0]["shares"])

    # Final stock = 0, delete row
    if shares_in_stock - shares <= 0:
        db.execute("DELETE FROM stock WHERE user=? AND symbol=?;",
                   session["user_id"], symbol)
    else:
        # Update shares in stock
        db.execute("UPDATE stock SET shares=shares-? WHERE user=? AND symbol=?;",
                   shares, session["user_id"], symbol)

    flash("Sold!")
    return


# Effectively saves the buy
def save_buy(shares, symbol):

    quote = lookup(symbol)
    # Save purchase in database
    db.execute("INSERT INTO transactions (price, shares, user, symbol) VALUES (?, ?, ?, ?);",
               quote["price"],
               shares,
               session["user_id"],
               symbol)

    # Update stock
    row = db.execute("SELECT * FROM stock WHERE user=? AND symbol=?;",
                     session["user_id"], symbol)

    # Insert new symbol
    if len(row) == 0:
        db.execute("INSERT INTO stock (shares, user, symbol) VALUES (?, ?, ?);",
                   shares, session["user_id"], symbol)
    else:
        # Update shares in stock

        db.execute("UPDATE stock SET shares=shares+? WHERE user=? AND symbol=?;",
                   shares, session["user_id"], symbol)

    flash("Bought!")
    return


#  Returns 0 if password meets mandatory conditions. Otherwise, -1.
def valid_password(password):
    flag = 0

    if len(password) <= 8:
        flag = -1
    elif not re.search("[a-z]", password) and not re.search("[A-Z]", password):
        flag = -1
    elif not re.search("[0-9]", password):
        flag = -1
    elif not re.search("[~`!@#$%^&*()-_+={}[]|\;:\"<>,./?]", password):
        flag = -1

    return flag == 0


# Returns TRUE if USER and PASSWORD are in DB.
def user_pass_ok(password, rows=""):
    if rows == "":
        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = ?",
                          request.form.get("username"))

    # Ensure username exists and password is correct
    if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get(password)):
        return False
    return True


# Return TRUE if shares are grater than stock. Otherwise, FALSE. """
def too_many(shares, symbol):
    stock = db.execute("SELECT shares FROM stock WHERE symbol=?;", symbol)
    if stock[0]["shares"] < shares:
        return True
    return False


# Returns "" if shares are valid. Otherwise, corresponding erro message.
def validate_tosell(shares, symbol):
    # Ensure a symbol was submitted
    if not symbol:
        return "must provide a symbol"

    # Ensure shares was submitted
    if shares == "":
        return "missing shares"

    # Ensures shares are not greater than the stock
    if too_many(int(shares), symbol):
        return "too many shares"

    return ""


#  Returns "" if shares are valid. Otherwise, corresponding erro message.
def validate_tobuy(shares, symbol):

    # Ensure a symbol was submitted
    if not symbol:
        return "must provide a symbol"

    # Ensure a valid symbol was submitted
    quote = lookup(symbol)
    if quote == None:
        return "invalid symbol"

    # Ensure shares was submitted
    if shares == "":
        return "missing shares"

    # Ensure shares are a positive integer
    if not positive_int(shares):
        return "invalid shares"

    # Get available credit
    credit = get_credit(get_cash())

    # Ensure purchase is affordable
    if credit < (int(shares) * quote["price"]):
        return "can't afford"

    return ""


# Returns TRUE if shares is a POSITE INTEGER. Otherwise, FALSE.
def positive_int(shares):
    try:
        shares = int(shares)
        if shares < 0:
            # not POSITIVE INT
            return False
    except ValueError:
        # not INT
        return False
    return True