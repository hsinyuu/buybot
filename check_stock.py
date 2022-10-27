from selenium import webdriver
import chromedriver_binary
import threading
import time
from exponent_server_sdk import (
    DeviceNotRegisteredError,
    PushClient,
    PushMessage,
    PushServerError,
    PushTicketError,
)
from requests.exceptions import ConnectionError, HTTPError
from pydub import AudioSegment
from pydub.playback import play

def send_push_message(token, message, extra=None):
    try:
        response = PushClient().publish(
            PushMessage(to=token,
                        body=message,
                        data=extra))
    except PushServerError as exc:
        # Encountered some likely formatting/validation error.
        rollbar.report_exc_info(
            extra_data={
                'token': token,
                'message': message,
                'extra': extra,
                'errors': exc.errors,
                'response_data': exc.response_data,
            })
        raise
    except (ConnectionError, HTTPError) as exc:
        # Encountered some Connection or HTTP error - retry a few times in
        # case it is transient.
        rollbar.report_exc_info(
            extra_data={'token': token, 'message': message, 'extra': extra})
        raise self.retry(exc=exc)

    try:
        # We got a response back, but we don't know whether it's an error yet.
        # This call raises errors so we can handle them with normal exception
        # flows.
        response.validate_response()
    except DeviceNotRegisteredError:
        # Mark the push token as inactive
        from notifications.models import PushToken
        PushToken.objects.filter(token=token).update(active=False)
    except PushTicketError as exc:
        # Encountered some other per-notification error.
        rollbar.report_exc_info(
            extra_data={
                'token': token,
                'message': message,
                'extra': extra,
                'push_response': exc.push_response._asdict(),
            })
        raise self.retry(exc=exc)

def check_stock():
    print("Check stock...")
    items = [
        {'name': 'Coffee Bag', 'url': 'https://www.jellycat.com/us/amuseable-coffeetogo-bag-a4cofb/'},
        {'name': 'Toast Bag', 'url': 'https://www.jellycat.com/us/amuseable-toast-bag-a4tb/'},
        {'name': 'Watermelon Bag','url': 'https://www.jellycat.com/us/amuseable-watermelon-bag-a4wb/'},
        {'name': 'Scallop','url': 'https://www.jellycat.com/us/sensational-seafood-scallop-ssea6sc/'},
    ]
    op = webdriver.ChromeOptions()
    op.add_argument('headless')
    wd = webdriver.Chrome(options=op)
    wd.implicitly_wait(5)
    wd.maximize_window()
    in_cart = list()
    out_of_stock = list()
    for item in items:
        name, url = item['name'], item['url']
        print("Checking item %s, url %s"%(name, url))
        wd.get(url)
        buy_button = wd.find_element('xpath', '//*[@id="variant-grid-area"]/div[4]/div[2]/div[11]/form[1]/div[1]/input')
        if buy_button.is_displayed():
            #buy_button.click()
            #continue_shopping_button = wd.find_element('xpath', '//*[@id="addtobasket"]/div/div[4]/a[1]')
            #continue_shopping_button.click()
            in_cart.append(name)
        else:
            print("%s Out of stock"%(name))
            out_of_stock.append(name)
            #cnmjcswd20180709
    wd.close()
    if in_cart:
        print("In stock: %s"%(in_cart))
        print("Out of stock: %s"%(out_of_stock))
        send_push_message(token, "In stock: %s"%(in_cart))
        alarm = AudioSegment.from_mp3("alarm.mp3")
        play(alarm)
    else:
        print("do nothing")

INTERVAL_IN_SEC = 10*60
while True:
    check_stock()
    print("Check stock in %ss"%(INTERVAL_IN_SEC))
    time.sleep(20)


# Checkout
#cart_button = wd.find_element('xpath', '//*[@id="cdnBasket2"]/span[2]/span[1]')
#cart_button.click()
#to_checkout_button = wd.find_element('xpath', '//*[@id="main"]/div[2]/form/div[1]/a')
#to_checkout_button.click()
#checkout_button = wd.find_element('xpath', '//*[@id="main"]/div[3]/div/div[2]/div/div/a')
#checkout_button.click()
