
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

| Command Option | Type | Description | Required |
|--|--|--|--|
| --writeKey | String | Segment Write Key | Yes |
| --apiHost | String | Custom Host | No |
| --payload | JSON | Event Payload | Yes |

### Example: Passing Multiple Events as JSON Array

```bash
$ e2e-test:run --writeKey='YOUR_WRITE_KEY' --apiHost='' --payload='"[{\"anonymousId\":\"507f191e810c89729de960ea\",\"channel\":\"browser\",\"context\":{\"app\":\"ecommerce\"},\"integrations\":{\"All\":false,\"Mixpanel\":true,\"Salesforce\":true},\"messageId\":\"022ty90c-bbac-11e4-8dfc-aa07a5b093q8\",\"traits\":{\"name\":\"Clark Kent\",\"email\":\"clark@example.com\",\"plan\":\"premium\",\"logins\":5,\"address\":{\"street\":\"6th St\",\"city\":\"San Francisco\",\"state\":\"CA\",\"postalCode\":\"94103\",\"country\":\"USA\"}},\"type\":\"identify\",\"userId\":\"AiUGstSDIg\",\"version\":\"2.0\"},{\"messageId\":\"122bb9ui-bbac-11e4-8dfc-aa07z5b098ip\",\"userId\":\"AiUGstSDIg\",\"type\":\"track\",\"event\":\"Course Clicked\",\"context\":{\"page\":{\"path\":\"/academy/\",\"referrer\":\"\",\"search\":\"\",\"title\":\"Analytics Academy\",\"url\":\"https://segment.com/academy/\"}},\"integrations\":{},\"properties\":{\"title\":\"Intro to Analytics\"}}]"'
```

### Example: Passing Individual Events

#### 1. Identify
 
 ``` bash
$ e2e-test:run --writeKey='YOUR_WRITE_KEY' --payload='"{\"anonymousId\":\"507f191e810c89729de960ea\",\"channel\":\"browser\",\"context\":{\"app\":\"ecommerce\"},\"integrations\":{\"All\":false,\"Mixpanel\":true,\"Salesforce\":true},\"messageId\":\"022bb90c-bbac-11e4-8dfc-aa07a5b093q8\",\"traits\":{\"name\":\"Clark Kent\",\"email\":\"clark@example.com\",\"plan\":\"premium\",\"logins\":5,\"address\":{\"street\":\"6th St\",\"city\":\"San Francisco\",\"state\":\"CA\",\"postalCode\":\"94103\",\"country\":\"USA\"}},\"type\":\"identify\",\"userId\":\"97980cfea0062\",\"version\":\"2.0\"}"'
```

#### 2. Track

``` bash
$ e2e-test:run --writeKey='YOUR_WRITE_KEY' --payload='"{\"messageId\":\"122bb90c-bbac-11e4-8dfc-aa07z5b098ip\",\"userId\":\"AiUGstSDIg\",\"type\":\"track\",\"event\":\"Course Clicked\",\"context\":{\"page\":{\"path\":\"/academy/\",\"referrer\":\"\",\"search\":\"\",\"title\":\"Analytics Academy\",\"url\":\"https://segment.com/academy/\"}},\"integrations\":{},\"properties\":{\"title\":\"Intro to Analytics\"}}"'
```

#### 3. Page

``` bash
$ e2e-test:run --writeKey='YOUR_WRITE_KEY' --payload='"{\"anonymousId\":\"507f191e810c19729de860ea\",\"channel\":\"browser\",\"integrations\":{\"All\":true,\"Mixpanel\":false,\"Salesforce\":false},\"messageId\":\"022bb90c-bbac-11e8-8dfc-aa07a5b090ol\",\"name\":\"Home\",\"properties\":{\"title\":\"Welcome | Initech\",\"url\":\"http://www.example.com\"},\"type\":\"page\",\"userId\":\"97980cfea0067\"}"'
```

#### 4. Screen

``` bash
$ e2e-test:run --writeKey='YOUR_WRITE_KEY' --payload='"{\"anonymousId\":\"507f191e810c19729de860ea\",\"channel\":\"browser\",\"integrations\":{\"All\":true,\"Mixpanel\":false,\"Salesforce\":false},\"messageId\":\"022bb90c-bbac-11e8-8dfc-aa07a5b090ol\",\"name\":\"Registration\",\"properties\":{\"title\":\"Welcome | Initech\",\"url\":\"http://www.example.com\"},\"type\":\"Screen\",\"userId\":\"97980cfea0067\"}"'
```

#### 5. Alias

``` bash
$ e2e-test:run --writeKey='YOUR_WRITE_KEY' --payload='"{\"anonymousId\":\"507f191e810c19729de800ea\",\"channel\":\"browser\",\"integrations\":{\"All\":true,\"Mixpanel\":false,\"Salesforce\":false},\"messageId\":\"022bb90c-bbac-11e4-8dfc-aa07u5b093lk\",\"previousId\":\"12345-239239-239239-23923\",\"type\":\"alias\",\"userId\":\"507f191e81\",\"version\":\"1.9\"}"'
```

#### 6. Group

``` bash
% e2e-test:run --writeKey='YOUR_WRITE_KEY' --payload='"{\"anonymousId\":\"507f191e810c19729de800ea\",\"channel\":\"browser\",\"integrations\":{\"All\":true,\"Mixpanel\":false,\"Salesforce\":false},\"messageId\":\"022bb90c-bbac-11e4-8dfc-aa07u5b093lk\",\"previousId\":\"12345-239239-239239-23923\",\"type\":\"alias\",\"userId\":\"507f191e81\",\"version\":\"1.9\"}"'
```

## Configuration Options

A few configuration options are available in the ```.env``` file.