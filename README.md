# Python Whatsapp Webscrapper
Webscrapper to extract Whatsapp messages from a user/group conversation.

<br>

## Requirements
- [Python 3](https://www.python.org/downloads/) (v3.8.6 used)
- Install required dependencies. Open a shell and run the following command:
  ```bash
  pip install -r requirements.txt
  ```
- Web browser, Firefox, Chrome or Brave.
- Web drivers:
	- **Firefox**: [https://github.com/mozilla/geckodriver/releases](https://github.com/mozilla/geckodriver/releases)
	- **Chrome**: [https://chromedriver.chromium.org/downloads](https://chromedriver.chromium.org/downloads)

<br>

## Usage
1. Download the webdrivers and place them in the folder ```drivers```.
	- Chrome driver must be named to: ```chromedriver.exe```
	- Firefox driver must be named to: ```geckodriver.exe```
2. Configure the browser paths in [settings.conf](./settings.conf) (only Firefox, Chrome or Brave compatible).<br>
   (path examples inside the file, modify with your own configuration)
   > **_browser_** : ```Browser name to use. Supported values: chrome/firefox. If you are using Brave, value is 'chrome'```<br>
   > **_binary_** : ```Path where the browser executable is located.```<br>
   > **_profile_path_** : ```Path where the browser user profile is located.``` <br>

3. Add the user(s) or group(s) in the [contacts.json](./contacts.json) file from which you want to extract messages.<br>
   ```last_message``` means from which message, all subsequent messages will be collected.<br>
   One of the limitations of the program is that the first time we have to introduce a very old message, for this we have to manually navigate through WhatsApp to extract it.
4. Running the program.<br>
   ```bash
   python main.py
   ```
	The first time the browser window will open. We log-in to WhatsApp (QR code) and once the session is opened, we close the browser.<br>
    Run the program again, a new window will be opened automatically, and it will start to search the contacts and extract the messages.

<br>

## Data Export
The program will automatically create a folder in the root of the project called ```data```, and within it all messages will be exported in ```csv``` format with the following columns:
- Date
- Hour
- User
- Message
- Emojis
- Quoted_Message

The file naming format is as follows: ```[contact_name/group] [date and hour].csv```, for example:
- ```John Smith 2021-04-03 21.25.38.csv```
- ```Family Group 2021-05-03 23.50.31.csv```

<br>

## Settings
### Firefox ```profile_path```
In Firefox, we can find our profile in:
- **Linux**: ```/home/user/.mozilla/firefox/xxxxxxxx.default```
- **Windows**: ```C:/Users/[user_name]/AppData/Roaming/Mozilla/Firefox/Profiles/xxxxxxxx.default```<br>

Once the path is located, we add it to our [settings.conf](./settings.conf) file in the section ```profile_path```.
<br><br>
### Chrome/Brave ```profile_path```
For Chrome or Brave, open the browser and type ```chrome://version/``` in the search bar. There you will find the path of the user profile.<br>
Copy the path and add it to [settings.conf](./settings.conf) in the section ```profile_path```.

<br>

## Program limitations
- If the program finds a message equal to ```last_message```, the program will take it as the last extraction point, regardless of whether that message was not our last starting point.

<br><br><br>
