# Dynatrace - ApplicationCreation 
This script will create a new Application and Application rules based on the Applicaiton rules defined on on a excel file

![Dashboard example](img/Dashboard.PNG?raw=true "Dashboard example")


## Getting Started

These instructions will get you a copy of the project up and running on your local machine for development and testing purposes. See deployment for notes on how to deploy the project on a live system.

### Prerequisites

This is a python script, so you will need [python installed](https://www.python.org/downloads/) to execute the script

URL from your Dynatrace environment

Dynatrace API Token

Application definition rules - provided in this repo [app-test.xlsx](app-test.xlsx) (the excel file will contain the AppName followe for the URL rule definition to apply) 
The applicaiton rules have to be defined in order (All definitions from an application together in teh excel file)

Appllicaiton definition template - Select the proper template to create an application with or without RUM enabled. Templates provided in this repo:
[applicationTemplate.json](applicationTemplate.json)
[applicationTemplate-NO-RUM.json](applicationTemplate-NO-RUM.json)


Application Rule templates - Select the rules to apply to the application rules together with the URLs from teh excel file. Is needed to indicate is those rules will be URL contains, begins with... There are different json tempaltes for the different rules that can be applied
[applicationRuleTemplate-BEGINS_WITH.json](applicationRuleTemplate-BEGINS_WITH.json)
[applicationRuleTemplateCONTAINS.json](applicationRuleTemplateCONTAINS.json)


![Application Rules Options in the Dynatrace Web UI](img/ruleOptions.PNG?raw=true "Application Rules Options in the Dynatrace Web UI")

### Generate Dynatrace API token

The script use the Dynatrace Configuration API, so an API-Token will be needed. 
To create a new token, access to Dynatrace UI Settings > Integration > Dynatrace API > Generate token
The token will need the following rights:

```
Write configuration
```
![Generate token](img/Token.png?raw=true "Generate token")

## Edit script

Edit the appCreator.py file, include your Dynatrace cluster URL and API Token

```
ENV = 'https://YOUR-DYNATRACE-CLUSTER-URL'
TOKEN = 'YOUR-DYNATRACE-API-TOKEN'
```
Select the right templates to have RUM enabled or not
```
APPLICATION_TEMPLATE = 'applicationTemplate.json'
```

And to create the rules with the right condition
```
APPLICATION_RULE_TEMPLATE = 'applicationRuleTemplateCONTAINS.json'
```

## Running the tests

Execute the following command to run the script

```
py appCreator.py
```

The output will print the HTTP code of the validation(204) and creation (201), after creation the id of the new entity will be printed
```
Edit the tenant: https://YOUR-DYNATRACE-CLUSTER-URL
204
201
New Application: My Application Name ID: APPLICATION-CCEA52B08BF3D123
204
201
New Application Rule: My Application Name ID: c0601982-eb34-4eef-9e47-54076397123
```

### Logs

The script will create a log with every execution. It will be place in the same directory as the script, with appCreatorLog_HH_MM_DD_MM_YYYY.log format

Example:
```
appCreatorLog_12_46_10_10_2019.log

```

```
2019-10-10 12:46:56,518 - root - INFO - New Application: My Application Name ID: APPLICATION-CCEA52B08BF3D89A
2019-10-10 12:47:01,951 - root - INFO - New Application Rule: My Application Name ID: c0601982-eb34-4eef-9e47-540763972ac5
```

## Limitations

The maximum Application rules allowed in v176 is 1000 different Application definitions.
If the application is already defined with teh same name as provided in the excel, it will create another one with the saame name followed by (1), ie: "My repeated App (1)"
In teh excel, the application definitions have to be together, for example
App1 | URL1
App1 | URL2
App1 | URL3
App2 | URL1
App2 | URL2

This will create  two applications : App1[URL1,URL2, URL3] and App2[URL1, URL2]

If the excel has the rules not in order it will create multiple applications with same name:
App1 | URL1
App2 | URL1
App1 | URL2
App2 | URL2
App2 | URL3

This will create 4 applications : App1[URL1], App2[URL1], App1 (1)[URL2] and App2 (1)[URL2, URL3]
