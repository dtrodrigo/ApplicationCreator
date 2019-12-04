import pandas as pd
import requests, ssl, os, sys, json, copy, logging, time
from datetime import datetime



#
# BEFORE EXECUTING THE SCRIPT VERIFY:
# - The ENV variable , where are you sending the information
# - APPLICATION_RULES_EXCEL : app-test.xlsx where you are extracting the information
# 	The format of the excel file has to be:
# 	- First row: AppName	| Rule. 
# 	- Second row contain the first rule to execute : MyNewApplicaiton | mydomain.com/mywebapp
# 	- All the rules for an application should be grouped together in the excel file. If the file contains the applicaiton name+ rule not grouped, it will create multiple applicaitons with the same name 
#
# - APPLICATION_TEMPLATE : select the template to define the application with or without RUM
# - APPLICATION_RULE_TEMPLATE to apply: Begings With or Contains
#   If using Begings with, add the string "https://" to the rule
#

ENV =  '<Dynatrace_URL>'  # For example: 'https://mypilotenvironment.live.dynatrace.com' 
TOKEN = '<API-Token>' # For example: 'asdASd8123asd'
HEADERS = {'Authorization': 'Api-Token ' + TOKEN}
HEADERS_POST = {'Authorization': 'Api-Token ' + TOKEN, 'Content-Type' : 'application/json'}
APPLICATION_TEMPLATE = 'applicationTemplate.json'
APPLICATION_RULE_TEMPLATE = 'applicationRuleTemplateCONTAINS.json'
APPLICATION_RULES_EXCEL = "apps-test.xlsx"
PATH = os.getcwd()
logging.basicConfig(filename=datetime.now().strftime('appCreatorLog_%H_%M_%d_%m_%Y.log'), filemode='w', format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# readAppRules: Access to the excelfile indicated (app-test.xlsx), and returns an array with all the pairs Appname|AppRule. Edit the file to add your new application rules or use another file.
# The format of the excel file has to be:
# - First row: AppName	| Rule. 
# - Second row contain the first rule to execute : MyNewApplicaiton | mydomain.com/mywebapp
# - All the rules for an application should be grouped together in the excel file. If the file contains the applicaiton name+ rule not grouped, it will create multiple applicaitons with the same name 
# Return: apprules will have the following format: {'App1': {'rules': ['myrule']}, 'App2': {'rules': ['myrule2', 'myrule3']}}
def readAppRules():
	df = pd.read_excel(APPLICATION_RULES_EXCEL)

	appRules = {}
	lastStoredApp = "";

	for index, row in df.iterrows():
	     logger.debug(row['AppName'], row['Rule'])
	     app = row['AppName']
	     if app in appRules :
	     	# App Already exist, just append the new rule
	     	appRules[app].append(row['Rule'])
	     else :
	     	# New Application and new rule
	     	appRules[app] = [row['Rule']]
	return appRules


# PostNewApplication: Create a new appication with the corresponding Application rules
#
def createNewApplicationAndRules(applicationName, applicationRules):
	application = createApplication(applicationName)
	if application:
				logger.debug(application)
				print("New Application: "+ application['name']+ " ID: "+ str(application['id']))
				logger.info("New Application: "+ application['name']+ " ID: "+ str(application['id']))
				createApplicationRules(applicationRules, application)
	else:
		logger.error("Failure creating a new Application")
		logger.error(application)


# Create body payload and post new Application 
#
def createApplication(applicationName):
	# Create a new applicaiton based on applicaitonJson
	newApplicationJson = createNewApplicationBody(applicationName)
	# Validate if the Json to send.
	if validateNewApplication(newApplicationJson):
			# Post/Create a new application. 
			# It does not verify if app exists, so if an application exist with the same name, it will create a new one with the appending (1) at the end of the AppName // "My App (1)"
			return postNewApplication(newApplicationJson)
	else :
			return None 

# Create body payload and post new Application Rule 
#
def createApplicationRules(applicationRules, application):
	# For each Application Rule obtained from the excel file
	for rule in applicationRules:
		# Build the Json that contains the new Application Rule
		newApplicationRuleJson = createNewApplicationRuleBody(rule, application['id'])
		# Validate the Json format of the new Application Rule
		if validateNewApplicationRule(newApplicationRuleJson):
				# Post/Create a new application
				apprule = postNewApplicationRule(newApplicationRuleJson)
				print("New Application Rule: "+ apprule['name']+ " ID: "+ apprule['id'])
				logger.info("New Application Rule: "+ apprule['name']+ " ID: "+ apprule['id'])
		else:
			logger.error("Failure creating a new AppRule")
			logger.error(newApplicationRuleJson)

#  Validate the format of the json, before creating an Application.
#  Use the Dynatrace API endpoint /validate to confirm that this will be accepted
#
def validateNewApplication(newApplicationJson):
	 response = postNewEntity('/api/config/v1/applications/web/validator',newApplicationJson)
	 print(response.text)
	 return response.status_code == 204

#  Validate the format of the json, before creating an Application Rule
#  Use the Dynatrace API endpoint /validate to confirm that this will be accepted
#
def validateNewApplicationRule(newApplicationRuleJson):
	 response = postNewEntity('/api/config/v1/applicationDetectionRules/validator',newApplicationRuleJson)
	 return response.status_code == 204

# Build Body payload of an Applicaiton to send on API call.
# Based on the applicationTemplate.json, it changes that template to use the AppName extracted from the excel file 
#
def createNewApplicationBody(applicationName):
	newApplicationBodyJson = readApplicationTemplate()
	newApplicationBodyJson['name'] = applicationName
	return newApplicationBodyJson

# Build Body payload of a new Applicaiton Rule to send on API call.
# Based on the applicationRuleTemplateCONTAINS.json, it changes that template to use the right ApplicationIdentifier and the URL pattern extracted from the excel file 
#
def createNewApplicationRuleBody(rule, applicationID):
	newApplicationRuleBodyJson = readApplicationRuleTemplate()
	newApplicationRuleBodyJson['applicationIdentifier'] = applicationID
	newApplicationRuleBodyJson['filterConfig']['pattern'] = rule 
	# Add framework config  or other options
	return newApplicationRuleBodyJson

# Read Json file, to be used as template when creating new application Json payload body
# The current template has enabled RUM monitoring, if no RUM or other configuration want to be used, modify the applicationTemplate.json
# for example: applicaitonTemplate-NO-RUM.json, can be used as template to create applications with RUM dissabled
#
def readApplicationTemplate():
	return readTemplate(APPLICATION_TEMPLATE)

#
# Read Json file, to be used as template when creating new application rule Json payload body
# The current template has use "contains" rule, if another rule "starts with", "ends with"... wants to be used, you can modify the applicationRuleTemplateCONTAINS.json
# for example: applicationRuleTemplate-BEGINS_WITH.json, can be used as template to create applications with RUM dissabled
#
def readApplicationRuleTemplate():
	return readTemplate(APPLICATION_RULE_TEMPLATE)

# ReadTemplate: read information from the file template.json, in the same locations as the dahsboard.py script
#				Rerunts the data in json format
def readTemplate(template):
	with open(template, encoding="utf8") as json_file:  
		data = json.load(json_file)
	return data

# Post new Applicaiton entity
#
def postNewApplication(newApplicationJson):
		return postNewEntity('/api/config/v1/applications/web',newApplicationJson)

# Post new Applicaiton rule entity
#
def postNewApplicationRule(newApplicationRuleJson):
		return postNewEntity('/api/config/v1/applicationDetectionRules',newApplicationRuleJson)

# Builds the URLs and  query needed to post/create a new entity
#
def postNewEntity(endpointURL,dataJson):
	j = json.JSONEncoder().encode(dataJson)
	try:
		r = requests.post(ENV + endpointURL, headers=HEADERS_POST, data=j)
		print(r.status_code)
		# If 201, successful. The entity has been created
		if r.status_code == 201:
				return r.json()
		# 400, failure on the creation of the entity
		elif r.status_code == 400:
			print("Failure creating :")
			logger.error("Failure creating :")
			logger.error(dataJson)
			logger.error(r.json())
			print(dataJson)
			print(r.json())
		# 429, Too many request, we have slow donw how many calls per second we are sending (wait 5s and resend)
		elif r.status_code == 429:
			print("Error too many calls, sleep 5s")
			# Wait for 5 seconds
			time.sleep(5)
			return postNewEntity(endpointURL,dataJson)
		return r
	except ssl.SSLError:
		print("SSL Error")

# formatEnvironmentURL: Verify if the Dynatrace environment URL has the proper format, starting with https:// and not ending with /
#
def formatEnvironmentURL(environmentURL):
	if environmentURL.endswith("/") or not environmentURL.startswith("https://"):
		errorMsg = "ERROR: Wrong Environment URL format, plase change teh ENV variable to follow the format : start with https://<your-Dynatrace-environment> , wihtout / at the end"
		errorExampleMSG = "Example: 'https://mypilotenvironment.live.dynatrace.com' or https://myenvironment.live.dynatrace.com or https://myenvironment.dynatrace-managed.com/e/123-123123-123-123-123"
		logger.error(errorMsg)
		print(errorMsg)
		logger.error(errorExampleMSG)
		print(errorExampleMSG)
		return False
	else:
		return True

# preConditionsEvaluation: Verify preconditions like formatEnvironmentURL
#
def preConditionsEvaluation():
	return formatEnvironmentURL(ENV)

def main():
	if preConditionsEvaluation():
		applicationList = readAppRules()
		print("Edit the tenant: "+ ENV)
		for applicationName in applicationList:
			createNewApplicationAndRules(applicationName, applicationList[applicationName])

if __name__ == '__main__':
	main()