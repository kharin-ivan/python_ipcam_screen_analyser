#!/usr/bin/python
# -*- coding: utf-8 -*-
import re, sys, os, email
from datetime import datetime
from email.header import decode_header

#set directory to save
directory = '/srv/sdb/alarm/img'
#some camera finds as local ip
local_ip = '172.24.82.117'

atom_rfc2822=r"[a-zA-Z0-9_!#\$\%&'*+/=?\^`{}~|\-]+"
atom_posfix_restricted=r"[a-zA-Z0-9_#\$&'*+/=?\^`{}~|\-]+" # without '!' and '%'
atom=atom_rfc2822
dot_atom=atom  +  r"(?:\."  +  atom  +  ")*"
quoted=r'"(?:\\[^\r\n]|[^\\"])*"'
local="(?:"  +  dot_atom  +  "|"  +  quoted  +  ")"
domain_lit=r"\[(?:\\\S|[\x21-\x5a\x5e-\x7e])*\]"
domain="(?:"  +  dot_atom  +  "|"  +  domain_lit  +  ")"
addr_spec=local  +  "\@"  +  domain
email_address_re=re.compile('^'+addr_spec+'$')
detectpointer = False

class Attachement(object):
    def __init__(self):
        self.data = None
        self.content_type = None
        self.size = None
        self.name = None

def getmailheader(header_text, default="ascii"):
    """Decode header_text if needed"""
    try:
        headers=decode_header(header_text)
    except email.Errors.HeaderParseError:
        # This already append in email.base64mime.decode()
        # instead return a sanitized ascii string
        return header_text.encode('ascii', 'replace').decode('ascii')
    else:
        for i, (text, charset) in enumerate(headers):
            try:
                headers[i]=unicode(text, charset or default, errors='replace')
            except LookupError:
                # if the charset is unknown, force default
                headers[i]=unicode(text, default, errors='replace')
        return u"".join(headers)

def getmailaddresses(msg, name):
    """retrieve From:, To: and Cc: addresses"""
    addrs=email.utils.getaddresses(msg.get_all(name, []))
    for i, (name, addr) in enumerate(addrs):
        if not name and addr:
            # only one string! Is it the address or is it the name ?
            # use the same for both and see later
            name=addr

        try:
            # address must be ascii only
            addr=addr.encode('ascii')
        except UnicodeError:
            addr=''
        else:
            # address must match adress regex
            if not email_address_re.match(addr):
                addr=''
        addrs[i]=(getmailheader(name), addr)
    return addrs

def parse_attachment(message_part, ip, date):
    content_disposition = message_part.get("Content-Disposition", None)
    if content_disposition:
        dispositions = content_disposition.strip().split(";")
        if bool(content_disposition and dispositions[0].lower() == "attachment"):
            attachment = Attachement()
            attachment.data = message_part.get_payload(decode=True)
            attachment.content_type = message_part.get_content_type()
            attachment.size = len(attachment.data)
            attachment.name = message_part.get_filename()
            #Creating directory
            date_for_dir_name = date.strftime("%Y-%m/%d")
            dir = directory + '/' + (ip) + '/' + date_for_dir_name
            if not os.path.exists(dir):
                os.makedirs(dir)
                os.chmod(dir,0777)
                subdir_ip = directory + '/' + (ip)
                os.chmod(subdir_ip, 0777)
                subdir_year = subdir_ip + '/' + date.strftime("%Y-%m")
                os.chmod(subdir_year,0777)
                subdir_day = subdir_year + '/' + date.strftime("%d")
                os.chmod(subdir_day,0777)
                print('cant find directory: ',dir,', creating done with: ', os.path.exists(dir))
            filedir = dir + '/' +attachment.name
            print ('find file in mail - save:',filedir)
            file = open(filedir, 'w+')
            file.write(attachment.data)
            file.close()
            os.chmod(filedir,0666)
            return attachment.name

    return None

def recognizecam(received):
    ipPattern = re.compile('\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}')
    findIP = re.findall(ipPattern,received)

    if findIP:
        if findIP[0] == local_ip:
            # print('problem while reading IP. error - local ip find, using last ip in list, PRINT IP =====> ', findIP)
            return findIP[1]
        return findIP[0]
    else:
        return ''

def savetodb(ip,date,screen=None, detect=None):
    import MySQLdb as mysql
    conn =mysql.connect(host="localhost",user="event", passwd="passwd",db="cams_event")
    x = conn.cursor()
    try:
        x.execute("""INSERT INTO `event`(`cam`, `chanel`, `type`, `date`, `screen`) VALUES (%s,%s,%s,%s,%s)""",(ip,0,'motion',date,screen))
        conn.commit()
        result=True
    except:
        conn.rollback()
        result=False
    conn.close()
    return result

if __name__=='__main__':

    msg = email.message_from_file(sys.stdin)
    received=getmailheader(msg.get('Received', ''))
    ip =  recognizecam(received)
    if ip:
        # print ('find ip = ', ip)
        curr_date = datetime.now()
        if(msg.is_multipart()):
            for part in msg.walk():
                attachement = parse_attachment(part, ip, curr_date)
                #uncomment for print message without attach
                # if not attachement:
                #     print(msg)
        if attachement:
            res = savetodb(ip,curr_date,attachement)
            # print('mysql insert data = ', res)
            # print 'Ivan DECoDER END =====<<<<<<<<'
    else:
        print(received)
        print(getmailheader(msg.get('From', '')))
        print 'Ivan DECoDER END WITH NULL =ERROR==error==ERROR==error==ERROR==error==ERROR==error==ERROR==ERROR==ERROR==ERROR==ERROR==ERROR==ERROR='





