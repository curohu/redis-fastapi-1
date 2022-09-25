#! /user/bin/python3
# This is an API template built on FastAPI that can be easily modified

# standard lib imports
import sys,os,time,json,hashlib,multiprocessing,asyncio

# imports requiring pip
from fastapi import FastAPI, Response, Request, status
import redis



# import from local path
sys.path.append(os.path.dirname(os.path.realpath(__file__))+'/../')
import remotelogger.event as rEvent
import remotelogger.remotelogger as rLogger


# get key for MD5 hash
# I have provided a random 64-bit key as an example. You should change it
keyFile = os.path.dirname(os.path.realpath(__file__))+'/../secret_key' 
KEY = ''
try:
    with open(keyFile, 'r') as file:
        KEY = file.readline()
        file.close()
except Exception as e:
    print('secret_key file not found')
    sys.exit()

# if the key is not found this will raise a "Missing secret_key" error
assert not KEY == '', "Missing secret_key" 

# this will error out if you do not change the secret_key
assert not KEY == 'g64iyGfvWE56wNC6kqgnUmTt5iFF4dodZKr8TZ17nnqwrUx78trNRhCKqpP5AAq6', "Change the secret_key" 

# initialize fast API app
app = FastAPI() 

DRIVING_PROCESS_TREE = "API_TEMPLATE" # This is used for syslog reporting in splunk. Once reports are generated you can search for this application with: index=* driving_process_tree={DRIVING_PROCESS_TREE}
ENDPOINT_BASE = '/redis_example/v1/' # This is the base for the proceeding API endpoints

# same as before, but now there are two parrameters to be passed.
# example url: http://127.0.0.1:8080/api_template/v1/example1?add1=123&add2=456
@app.post(ENDPOINT_BASE+'redisW')
async def redisWrite(request: Request) -> Response:
    endpoint = ENDPOINT_BASE+'redis'
    clientIp = request.client.host
    # eventString = ',processingTime={:.3f},endpoint={},clientIp={},dataSent={},statusCode={}'
    stime = time.time()
    try: 
        if not await _checkKey(request.headers.get('X-API-KEY')):
            # _generateLog(eventString.format(time.time()-stime,endpoint,clientIp,'401'))
            return Response(status_code=status.HTTP_401_UNAUTHORIZED)
        bodyJson = await _parseBody(request)
        return Response(content=await redisWrite_task(bodyJson),media_type='application/json',status_code=status.HTTP_200_OK)
    except Exception as e:
        raise e
        # eventString+="exceptionCode={},".format(str(e))
        # _generateLog(eventString.format(time.time()-stime,endpoint,clientIp,'500'))
        return Response(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)


async def redisWrite_task(bodyJson: json) -> json:
    # r = _createRedisInterface
    # for key,value in bodyJson['set'].items():
    #     r.set(key,value)
    # return json.dumps({'set': bodyJson['set']})
    time.sleep(1)
    print(bodyJson)
    return '1'


@app.get(ENDPOINT_BASE+'redisR')
async def redisRead(request: Request) -> Response:
    endpoint = ENDPOINT_BASE+'redis'
    clientIp = request.client.host
    # eventString = ',processingTime={:.3f},endpoint={},clientIp={},dataSent={},statusCode={}'
    stime = time.time()
    try: 
        if not await _checkKey(request.headers.get('X-API-KEY')):
            # _generateLog(eventString.format(time.time()-stime,endpoint,clientIp,'401'))
            return Response(status_code=status.HTTP_401_UNAUTHORIZED)
        return Response(content=await redisRead_task(await _parseBody(request)),media_type='application/json',status_code=status.HTTP_200_OK)
    except Exception as e:
        raise e
        # eventString+="exceptionCode={},".format(str(e))
        # _generateLog(eventString.format(time.time()-stime,endpoint,clientIp,'500'))
        return Response(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)


async def redisRead_task(bodyJson: json) -> json:
    r = _createRedisInterface
    readData = {}
    for arg in bodyJson['read']:
        redisData = r.get(str(arg))
        if redisData:
            readData[str(arg)] = str(redisData.decode('utf-8'))
    return json.dumps({'read': readData})


@app.delete(ENDPOINT_BASE+'redisD')
async def redisDelete(request: Request) -> Response:
    endpoint = ENDPOINT_BASE+'redis'
    clientIp = request.client.host
    # eventString = ',processingTime={:.3f},endpoint={},clientIp={},dataSent={},statusCode={}'
    stime = time.time()
    try: 
        if not await _checkKey(request.headers.get('X-API-KEY')):
            # _generateLog(eventString.format(time.time()-stime,endpoint,clientIp,'401'))
            return Response(status_code=status.HTTP_401_UNAUTHORIZED)
        return Response(content=await redisDelete_task(await _parseBody(request)),media_type='application/json',status_code=status.HTTP_200_OK)
    except Exception as e:
        # eventString+="exceptionCode={},".format(str(e))
        # _generateLog(eventString.format(time.time()-stime,endpoint,clientIp,'500'))
        raise e
        return Response(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)


async def redisDelete_task(bodyJson: json) -> json:
    r = _createRedisInterface
    for arg in bodyJson['delete']:
        if r.get(str(arg)):
            r.unlink(arg)
    return json.dumps({'delete': bodyJson['delete']})





###################################################################################
# Utility Functions
###################################################################################

# this is a security function to authenticate the client. It is really basic in that it rounds unix time to the 100s place and uses that to salt the md5 hash of our secret_key.
# It is not perfect as there is a small chance that when the user sends the request and when the server recieves it you will increment the 100s place. However, you could catch this error in the client and just resend it.
# most APIs use https to get around sending the key in plain text, but I don't want to set that up
async def _checkKey(apiKey:str) -> bool:
    requestTime = str(round(time.time(),-2))
    md5Hash = hashlib.md5(str(KEY+requestTime).encode()).hexdigest()
    return md5Hash == apiKey

# This function creates the Event object and then passes it to the remote logger inorder to be sent over to our syslog server
# I want this to run in both async and parallel so it also kicks off a new process to do this
def _generateLog(eventText: str, drivingProcessTree: str = DRIVING_PROCESS_TREE) -> None:
    evnt = rEvent.Event(event_text=eventText,driving_process_tree=drivingProcessTree)
    logProc = multiprocessing.Process(target=_generateLogSubprocess,args=(evnt,))
    logProc.start()

def _generateLogSubprocess(evnt: rEvent.Event) -> None:
    rLogger.sendLog(evnt)


def _createRedisInterface() -> redis.Redis:
    return redis.Redis(
        host='127.0.0.1',
        port=6379
        )

async def _parseBody(request: Request) -> json:
    bJson = await request.body()    
    return bJson