"""Sends an email regarding problems in the PAGER workflow.
"""

import sys, smtplib, socket
from getpass import getpass
from email.mime.text import MIMEText

import json,os
import checkError

def sendEmail(server, fromaddr, toaddrs, smallKey, workspace, logs):
    """send email
    Args:
        server: smtp server
        fromaddr: sender email address
        toaddrs: receriver email addresses
        smallKey: smallKey
        worksapce: playload folder
        logs: log list holds all log items for current publication
    """

    try:
        #Get the UUID from the supplied JSON file
        try:
            jsonPath = os.path.join(workspace, smallKey + '.json')
            jsonData = open(jsonPath)
            jsonObj = json.load(jsonData)
            jsonData.close()
        except IOError:
            checkError.printLog(logs,"Json file is not found")
            raise

        uuid = jsonObj['config']['UUID']


        errorInfo = '\n'.join([str(i) for i in logs])

        subject ="Error publishing data for UUID [{0}]".format(uuid)

        body= """Hello,

        This email is to inform you of a potential problem in the PAGER (Publication to ArcGIS Environments and RAMP) workflow that has returned a status code requiring your attention.

        {0}]

        Please get in touch with the BASD development team if you believe this error requires their attention.
        """.format(errorInfo)

        msg = MIMEText(body)
        msg['Subject'] = subject
        msg['From'] = fromaddr
        msg['To'] = toaddrs

        # sending
        toaddrs= toaddrs.split(',')
        session = smtplib.SMTP(server)

        try:
            session.sendmail(fromaddr, toaddrs, msg.as_string())
        finally:
            session.quit()

    except (socket.gaierror, socket.error, socket.herror, smtplib.SMTPException), e:
        checkError.printLog(logs,str(e.errno) + ":"+ e.strerror)
        raise
    else:
       checkError.printLog(logs,"Mail successfully sent.")

