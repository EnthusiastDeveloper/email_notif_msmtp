# email_notif_msmtp

This repository contains scripts for sending emails via SMTP, based on Linux `msmtp`.

## Description

The repository contains the following files:

- `prepare_and_send_email.py`: Bash script prepares and sends emails based on a template file and using msmtp.
- `prepare_and_send_email.py`: Python3 script prepares and sends emails based on a template file and using msmtp.
- `template.txt`: Template file with placeholders for sender, recipient, email subject and body.

## Requirements

- Python 3.6+
- msmtp installed and configured (`~/.msmtprc`) (see [ArchWiki - msmtp](https://wiki.archlinux.org/title/Msmtp) for more information)
- Only for Python3 script - write access to `/var/log/` directory

## Usage
First, edit the `template.txt` file and set the desired sender and receipient email addresses, as these are not covered by the scripts.

Then, run the script with the following command:

```bash
prepare_and_send_email` -t "Subject" -b "Body" [-h "Hostname"]
# Example
prepare_and_send_email.py -t "test email topic" -b "test email body" -h "Hostname"
```
Or

```python3
prepare_and_send_email.py -t "Subject" -b "Body" [-h "Hostname"]
# Example
python3 prepare_and_send_email.py -t "test email topic" -b "test email body" -h "Hostname"
```

The script will read the template file and replace the placeholders with the provided values, then send the email using msmtp.
