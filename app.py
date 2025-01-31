from flask import Flask, request
import json
import requests
import telethon
import zipfile
import io
import asyncio

from secret import *

app = Flask(__name__)
client = telethon.TelegramClient('/app/data/tg', API_ID, API_HASH)
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from telethon.types import DocumentAttributeFilename

event_loop = asyncio.get_event_loop()
event_loop.run_until_complete(client.connect())

email_to_send = [email_from]
@app.route('/webhooks/master-thesis', methods=['POST'])
@app.route('/', methods=['POST'])
def test():
    data = json.loads(request.data)
    print('Received:', request.data)
    reason = request.headers.get('X-GitHub-Event')
    # check if the event is a release
    if reason == 'ping':
        event_loop.run_until_complete(client.send_message('me', 'pong'))
        return 'OK'
    if reason == 'workflow_run':
        if (data['action'] == 'completed'
                and data['workflow_run']['conclusion'] == 'success'
                and data['workflow_run']['status'] == 'completed'):
            #event_loop.run_until_complete(client.send_message('me', 'Workflow completed'))
            # Get the artifacts of the workflow
            artifacts_url = data['workflow_run']['artifacts_url']
            #event_loop.run_until_complete(client.send_message('me', artifacts_url))
            # We should have only one artifact, so we get the first one
            response = requests.get(artifacts_url, headers={'Authorization': f'token {GITHUB_TOKEN}'})
            artifacts = response.json()['artifacts']
            if len(artifacts) != 1:
                return 'OK'
            artifact = response.json()['artifacts'][0]
            # Download the artifact
            download_url = artifact['archive_download_url']
            #event_loop.run_until_complete(client.send_message('me', download_url))
            artifact = requests.get(download_url, headers={'Authorization': f'token {GITHUB_TOKEN}'})
            # Unzip the artifact: There should me only one file, the thesis
            # we do not know the name of the file, so we need to extract it
            with zipfile.ZipFile(io.BytesIO(artifact.content)) as z:
                file_name = z.namelist()[0]
                thesis = z.read(file_name)
                # Send the thesis to everyone in the list
                for contact, name in telegram_contacts_to_send.items():
                    event_loop.run_until_complete(
                        client.send_file(
                            contact, thesis, caption=f'Ciao {name}, ti invio la nuova versione della tesi!',
                            attributes=[DocumentAttributeFilename('thesis.pdf')]))
        return 'OK'
    if reason == 'release':
        if data['action'] == 'published':
            # get the assets url
            assets_url = data['release']['assets_url']
            # get the assets
            response = requests.get(assets_url, headers={'Authorization': f'token {GITHUB_TOKEN}'})
            assets = response.json()
            # get the pdf
            pdf = next(asset for asset in assets if asset['content_type'] == 'application/pdf')
            # download the pdf, set accept header to octet-stream
            pdf = requests.get(pdf['url'], headers={'Accept': 'application/octet-stream',
                                                                     'Authorization': f'token {GITHUB_TOKEN}'})
            version = data['release']['tag_name']
            # Send email to everyone in the list and attach the PDF (gmail servers)
            with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
                server.login(email_from, email_password)
                for email in email_to_send:
                    msg = MIMEMultipart()
                    msg['From'] = email_from
                    msg['To'] = email
                    msg['Subject'] = 'Tesi {}'.format(version)
                    msg.attach(MIMEText('Gentile professore,\n'
                                        'le invio la versione {} della mia tesi.\n'
                                        'Attendendo un suo riscontro,\n'
                                        'la saluto cordialmente.'.format(version)))
                    attachment = MIMEBase('application', 'octet-stream')
                    attachment.set_payload(pdf.content)
                    encoders.encode_base64(attachment)
                    attachment.add_header('Content-Disposition', 'attachment', filename='thesis.pdf')
                    msg.attach(attachment)
                    server.sendmail(email_from, email, msg.as_string())
        return 'OK'
    return 'OK'


if __name__ == '__main__':
    app.run(port=8080, host='0.0.0.0')
