## webgpio (GPIO web control)
Run development server:
```
git clone https://github.com/dmitriyminer/webgpio.git
cd webgpio
vagga run
```

Run client:
   - copy client.py to your Raspberry
   - configure client.py (REMOTE_SERVER, REMOTE_PORT, EMAIL, PASSWD, DEVICE_KEY)

```
pip install aiohttp RPi.GPIO
python3.6 client.py
```
