import os
from linebot.models.messages import FileMessage, ImageMessage
import pymysql
from flask import Flask, request, abort

from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.exceptions import (
    InvalidSignatureError
)
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage, ImageSendMessage
)

import time
import tempfile

import requests
import base64
from requests.structures import CaseInsensitiveDict

from flask_sslify import SSLify
# headers = CaseInsensitiveDict()
# headers["Authorization"] = "Bearer ESQrr+IOU3N5cWYyaXVlGpu3FuOu2C2jRl12uXP6QkqVNtYV5oRCKxqaPLoFqZYOz3/oGqMNEQjzbkfIgmZ9dIYfU5Q3L8zsyfbvDzDHziCsL5mdzPPX7+XW4WHZ3X5u5+SCn++aqAIzC4YSW24TNQdB04t89/1O/w1cDnyilFU="

static_tmp_path = os.path.join(os.path.dirname(__file__), 'static', 'tmp')

app = Flask(__name__)
sslify = SSLify(app)

line_bot_api = LineBotApi(
    'ESQrr+IOU3N5cWYyaXVlGpu3FuOu2C2jRl12uXP6QkqVNtYV5oRCKxqaPLoFqZYOz3/oGqMNEQjzbkfIgmZ9dIYfU5Q3L8zsyfbvDzDHziCsL5mdzPPX7+XW4WHZ3X5u5+SCn++aqAIzC4YSW24TNQdB04t89/1O/w1cDnyilFU=')
handler = WebhookHandler('f3ecd5b2a186a01049a89635ec6ab2b9')


def connect_db_broadcast():
    conn = pymysql.connect(
        host='remotemysql.com', user='begrcbym37', password='BnHj0FciX0', db='begrcbym37')
    return conn


@app.route("/callback", methods=['POST'])
def callback():
    # Get X-Line-Signature header value
    signature = request.headers['X-Line-Signature']

    # Get request body as text
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    # Handle webhook body
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return 'OK'


def bc(PESAN):
    db_broadcast = connect_db_broadcast()
    cursor_broadcast = db_broadcast.cursor()

    if(PESAN == "!bc-text"):
        sql_select = "SELECT * FROM tb_outbox WHERE flag_line=1 AND type='msg'"
        cursor_broadcast.execute(sql_select)
        results = cursor_broadcast.fetchall()

        if(cursor_broadcast.rowcount == 0):
            print("Tidak ada pesan yang ingin dikirim.")
        else:
            print("Terdapat pesan yang ingin dikirim.")
            print("-----Broadcast Via Line-----")
            users = ["U18bafb1de4d5a7014e46e6255371c56a",
                     "U1b3519cef04ba5d611e5fd056d335693"]
            for data in results:
                print("***Memulai broadcast dengan pesan = ", data[1])
                try:
                    line_bot_api.broadcast(TextSendMessage(text=data[1]))
                    print("- Menungu {} detik".format(4))
                    time.sleep(4)
                except Exception as e:
                    print("Error:", e)
                    print("Menungu {} detik".format(4))
                    time.sleep(4)
                sql = "UPDATE tb_outbox SET flag_line = %s WHERE id_outbox = %s"
                val = (2, data[0])
                cursor_broadcast.execute(sql, val)
                db_broadcast.commit()

            print("-----Broadcast Pesan Via Line SELESAI-----")

    elif(PESAN == "!bc-img"):
        sql_select = "SELECT * FROM tb_outbox WHERE flag_line=1 AND type='image'"
        cursor_broadcast.execute(sql_select)
        results = cursor_broadcast.fetchall()

        if(cursor_broadcast.rowcount == 0):
            print("Tidak ada gambar yang ingin dikirim.")
        else:
            print("Terdapat gambar yang ingin dikirim.")
            print("-----Broadcast Via Line-----")
            users = ["U18bafb1de4d5a7014e46e6255371c56a",
                     "U1b3519cef04ba5d611e5fd056d335693"]
            for data in results:
                print("***Memulai broadcast dengan gambar = ", data[1])
                try:
                    line_bot_api.broadcast(ImageSendMessage(
                        original_content_url=data[1],
                        preview_image_url=data[1]
                    ))
                    print("- Menungu {} detik".format(4))
                    time.sleep(4)
                except Exception as e:
                    print("Error:", e)
                    print("Menungu {} detik".format(4))
                    time.sleep(4)
                sql = "UPDATE tb_outbox SET flag_line = %s WHERE id_outbox = %s"
                val = (2, data[0])
                cursor_broadcast.execute(sql, val)
                db_broadcast.commit()

            print("-----Broadcast Gambar Via Line SELESAI-----")

# Handler command dari user


@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    print("Info Webhook Event = ", event)
    db_broadcast = connect_db_broadcast()
    cursor_broadcast = db_broadcast.cursor()
    PESAN = event.message.text
    if(PESAN == "!bc-text" or PESAN == "!bc-img"):
        bc(PESAN)
    else:
        balasan = "=====PESAN BARU DITERIMA=====\n\nPesan yang ingin anda broadcast = " + PESAN + \
            "\n\nKirim perintah !bc-text untuk broadcast pesan."
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=balasan))
        sql = "INSERT INTO tb_outbox (out_msg, type, flag, flag_tele, flag_line, tgl) VALUES (%s, %s, %s, %s, %s, CURDATE())"
        val = (PESAN, "msg", 1, 1, 1)
        cursor_broadcast.execute(sql, val)
        db_broadcast.commit()


@handler.add(MessageEvent, message=ImageMessage)
def handle_image(event):
    print("Info Webhook Event Image = ", event)
    db_broadcast = connect_db_broadcast()
    cursor_broadcast = db_broadcast.cursor()

    image = event.message.id

    # Terima image dari user
    message_content = line_bot_api.get_message_content(image)
    with open(image + ".jpg", 'wb') as fd:
        for chunk in message_content.iter_content():
            fd.write(chunk)

    # Upload image ke Imgbb
    with open(image+".jpg", "rb") as file:
        url = "https://api.imgbb.com/1/upload"
        payload = {
            "key": "ec44685d5491f31446130b4458fe995f",
            "image": base64.b64encode(file.read()),
        }
        res = requests.post(url, payload)
        print(res)
        res_image = res.json()
        # Ambil url gambar dari imgbb
        url_image = res_image["data"]["url"]

    # Insert database
    sql = "INSERT INTO tb_outbox (out_msg, type, flag, flag_tele, flag_line, tgl) VALUES (%s, %s, %s, %s, %s, CURDATE())"
    val = (url_image, "image", 1, 1, 1)

    cursor_broadcast.execute(sql, val)
    db_broadcast.commit()

    # Pesan konfirmasi
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text="=====GAMBAR BARU DITERIMA=====\n\nKirim perintah !bc-img untuk broadcast gambar."))


if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
