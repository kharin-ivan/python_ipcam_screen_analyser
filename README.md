# python_ipcam_screen_analyser
Task - store motion detection sccrenshot from ip cam

put this file into /var/www/mailanalyzer

we use postfix for Mail Queue

ipcam smtp settings:
smtp : yoursmtp server
tomail: youmailbox@yoursmtp server
user: alert

postfix alias file:
alert: "|python /var/www/mailanalyzer/mail.py >> /var/www/mailanalyzer/log"






