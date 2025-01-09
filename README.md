# emailRelay

A small software to forward new versions of the thesis to professor and friends.

## Flow
1. Receives a webhook notifying a push or a release from my master-thesis repo
2. Downloads the thesis from Github servers and sends them to my Telegram friends
3. If I manually trigger a release, the thesis will be sent to my professor with email.