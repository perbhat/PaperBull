import random
import models
import datetime

now = lambda: datetime.datetime.now()

# TODO: We need to centralize API usage
import stockquotes

TRANSACTION_MODES = {"Buy", "Sell"}


class ErrorMessages:
    """ Client-Side friendly. Consider moving to JS """
    INVALID_USER = "Invalid User"
    INVALID_REQUEST = "Invalid Request"
    INVALID_STOCK = "Invalid Stock"
    TRANS_EXPENSIVE = "Not enough money"
    TRANS_LACK_STOCK = "Not enough stocks"

    # TODO
    TRANS_TIMEOUT = "Transaction took too long to process"


def helper_get_stock_price(stock):
    try:
        return stockquotes.Stock(stock).current_price
    except stockquotes.StockDoesNotExistError:
        return None


def poll_stock_implementation(data):
    response = {}
    stock = data["ticker_symbol"]

    stock_price_or_none = helper_get_stock_price(stock)

    if stock_price_or_none is not None:
        response[stock] = stock_price_or_none
    else:
        response["error"] = ErrorMessages.INVALID_STOCK

    return response


def request_user_stock_info_implementation(data, db):
    response = {}

    user_id = int(data.get("user_id"))
    stock = data.get("ticker_symbol")

    db_user_stock_info = db.session.query(models.STOCKS).filter_by(
        username_id=user_id).filter_by(ticker=stock).first()

    if db_user_stock_info is None:
        response["quantity"] = 0
    else:
        response["quantity"] = db_user_stock_info.quantity
        response["avg_price"] = db_user_stock_info.avg_price

    return response


def process_transaction_implementation(data, db):
    response = {}

    # TODO: Add security when we have Google API Login
    user_id = int(data.get("user_id"))
    quantity = int(data.get("quantity"))
    stock = data.get("ticker_symbol")
    mode = data.get("transaction_mode")

    db_user_info = db.session.query(
        models.USERS).filter_by(username_id=user_id).first()
    db_prev_stock_info_or_none = db.session.query(models.STOCKS).filter_by(
        username_id=user_id).filter_by(ticker=stock).first()

    price_of_stock_or_none = helper_get_stock_price(stock)
    try:
        delta_of_transaction = price_of_stock_or_none * quantity
    except TypeError:
        response["error"] = ErrorMessages.INVALID_STOCK
        return response

    if mode == "Buy":
        if db_user_info.cash_balance < delta_of_transaction:
            response["error"] = ErrorMessages.TRANS_EXPENSIVE
            return response

        db_user_info.cash_balance -= delta_of_transaction

        avg_price = price_of_stock_or_none

        if db_prev_stock_info_or_none is not None:
            avg_price = (avg_price + db_prev_stock_info_or_none.avg_price) / 2
            db_prev_stock_info_or_none.avg_price = avg_price
            db_prev_stock_info_or_none.quantity += quantity
        else:
            new_stock_entry = models.STOCKS(username_id=user_id, ticker=stock, quantity=quantity, avg_price)


        new_history_entry = models.HISTORY(
            username_id=user_id,
            date=now(),
            stock=stock,
            quantity=quantity,
            action_type='buy',
            change_in_money=delta_of_transaction)

        db.session.add(new_history_entry)
        db.session.commit()
        
    elif mode == "Sell":
        if db_prev_stock_info_or_none is None or db_prev_stock_info_or_none.quantity < quantity:
            response["error"] = ErrorMessages.TRANS_LACK_STOCK
            return response

        db_user_info.cash_balance += delta_of_transaction

        if quantity == db_prev_stock_info_or_none.quantity:
            db.session.delete(prev_quantity_or_zero)
        else:
            prev_quantity_or_zero.quantity -= quantity

        new_history_entry = models.HISTORY(
            username_id=user_id,
            date=now(),
            stock=stock,
            quantity=quantity,
            action_type='sell',
            change_in_money=delta_of_transaction)

        db.session.add(new_history_entry)
        db.session.commit()
    else:
        response["error"] = ErrorMessages.INVALID_REQUEST
        return response
    
    # Any global Success Operations Here
    response["newBalance"] = db_user_info.cash_balance

    return response