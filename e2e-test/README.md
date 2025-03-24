
# Analytics Python CLI

This tool is created for the purpose of E2E Testing.

## Dependencies

| Module | Version |
|--|--|
| python | 3.9 |
| click | 8.1.8 |
| python-dotenv | 1.0.1 |
| python-dateutil | 2.8.2 |
| requests | 2.32.3 |
| PyJWT | 2.10.1 |
| backoff | 2.2.1 |

## Installation

 1. Change the working directory
     ```bash 
	 $ cd e2e-test 
	  ```
 2. Create a virtual environment inside the working directory
	  ```bash 
	  $ python3 -m venv .venv 
	  ```
 3. Enable the virtual environment
	```bash 
	$ source .venv/bin/activate 
	  ```
 4. Install dependencies
     ```bash 
	 $ pip install -r requirements.txt 
	  ```
  5. Install the script as a module
      ```bash 
	  $ pip install --editable . 
	  ```

## Usage Examples with Sample Payloads

### 1. Identify
 
 ``` bash
$ e2e-test:run --writeKey='YOUR_WRITE_KEY' --payload='"{\"anonymousId\":\"507f191e810c89729de960ea\",\"channel\":\"browser\",\"context\":{\"ip\":\"8.8.8.8\",\"userAgent\":\"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/40.0.2214.115 Safari/537.36\"},\"integrations\":{\"All\":false,\"Mixpanel\":true,\"Salesforce\":true},\"messageId\":\"022bb90c-bbac-11e4-8dfc-aa07a5b093q8\",\"traits\":{\"name\":\"Clark Kent\",\"email\":\"clark@example.com\",\"plan\":\"premium\",\"logins\":5,\"address\":{\"street\":\"6th St\",\"city\":\"San Francisco\",\"state\":\"CA\",\"postalCode\":\"94103\",\"country\":\"USA\"}},\"type\":\"identify\",\"userId\":\"97980cfea0062\",\"version\":\"2.0\"}"'
```

### 2. Track

``` bash
$ e2e-test:run --writeKey='YOUR_WRITE_KEY' --payload='"{\"messageId\":\"122bb90c-bbac-11e4-8dfc-aa07z5b098ip\",\"userId\":\"AiUGstSDIg\",\"type\":\"track\",\"event\":\"Course Clicked\",\"context\":{\"page\":{\"path\":\"/academy/\",\"referrer\":\"\",\"search\":\"\",\"title\":\"Analytics Academy\",\"url\":\"https://segment.com/academy/\"},\"userAgent\":\"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/46.0.2490.86 Safari/537.36\",\"ip\":\"108.0.78.21\"},\"integrations\":{},\"properties\":{\"title\":\"Intro to Analytics\"}}"'
```

### 3. Page

``` bash
$ e2e-test:run --writeKey='YOUR_WRITE_KEY' --payload='"{\"anonymousId\":\"507f191e810c19729de860ea\",\"channel\":\"browser\",\"context\":{\"ip\":\"8.8.8.8\",\"userAgent\":\"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/40.0.2214.115 Safari/537.36\"},\"integrations\":{\"All\":true,\"Mixpanel\":false,\"Salesforce\":false},\"messageId\":\"022bb90c-bbac-11e8-8dfc-aa07a5b090ol\",\"name\":\"Home\",\"properties\":{\"title\":\"Welcome | Initech\",\"url\":\"http://www.example.com\"},\"type\":\"page\",\"userId\":\"97980cfea0067\"}"'
```

### 4. Screen

``` bash
$ e2e-test:run --writeKey='YOUR_WRITE_KEY' --payload='"{\"anonymousId\":\"507f191e810c19729de860ea\",\"channel\":\"browser\",\"context\":{\"ip\":\"8.8.8.8\",\"userAgent\":\"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/40.0.2214.115 Safari/537.36\"},\"integrations\":{\"All\":true,\"Mixpanel\":false,\"Salesforce\":false},\"messageId\":\"022bb90c-bbac-11e4-8dfc-aa07a5b090op\",\"name\":\"Registration\",\"properties\":{\"title\":\"Welcome | Initech\",\"url\":\"http://www.example.com\"},\"type\":\"screen\",\"userId\":\"97980cfea0067\"}"'
```

### 5. Alias

``` bash
$ e2e-test:run --writeKey='YOUR_WRITE_KEY' --payload='"{\"anonymousId\":\"507f191e810c19729de800ea\",\"channel\":\"browser\",\"context\":{\"ip\":\"8.8.8.8\",\"userAgent\":\"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/40.0.2214.115 Safari/537.36\"},\"integrations\":{\"All\":true,\"Mixpanel\":false,\"Salesforce\":false},\"messageId\":\"022bb90c-bbac-11e4-8dfc-aa07u5b093lk\",\"previousId\":\"12345-239239-239239-23923\",\"type\":\"alias\",\"userId\":\"507f191e81\",\"version\":\"1.9\"}"'
```

### 6. Group

``` bash
% e2e-test:run --writeKey='YOUR_WRITE_KEY' --payload='"{\"type\":\"group\",\"groupId\":\"0e8c78ea9d97a7b8185e8632\",\"userId\":\"EMP12345\",\"traits\":{\"name\":\"Initech\",\"industry\":\"Technology\",\"employees\":329,\"plan\":\"enterprise\",\"total billed\":830}}"'
```

## Error Logs

 1. Errors logs are written under ```logs```directory.
 2. Each day, a new log directory is created under ```logs``` in ```YearMonthDay``` format.
 3. Log files are named as ```e2e-test_<hour-of-the-day>.log```
 4. Log file is rotated is maximum allowed file size is reached.

## Configuration Options

A few configuration options are available in the ```.env``` file.