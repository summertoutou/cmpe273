from __future__ import print_function
from collections import OrderedDict
import boto3
import json
import time
from datetime import datetime, timedelta

print('Loading function')

def return_method(response_s):
    resp_code = response_s.get('ResponseMetadata').get('HTTPStatusCode')
    if resp_code == 200:
        return "200 OK"
    else:
        msg = str(resp_code) + "Something wrong with your request"
        return msg
    
def update_data(table,payload_s,input_s,id):
    response = table.update_item(
        Key={
             "menu_id":id
        },
        UpdateExpression="SET"+" "+input_s+"=:a",  
        ExpressionAttributeValues={
            ":a": payload_s[input_s]
        },
        ReturnValues="UPDATED_NEW"
    )
    #print ("Update successful!",response)
    return response

def update_order(table,orderID,key,value):
    response = table.update_item(
        Key={
             "order_id":orderID
        },
        UpdateExpression="SET"+" "+key+"=:a",  
        ExpressionAttributeValues={
            ":a": value
        },
        ReturnValues="UPDATED_NEW"
    )
    #print ("Update successful!",response)
    return response.get('ResponseMetadata')

def handler(event, context):
    '''Provide an event that contains the following keys:

      - operation: one of the operations in the operations dict below
      - tableName: required for operations that interact with DynamoDB
      - payload: a parameter to pass to the operation being performed
    '''
    #print("Received event: " + json.dumps(event, indent=2))

    operation = event['operation']

    if 'TableName' in event:
        dynamo = boto3.resource('dynamodb').Table(event['TableName'])
        dynamo_menu = boto3.resource('dynamodb').Table('Menu')

    operations = {
        'create': lambda x: dynamo.put_item(**x),
        'read': lambda x: dynamo.get_item(**x).get('Item'),
        'delete': lambda x: dynamo.delete_item(**x),
        'list': lambda x: dynamo.scan(**x),
        'echo': lambda x: x,
        'ping': lambda x: 'pong'
    }

    if operation in operations:
        response = operations[operation](event.get('payload'))

    if operation == 'delete':
        return return_method(response)
    elif operation == 'read':
        return response
    elif operation == 'create':
        if event['TableName']=="Menu":
            return return_method(response)
        else:
            order_id_m = event.get('payload').get('Item').get('order_id')
           #update order status to incomplete
            name = event.get('payload').get('Item').get('customer_name')
            response_temp = operations[operation](event.get('payload'))
            menu_id_o = event.get('payload').get('Item').get('menu_id')
            menu_m = dynamo_menu.get_item(TableName="Menu",Key={"menu_id": menu_id_o})
            menu_selection = menu_m.get('Item').get('selection')
            count = 1
            array_s = ""
            for s in menu_selection:
                array_s = array_s + str(count) + "."+ s + " "
                count += 1
            if response_temp.get('ResponseMetadata').get('HTTPStatusCode')==200:
                value = "incomplete"
                update_order(dynamo,order_id_m,"order_status",value)
                message = '{"Message": "Hi %s, please choose one of these selection: %s"}' % (name,array_s)
                msg = json.loads(message, object_pairs_hook=OrderedDict)
                return msg
                
    elif operation == 'update':
        payload = event['payload'] 
        if event['TableName']=="Menu":
            dict_keys = payload.keys()
            for key in dict_keys:
                if key != 'menu_id':
                    response2 = update_data(dynamo,payload,key,payload['menu_id'])
                else:
                    continue
            return return_method(response2)
        else:
            order_id_n = event.get('order_id')
            number = int(payload.get('input'))
            #check if the selection is made
            order_item= dynamo.get_item(TableName="Order",Key={"order_id": order_id_n}).get('Item')
            
            order_list = len(order_item)
            menu_id = order_item.get('menu_id')
            menu_m = dynamo_menu.get_item(TableName="Menu",Key={"menu_id": menu_id})
            menu_selection = menu_m.get('Item').get('selection')
            menu_size = menu_m.get('Item').get('size')
            menu_price = menu_m.get('Item').get('price')
            if order_list == 5:
                # make selection
                selected = menu_selection[number-1]
                selected_s = '{"selection": "%s"}' % (selected)
               
                response3 = update_order(dynamo,order_id_n,"order_details",json.loads(selected_s)).get('HTTPStatusCode')
                count = 1
                array_s = ""
                for s in menu_size:
                    array_s = array_s + str(count) + "."+ s + " "
                    count += 1
                if response3 == 200:
                    message = '{"Message": "Which size do you want? %s"}' % (array_s)
                    msg = json.loads(message, object_pairs_hook=OrderedDict)
                else:
                    msg = json.loads('{"Message": "Something wrong with your input"}', object_pairs_hook=OrderedDict)
                return msg
            elif order_list == 6:
                # choose size
                order_selection = order_item.get('order_details').get('selection')
                size_selected = menu_size[number-1]
                if number<=len(menu_price):
                    cost = menu_price[number-1]
                else:
                    cost = menu_price[len(menu_price)-1]
                format = "%m-%d-%Y %H:%M:%S"
                current_time_in_utc = datetime.utcnow()
                time_s = (current_time_in_utc + timedelta(hours=-7)).strftime(format)
                order_s2 = '{"selection": "%s", "size": "%s", "costs": "%s", "order_time": "%s"}' % (order_selection,size_selected,cost,time_s)
                
                response4 = update_order(dynamo,order_id_n,"order_details",json.loads(order_s2, object_pairs_hook=OrderedDict))
                
                if response4.get('HTTPStatusCode') == 200:
                    update_order(dynamo,order_id_n,"order_status","processing")
                    message = '{"Message": "Your order costs $%s. We will email you when the order is ready. Thank you!"}' % (cost)
                    msg = json.loads(message, object_pairs_hook=OrderedDict)
                else:
                    msg = json.loads('{"Message": "Something wrong with your input"}', object_pairs_hook=OrderedDict)
                return msg 
                
    else:
        raise ValueError('Unrecognized operation "{}"'.format(operation))