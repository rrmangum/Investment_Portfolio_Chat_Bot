### Required Libraries ###
from datetime import datetime
from dateutil.relativedelta import relativedelta

### Functionality Helper Functions ###
def parse_int(n):
    """
    Securely converts a non-integer value to integer.
    """
    try:
        return int(n)
    except ValueError:
        return float("nan")

def parse_float(n):
    """
    Securely converts a non-float value to float.
    """
    try:
        return float(n)
    except ValueError:
        return float("nan")

def build_validation_result(is_valid, violated_slot, message_content):
    """
    Define a result message structured as Lex response.
    """
    if message_content is None:
        return {"isValid": is_valid, "violatedSlot": violated_slot}

    return {

        "isValid": is_valid,
        "violatedSlot": violated_slot,
        "message": {"contentType": "PlainText", "content": message_content},
    }


### Dialog Actions Helper Functions ###
def get_slots(intent_request):
    """
    Fetch all the slots and their values from the current intent.
    """
    return intent_request["currentIntent"]["slots"]


def elicit_slot(session_attributes, intent_name, slots, slot_to_elicit, message):
    """
    Defines an elicit slot type response.
    """

    return {
        "sessionAttributes": session_attributes,
        "dialogAction": {
            "type": "ElicitSlot",
            "intentName": intent_name,
            "slots": slots,
            "slotToElicit": slot_to_elicit,
            "message": message,
        },
    }


def delegate(session_attributes, slots):
    """
    Defines a delegate slot type response.
    """

    return {
        "sessionAttributes": session_attributes,
        "dialogAction": {"type": "Delegate", "slots": slots},
    }


def close(session_attributes, fulfillment_state, message):
    """
    Defines a close slot type response.
    """

    response = {
        "sessionAttributes": session_attributes,
        "dialogAction": {
            "type": "Close",
            "fulfillmentState": fulfillment_state,
            "message": message,
        },
    }

    return response


"""
Step 3: Enhance the Robo Advisor with an Amazon Lambda Function

In this section, you will create an Amazon Lambda function that will validate the data provided by the user on the Robo Advisor.

1. Start by creating a new Lambda function from scratch and name it `recommendPortfolio`. Select Python 3.7 as runtime.

2. In the Lambda function code editor, continue by deleting the AWS generated default lines of code, then paste in the starter code provided in `lambda_function.py`.

3. Complete the `recommend_portfolio()` function by adding these validation rules:

    * The `age` should be greater than zero and less than 65.
    * The `investment_amount` should be equal to or greater than 5000.

4. Once the intent is fulfilled, the bot should respond with an investment recommendation based on the selected risk level as follows:

    * **none:** "100% bonds (AGG), 0% equities (SPY)"
    * **low:** "60% bonds (AGG), 40% equities (SPY)"
    * **medium:** "40% bonds (AGG), 60% equities (SPY)"
    * **high:** "20% bonds (AGG), 80% equities (SPY)"

> **Hint:** Be creative while coding your solution, you can have all the code on the `recommend_portfolio()` function, or you can split the functionality across different functions, put your Python coding skills in action!

5. Once you finish coding your Lambda function, test it using the sample test events provided for this Challenge.

6. After successfully testing your code, open the Amazon Lex Console and navigate to the `recommendPortfolio` bot configuration, integrate your new Lambda function by selecting it in the “Lambda initialization and validation” and “Fulfillment” sections.

7. Build your bot, and test it with valid and invalid data for the slots.

"""


def validate_data(age, investmentAmount, riskLevel, intent_request):
    """
    Validates the data provided by the user.
    """

    # Validate the user is of the correct age
    if age is not None:
        age = parse_int(age)
        if age <= 0:
            return build_validation_result(
                False,
                'age',
                'You must be atleast one year of age, to start saving for retirement!'
            )
            
        elif age > 64:
            return build_validation_result(
                False,
                'age',
                'You are already retired!'
            )
   
    # Validate the user is investing the minimum amount
    if investmentAmount is not None:
        investmentAmount = parse_int(investmentAmount)
        if investmentAmount < 5000:
            return build_validation_result(
                False,
                'investment_amount',
                'Sorry, you must invest $5,000 or more.'
            )

    # Validate the user has entered a correct risk level        
    if riskLevel not in ['None', 'Low', 'Medium', 'High']:
        return build_validation_result(
            False,
            'riskLevel',
            "Sorry you must select one of the following options: 'None', 'Low', 'Medium', or 'High'"
        )
            
    # a True is returned if age and investmentAmount are valid
    return build_validation_result(True, None, None)


### Intents Handlers ###
def recommend_portfolio(intent_request):
    """
    Performs dialog management and fulfillment for recommending a portfolio.
    """

    first_name = get_slots(intent_request)["firstName"]
    age = get_slots(intent_request)["age"]
    investment_amount = get_slots(intent_request)["investmentAmount"]
    risk_level = get_slots(intent_request)["riskLevel"]
    
    source = intent_request["invocationSource"]

    if source == 'DialogCodeHook':
        # get all the slots
        slots= get_slots(intent_request)
        
        # validate user input
        validation_result = validate_data(age, investment_amount, risk_level, intent_request)
        
        # If the data provided by the user is not valid,
        # the elicitSlot dialog action is used to re-prompt for the first violation detected.
        if not validation_result["isValid"]:
            slots[validation_result["violatedSlot"]] = None  # Cleans invalid slot

            # Returns an elicitSlot dialog to request new data for the invalid slot
            return elicit_slot(
                intent_request["sessionAttributes"],
                intent_request["currentIntent"]["name"],
                slots,
                validation_result["violatedSlot"],
                validation_result["message"],
            )

        # Fetch current session attributes
        output_session_attributes = intent_request["sessionAttributes"]

        # Once all slots are valid, a delegate dialog is returned to Lex to choose the next course of action.
        return delegate(output_session_attributes, get_slots(intent_request))
        
    # reccomend portfolio based on user risk level
    if risk_level == 'None':
        # Calculate the recommended portfolio multiplier
        bond_pct = 1.0
        stock_pct = 0.0
        portfolio_bonds = parse_float(investment_amount) * bond_pct
        portfolio_stocks = parse_float(investment_amount) * stock_pct
        
    elif risk_level == 'Low':
        # Calculate the recommended portfolio multiplier
        bond_pct = 0.6
        stock_pct = 0.4
        portfolio_bonds = parse_float(investment_amount) * bond_pct
        portfolio_stocks = parse_float(investment_amount) * stock_pct
 
    elif risk_level == 'Medium':
        # Calculate the recommended portfolio multiplier
        bond_pct = 0.4
        stock_pct = 0.6
        portfolio_bonds = parse_float(investment_amount) * bond_pct
        portfolio_stocks = parse_float(investment_amount) * stock_pct
        
    elif risk_level == 'High':
         # Calculate the recommended portfolio multiplier
        bond_pct = 0.2
        stock_pct = 0.8
        portfolio_bonds = parse_float(investment_amount) * bond_pct
        portfolio_stocks = parse_float(investment_amount) * stock_pct

    return close(
        intent_request["sessionAttributes"],
        "Fulfilled",
        {
            "contentType": "PlainText",
            "content": """Thank you for your information,
            based on your {} risk level,
            you should invest ${} in bonds and ${} in stocks.
            Bonds will make up {}% of your portfolio and 
            Stocks will make up {}% of your portfolio
            """.format(
                risk_level, portfolio_bonds, portfolio_stocks, (bond_pct * 100), (stock_pct * 100)
            )
        }
    )

### Intents Dispatcher ###
def dispatch(intent_request):
    """
    Called when the user specifies an intent for this bot.
    """

    intent_name = intent_request["currentIntent"]["name"]

    # Dispatch to bot's intent handlers
    if intent_name == "recommendPortfolio":
        return recommend_portfolio(intent_request)

    raise Exception("Intent with name " + intent_name + " not supported")


### Main Handler ###
def lambda_handler(event, context):
    """
    Route the incoming request based on intent.
    The JSON body of the request is provided in the event slot.
    """

    return dispatch(event)
