# Send emails with Python

> Learn how to send your first email using the Resend Python SDK.

## Prerequisites

To get the most out of this guide, you'll need to:

* [Create an API key](https://resend.com/api-keys)
* [Verify your domain](https://resend.com/domains)

## 1. Install

Get the Resend Python SDK.

<CodeGroup>
  ```bash Pip theme={null}
  pip install resend
  ```
</CodeGroup>

## 2. Send email using HTML

The easiest way to send an email is by using the `html` parameter.

```py index.py theme={null}
import os
import resend

resend.api_key = os.environ["RESEND_API_KEY"]

params: resend.Emails.SendParams = {
    "from": "Acme <onboarding@resend.dev>",
    "to": ["delivered@resend.dev"],
    "subject": "hello world",
    "html": "<strong>it works!</strong>",
}

email = resend.Emails.send(params)
print(email)
```

## 3. Try it yourself

<Card title="Python Example" icon="arrow-up-right-from-square" href="https://github.com/resend/resend-python-example">
  See the full source code.
</Card>
